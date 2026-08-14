# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Shared knowledge-graph build machinery for Lab 1.

`prepare_graph.py` and the notebook both call `run_build` here, so the pinned
schema, the canary check, the scoped wipe, and the verification queries have one
definition and the script path and the notebook path cannot drift apart the way
they previously did (one verified on `h.id`, the other on `h.name`, and neither
matched the notebook).

Build order matters and is deliberate:

    wipe -> canary (3 docs) -> verify typing -> wipe canary -> ingest all
    -> retry the failures -> report

The wipe happens *before* the canary. The graph this lab builds is
disposable, rebuilt from scratch on every run, so there is nothing
worth preserving across a failed build. Wiping first also means the canary
runs against an empty graph, so entity resolution has nothing to merge into
and the check reflects exactly what this run extracted.
"""

import asyncio
import os
from pathlib import Path

from neo4j import Driver, GraphDatabase
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

from graph_config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EXTRACTION_MAX_TOKENS,
)
from workshop.bedrock_providers import BedrockEmbeddings, BedrockLLM
from workshop.graph_connection import NEO4J_URI, neo4j_auth
from workshop.graph_schema import (
    GRAPH_SCHEMA,
    OFF_SCHEMA_LABELS,
    SCHEMA_NODE_LABELS,
)
from workshop.retrieval_setup import (
    ensure_retrieval_indexes,
    missing_source_fixtures,
    report_readiness,
)

# The per-document bound the build enforces with `asyncio.wait_for`. It sits
# above a single Bedrock read timeout, not above the whole retry chain:
# `bedrock_providers.BEDROCK_CONFIG` allows 6 attempts at 45s, so a worst case
# of six consecutive hung sockets runs to 270s. That case ends with this
# timeout firing and the build moving on while the worker thread underneath
# keeps going, which is the trade recorded next to BEDROCK_CONFIG.
DOC_TIMEOUT_SECONDS = 180

# The canary samples several documents rather than one. LLM extraction is
# stochastic, so a single-document gate intermittently fails a healthy
# pipeline, and a participant who hits that concludes the lab is broken.
CANARY_DOCS = 3

# A document that failed once is tried once more. Extraction failures are
# usually a throttle or a timeout rather than a bad document, and without a
# retry one lost document costs a full rebuild.
RETRY_PASSES = 1

# Everything neo4j-graphrag writes carries this label, so the wipe can be
# scoped to this lab's own output instead of `MATCH (n) DETACH DELETE n`,
# which would also take out anything else sharing the instance.
KG_LABEL = "__KGBuilder__"


def graph_database() -> str:
    """Return the Neo4j database every session in this build opens.

    Read at call time rather than at import so a `.env` loaded by the caller is
    already in the environment. `NEO4J_DATABASE` used to be honoured by the
    fixture seed and ignored here, which left a non-default database holding
    half the lab.
    """
    return os.environ.get("NEO4J_DATABASE", "neo4j")


def connect() -> Driver:
    """Open a Neo4j driver using NEO4J_USERNAME / NEO4J_PASSWORD."""
    return GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())


def session(driver: Driver):
    """Open a session against the configured database."""
    return driver.session(database=graph_database())


def build_pipeline(driver: Driver) -> SimpleKGPipeline:
    """Construct the extraction pipeline with the schema pinned.

    Without `schema=`, `SimpleKGPipeline` asks the LLM to invent a schema per
    chunk, and the labels it invents do not match what the agent is told to
    query.
    """
    llm = BedrockLLM(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        max_tokens=EXTRACTION_MAX_TOKENS,
    )
    embedder = BedrockEmbeddings(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
    return SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=GRAPH_SCHEMA,
        text_splitter=FixedSizeSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        ),
        from_pdf=False,
        perform_entity_resolution=True,
    )


def snapshot_chunk_ids(driver: Driver) -> set[str]:
    """Return the element IDs of every :Chunk currently in the graph.

    The canary is scoped by chunk rather than by a diff over all nodes because
    `perform_entity_resolution=True` merges a newly extracted entity into an
    existing node when one already matches. Re-ingesting a document the graph
    already holds therefore creates a `Chunk` but no new `Hotel`, and a
    node-level diff reads that as "extraction produced no Hotel" when in fact
    it produced one and deduplicated it. Chunks are never merged, so they are a
    stable handle on "what this run just extracted".
    """
    with session(driver) as neo4j_session:
        return {
            record["id"]
            for record in neo4j_session.run(
                "MATCH (c:Chunk) RETURN elementId(c) AS id"
            )
        }


def clear_lab_graph(driver: Driver) -> None:
    """Delete only the nodes this lab created."""
    with session(driver) as neo4j_session:
        neo4j_session.run(f"MATCH (n:`{KG_LABEL}`) DETACH DELETE n")


# Entities are deleted only when every chunk they came from belongs to the
# document being cleared. `perform_entity_resolution=True` merges a hotel two
# documents both mention into one node, and deleting that node would take a
# healthy document's extraction with it.
DELETE_DOCUMENT_ENTITIES = """
MATCH (d:Document {path: $filename})<-[:FROM_DOCUMENT]-(c:Chunk)
WITH collect(c) AS chunks
UNWIND chunks AS chunk
MATCH (entity)-[:FROM_CHUNK]->(chunk)
WITH DISTINCT entity, chunks
WHERE all(source IN [(entity)-[:FROM_CHUNK]->(x) | x] WHERE source IN chunks)
DETACH DELETE entity
"""

DELETE_DOCUMENT_LEXICAL = """
MATCH (d:Document {path: $filename})
OPTIONAL MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d)
DETACH DELETE c, d
"""


def clear_document(driver: Driver, filename: str) -> None:
    """Remove everything one source document wrote, so a retry starts clean.

    A run that fails inside extraction can still have committed the lexical
    graph, and every node here is written with `CREATE` rather than `MERGE`. A
    plain retry would therefore leave a second `:Document` and a second
    `:Chunk` for that file, and the count assertion at the end of the build
    would fire on a graph that is otherwise complete.
    """
    with session(driver) as neo4j_session:
        neo4j_session.run(DELETE_DOCUMENT_ENTITIES, filename=filename).consume()
        neo4j_session.run(DELETE_DOCUMENT_LEXICAL, filename=filename).consume()


async def ingest(pipeline: SimpleKGPipeline, paths: list[Path]) -> list[Path]:
    """Run every document through the pipeline. Returns the ones that failed."""
    total = len(paths)
    failures: list[Path] = []
    for i, path in enumerate(paths, 1):
        text = path.read_text(encoding="utf-8")
        print(f"  [{i}/{total}] {path.name}...", end=" ", flush=True)
        try:
            await asyncio.wait_for(
                pipeline.run_async(
                    file_path=path.name,
                    text=text,
                    document_metadata={"source_filename": path.name},
                ),
                timeout=DOC_TIMEOUT_SECONDS,
            )
            print("✅")
        except asyncio.TimeoutError:
            failures.append(path)
            print("⏰ timeout")
        except Exception as exc:  # noqa: BLE001 - one bad doc must not stop the build
            failures.append(path)
            print(f"❌ {str(exc)[:80]}")
    return failures


async def retry_failures(
    driver: Driver,
    pipeline: SimpleKGPipeline,
    failures: list[Path],
) -> list[Path]:
    """Re-ingest failed documents, clearing each one's partial write first.

    Without this, a single throttled document costs a fifteen-minute rebuild:
    the count assertion below fires, and the next run clears the graph and
    starts over. Returns whatever still failed after `RETRY_PASSES`.
    """
    remaining = failures
    for attempt in range(1, RETRY_PASSES + 1):
        if not remaining:
            break
        print(
            f"\nRetry pass {attempt} of {RETRY_PASSES}: "
            f"{len(remaining)} document(s) to re-ingest"
        )
        for path in remaining:
            clear_document(driver, path.name)
        remaining = await ingest(pipeline, remaining)
    return remaining


def check_schema_held(driver: Driver, chunk_ids: set[str]) -> list[str]:
    """Return a list of problems with what the canary chunks extracted.

    Entities are reached by traversing `(:Chunk)<-[:FROM_CHUNK]-(entity)` from
    the chunks this run created, so the check is correct whether the entity was
    newly inserted or merged into an existing node by entity resolution.

    An empty list means extraction honoured the pinned schema in
    `workshop.graph_schema`, which is the contract Labs 2 through 5 query.
    """
    problems: list[str] = []
    ids = list(chunk_ids)
    with session(driver) as neo4j_session:
        labels = {
            record["label"]: record["count"]
            for record in neo4j_session.run(
                """
                MATCH (c:Chunk)<-[:FROM_CHUNK]-(n)
                WHERE elementId(c) IN $ids
                UNWIND labels(n) AS label
                WITH label, count(*) AS count
                WHERE NOT label STARTS WITH '__'
                RETURN label, count
                """,
                ids=ids,
            )
        }
        print(f"  labels produced: {labels}")

        stray = sorted(set(labels) & set(OFF_SCHEMA_LABELS))
        if stray:
            problems.append(f"off-schema labels present: {stray}")

        if not labels.get("Hotel"):
            problems.append("no :Hotel node was extracted from the canary chunks")
            return problems

        # Extraction is stochastic: an LLM can miss a field on any single
        # document without the pipeline being broken. The gate is therefore
        # "at least one canary document extracted a complete Hotel", not
        # "every one did". The off-schema label check above stays strict,
        # because inventing an `Address` node is a schema failure rather than
        # a bad roll.
        hotels = list(
            neo4j_session.run(
                """
                MATCH (c:Chunk)<-[:FROM_CHUNK]-(h:Hotel)
                WHERE elementId(c) IN $ids
                OPTIONAL MATCH (h)-[r]->(n)
                WHERE type(r) IN ['HAS_ROOM', 'OFFERS_AMENITY',
                                  'HAS_POLICY', 'PROVIDES_SERVICE']
                RETURN DISTINCT h.name AS name, h.address AS address,
                       h.guest_rating AS guest_rating, count(r) AS relationships
                """,
                ids=ids,
            )
        )

        conforming = []
        for hotel in hotels:
            missing = [
                field
                for field in ("name", "address", "guest_rating")
                if hotel[field] is None
            ]
            is_conforming = not missing and hotel["relationships"] > 0
            if is_conforming:
                conforming.append(hotel)
            status = "ok" if is_conforming else "INCOMPLETE"
            print(
                f"  hotel: {hotel['name']!r} rating={hotel['guest_rating']} "
                f"rels={hotel['relationships']} [{status}]"
            )

        print(f"  conforming hotels: {len(conforming)}/{len(hotels)}")
        if not conforming:
            problems.append(
                f"none of the {len(hotels)} canary hotels had name, address, "
                "guest_rating and a contracted relationship"
            )

    return problems


def count_documents(driver: Driver) -> int:
    """Return the number of :Document nodes in the graph.

    The invariant: after a clean build this equals the number of source files
    that were processed. Anything else means two builds overlapped or a partial
    run was left behind, and the resulting graph looks plausible while being
    wrong.
    """
    with session(driver) as neo4j_session:
        return neo4j_session.run(
            "MATCH (d:Document) RETURN count(d) AS count"
        ).single()["count"]


def count_chunks(driver: Driver) -> int:
    """Return the number of :Chunk nodes in the graph."""
    with session(driver) as neo4j_session:
        return neo4j_session.run(
            "MATCH (c:Chunk) RETURN count(c) AS count"
        ).single()["count"]


def report(driver: Driver) -> None:
    """Print the graph shape plus the three queries the notebook depends on."""
    with session(driver) as neo4j_session:
        print("\nNode labels:")
        for record in neo4j_session.run(
            """
            MATCH (n)
            WHERE any(l IN labels(n) WHERE l IN $labels)
            UNWIND [l IN labels(n) WHERE l IN $labels] AS label
            RETURN label, count(*) AS count
            ORDER BY count DESC
            """,
            labels=list(SCHEMA_NODE_LABELS),
        ):
            print(f"  :{record['label']}: {record['count']}")

        print("\nRelationship types:")
        for record in neo4j_session.run(
            """
            MATCH ()-[r]->()
            WHERE type(r) IN ['HAS_ROOM', 'OFFERS_AMENITY',
                              'HAS_POLICY', 'PROVIDES_SERVICE']
            RETURN type(r) AS rel, count(*) AS count
            ORDER BY count DESC
            """
        ):
            print(f"  :{record['rel']}: {record['count']}")

        print("\n--- Acceptance queries (these are what the notebook asks) ---")

        record = neo4j_session.run(
            """
            MATCH (h:Hotel)
            WHERE toLower(h.address) CONTAINS 'paris'
            RETURN avg(h.guest_rating) AS avg_rating, count(h) AS hotels
            """
        ).single()
        print(
            f"  Aggregation  avg guest rating in Paris: {record['avg_rating']} "
            f"across {record['hotels']} hotels"
        )

        record = neo4j_session.run(
            """
            MATCH (h:Hotel)-[:OFFERS_AMENITY]->(a:Amenity)
            WHERE toLower(a.name) CONTAINS 'pool'
            RETURN count(DISTINCT h) AS hotels
            """
        ).single()
        print(f"  Counting  hotels with a pool: {record['hotels']}")

        print("  Multi-hop  Cairo hotels with spa AND pool:")
        rows = neo4j_session.run(
            """
            MATCH (h:Hotel)-[:OFFERS_AMENITY]->(spa:Amenity),
                  (h)-[:OFFERS_AMENITY]->(pool:Amenity)
            WHERE h.address CONTAINS 'Cairo'
              AND toLower(spa.name) CONTAINS 'spa'
              AND toLower(pool.name) CONTAINS 'pool'
            RETURN DISTINCT h.name AS name, h.guest_rating AS rating
            """
        )
        found = False
        for record in rows:
            found = True
            print(f"    {record['name']}: {record['rating']}")
        if not found:
            print("    (none)")


async def run_build(paths: list[Path], title: str) -> int:
    """Canary, verify, wipe, ingest, retry, report. Returns an exit code."""
    if not paths:
        print("No documents selected.")
        return 1

    missing_sources = missing_source_fixtures(paths)
    if missing_sources:
        print("Source documents that later labs depend on are missing from this build:")
        for filename in missing_sources:
            print(f"  - {filename}")
        return 1

    print(f"{title}: {len(paths)} documents")
    print(f"Database: {graph_database()}\n")
    driver = connect()
    try:
        print("Clearing the previous graph this lab built...")
        clear_lab_graph(driver)
        print("✅ Cleared\n")

        canary = paths[:CANARY_DOCS]
        names = ", ".join(path.name for path in canary)
        print(f"Canary: extracting {names} before ingesting the rest...")
        baseline = snapshot_chunk_ids(driver)
        pipeline = build_pipeline(driver)
        await ingest(pipeline, canary)

        new_chunks = snapshot_chunk_ids(driver) - baseline
        if not new_chunks:
            print("\n❌ Canary produced no :Chunk. Extraction did not run.")
            clear_lab_graph(driver)  # leave a clean, empty graph on failure
            return 1
        problems = check_schema_held(driver, new_chunks)
        if problems:
            print("\n❌ Canary failed. The graph was cleared; fix and re-run:")
            for problem in problems:
                print(f"  - {problem}")
            clear_lab_graph(driver)  # remove the canary's partial docs
            return 1
        print("✅ Canary passed: extraction matches the documented schema\n")

        print("Clearing the canary's documents before the full ingest...")
        clear_lab_graph(driver)
        print("✅ Cleared\n")

        failures = await ingest(pipeline, paths)
        # No `await pipeline.close()` here. `SimpleKGPipeline` defines no
        # `close()`, so that call raised `AttributeError` at the end of every
        # otherwise-successful build. It owns no resource needing release; the
        # driver is closed in the `finally` below.

        # The retry runs before the count check below, so a throttled document
        # gets a second attempt instead of costing a fifteen-minute rebuild.
        # The assertion itself is unchanged: every selected source still has to
        # end up with exactly one Document and one Chunk.
        failures = await retry_failures(driver, pipeline, failures)
        if failures:
            print(
                f"\n{len(failures)} document(s) still failed after the retry pass:"
            )
            for path in failures:
                print(f"  - {path.name}")

        acknowledged = len(paths) - len(failures)
        print(f"\n{'=' * 60}")
        print(
            f"BUILD COMPLETE ({acknowledged}/{len(paths)} ingests acknowledged)"
        )
        print(f"{'=' * 60}")

        documents = count_documents(driver)
        chunks = count_chunks(driver)
        expected = len(paths)
        print(f"\n:Document nodes: {documents} (expected {expected})")
        print(f":Chunk nodes: {chunks} (expected {expected}, one chunk per document)")
        if documents != expected or chunks != expected:
            print(
                "❌ Document or chunk count does not match the selected source "
                "files. That means a build was incomplete, another build "
                "overlapped this one, or a partial run was left behind."
            )
            return 1
        if failures:
            print(
                "⚠️ One or more client acknowledgements were lost, but every "
                "source has a committed Document and Chunk. Continuing with "
                "graph fixture validation."
            )

        print("\nCreating and verifying the retrieval indexes...")
        ensure_retrieval_indexes(driver)
        print("✅ Retrieval indexes are online and match the embedding contract")

        readiness_problems = report_readiness(driver, expected_documents=expected)
        if readiness_problems:
            print("\n❌ Fixture validation for the later labs failed:")
            for problem in readiness_problems:
                print(f"  - {problem}")
            return 1

        report(driver)
        print("\n✅ Done!")
        return 0
    finally:
        driver.close()
