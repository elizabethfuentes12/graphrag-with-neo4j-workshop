# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Index setup and readiness checks shared by the Lab 1 build paths.

The notebook only retrieves. Graph preparation owns index creation and checks
the deterministic fixtures every Lab 1 build path needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

from neo4j import Driver
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index

from workshop.contracts import graph_database
from workshop.graph_schema import GRAPH_SCHEMA, SCHEMA_NODE_LABELS
from workshop.retrieval_contract import (
    CHUNK_FULLTEXT_INDEX,
    CHUNK_VECTOR_INDEX,
    EMBEDDING_DIMENSIONS,
)

# The source documents every lab after Lab 1 asks a question against. A build
# that samples the corpus has to include these or a later lab opens onto a
# graph that cannot answer its own hero question.
REQUIRED_SOURCE_FILES = (
    "hotel-paris-001.txt",
    "hotel-paris-002.txt",
    "hotel-cairo-001.txt",
    "hotel-cairo-002.txt",
    "hotel-chicago-001.txt",
)

# Derived from the pinned schema rather than restated. The extraction contract
# in graph_schema is what the build refuses to write outside of, so counting a
# relationship type this readiness check names but that schema does not pin
# would report a number the build can never produce.
SCHEMA_RELATIONSHIP_TYPES = tuple(
    entry["label"]
    for entry in cast(
        Sequence[Mapping[str, str]], GRAPH_SCHEMA["relationship_types"]
    )
)


class ReadinessError(RuntimeError):
    """Raised when an index exists but does not match the retrieval contract."""


@dataclass(frozen=True)
class Fixture:
    """One graph fact required by a learner-facing question."""

    name: str
    query: str
    parameters: Mapping[str, Any]
    minimum: int = 1


REQUIRED_FIXTURES = (
    Fixture(
        name="Paris ratings for aggregation",
        query="""
            MATCH (h:Hotel)
            WHERE toLower(h.address) CONTAINS 'paris'
              AND h.guest_rating IS NOT NULL
            RETURN count(DISTINCT h) AS actual
        """,
        parameters={},
        minimum=2,
    ),
    Fixture(
        name="hotel-to-pool relationship for counting",
        query="""
            MATCH (h:Hotel)-[:OFFERS_AMENITY]->(a:Amenity)
            WHERE toLower(a.name) CONTAINS 'pool'
            RETURN count(DISTINCT h) AS actual
        """,
        parameters={},
    ),
    Fixture(
        name="Cairo spa-and-pool multi-hop result",
        query="""
            MATCH (h:Hotel)-[:OFFERS_AMENITY]->(spa:Amenity),
                  (h)-[:OFFERS_AMENITY]->(pool:Amenity)
            WHERE toLower(h.address) CONTAINS 'cairo'
              AND toLower(spa.name) CONTAINS 'spa'
              AND toLower(pool.name) CONTAINS 'pool'
              AND h.guest_rating IS NOT NULL
            RETURN count(DISTINCT h) AS actual
        """,
        parameters={},
    ),
    Fixture(
        name="Windward Mile Tower hotel at postal code 60611",
        query="""
            MATCH (h:Hotel)
            WHERE h.name = $hotel_name AND h.address CONTAINS $postal_code
            RETURN count(h) AS actual
        """,
        parameters={
            "hotel_name": "Windward Mile Tower",
            "postal_code": "60611",
        },
    ),
    Fixture(
        name="embedded Windward Mile Tower chunk containing 60611",
        query="""
            MATCH (c:Chunk)
            WHERE c.text CONTAINS $hotel_name
              AND c.text CONTAINS $postal_code
              AND c.embedding IS NOT NULL
              AND size(c.embedding) = $dimensions
            RETURN count(c) AS actual
        """,
        parameters={
            "hotel_name": "Windward Mile Tower",
            "postal_code": "60611",
            "dimensions": EMBEDDING_DIMENSIONS,
        },
    ),
)


def missing_source_fixtures(paths: Iterable[Path]) -> list[str]:
    """Return required source filenames absent from ``paths``."""
    selected = {path.name for path in paths}
    return sorted(set(REQUIRED_SOURCE_FILES) - selected)


def _session(driver: Driver):
    """Open a session against the configured database.

    Indexes, counts, and fixture checks all have to land on the database the
    build wrote to. Left on the driver's home database, a participant who sets
    `NEO4J_DATABASE` gets data in one place and indexes in another, and every
    later lab retrieves nothing while every call succeeds.
    """
    return driver.session(database=graph_database())


def ensure_retrieval_indexes(driver: Driver) -> None:
    """Create the two chunk indexes idempotently and verify their contracts."""
    database = graph_database()
    create_vector_index(
        driver=driver,
        name=CHUNK_VECTOR_INDEX,
        label="Chunk",
        embedding_property="embedding",
        dimensions=EMBEDDING_DIMENSIONS,
        similarity_fn="cosine",
        fail_if_exists=False,
        neo4j_database=database,
    )
    create_fulltext_index(
        driver=driver,
        name=CHUNK_FULLTEXT_INDEX,
        label="Chunk",
        node_properties=["text"],
        fail_if_exists=False,
        neo4j_database=database,
    )
    with _session(driver) as session:
        session.run("CALL db.awaitIndexes($timeout_seconds)", timeout_seconds=300).consume()
    verify_retrieval_indexes(driver)


def _index_contract_problems(records: Iterable[Mapping[str, Any]]) -> list[str]:
    """Return mismatches between SHOW INDEXES records and the retrieval contract."""
    indexes = {record["name"]: record for record in records}
    problems: list[str] = []

    expected = {
        CHUNK_VECTOR_INDEX: {
            "type": "VECTOR",
            "labels": ["Chunk"],
            "properties": ["embedding"],
        },
        CHUNK_FULLTEXT_INDEX: {
            "type": "FULLTEXT",
            "labels": ["Chunk"],
            "properties": ["text"],
        },
    }
    for name, contract in expected.items():
        record = indexes.get(name)
        if record is None:
            problems.append(f"missing index {name!r}")
            continue
        if record.get("state") != "ONLINE":
            problems.append(f"index {name!r} is {record.get('state')!r}, not 'ONLINE'")
        if record.get("type") != contract["type"]:
            problems.append(
                f"index {name!r} has type {record.get('type')!r}, "
                f"expected {contract['type']!r}"
            )
        if record.get("labelsOrTypes") != contract["labels"]:
            problems.append(
                f"index {name!r} targets {record.get('labelsOrTypes')!r}, "
                f"expected {contract['labels']!r}"
            )
        if record.get("properties") != contract["properties"]:
            problems.append(
                f"index {name!r} covers {record.get('properties')!r}, "
                f"expected {contract['properties']!r}"
            )

    vector = indexes.get(CHUNK_VECTOR_INDEX)
    if vector is not None:
        config = vector.get("options", {}).get("indexConfig", {})
        dimensions = config.get("vector.dimensions")
        similarity = config.get("vector.similarity_function")
        if dimensions != EMBEDDING_DIMENSIONS:
            problems.append(
                f"index {CHUNK_VECTOR_INDEX!r} has {dimensions!r} dimensions, "
                f"expected {EMBEDDING_DIMENSIONS}"
            )
        normalized_similarity = (
            similarity.lower() if isinstance(similarity, str) else similarity
        )
        if normalized_similarity != "cosine":
            problems.append(
                f"index {CHUNK_VECTOR_INDEX!r} uses {similarity!r}, "
                "expected 'cosine'"
            )
    return problems


def verify_retrieval_indexes(driver: Driver) -> None:
    """Raise with a precise message unless both retrieval indexes are ready."""
    with _session(driver) as session:
        records = list(
            session.run(
                """
                SHOW INDEXES
                YIELD name, type, state, labelsOrTypes, properties, options
                WHERE name IN $names
                RETURN name, type, state, labelsOrTypes, properties, options
                """,
                names=[CHUNK_VECTOR_INDEX, CHUNK_FULLTEXT_INDEX],
            )
        )
    problems = _index_contract_problems(records)
    if problems:
        details = "\n  - ".join(problems)
        raise ReadinessError(f"Retrieval index check failed:\n  - {details}")


def graph_counts(driver: Driver) -> tuple[int, int, dict[str, int], dict[str, int]]:
    """Return document, chunk, extracted-label, and relationship counts."""
    with _session(driver) as session:
        document_count = session.run(
            "MATCH (d:Document) RETURN count(d) AS count"
        ).single()["count"]
        chunk_count = session.run(
            "MATCH (c:Chunk) RETURN count(c) AS count"
        ).single()["count"]
        label_counts = {
            record["label"]: record["count"]
            for record in session.run(
                """
                MATCH (n)
                UNWIND [label IN labels(n) WHERE label IN $labels] AS label
                RETURN label, count(*) AS count
                ORDER BY label
                """,
                labels=list(SCHEMA_NODE_LABELS),
            )
        }
        relationship_counts = {
            record["relationship"]: record["count"]
            for record in session.run(
                """
                MATCH ()-[r]->()
                WHERE type(r) IN $types
                RETURN type(r) AS relationship, count(*) AS count
                ORDER BY relationship
                """,
                types=list(SCHEMA_RELATIONSHIP_TYPES),
            )
        }
    return document_count, chunk_count, label_counts, relationship_counts


def fixture_problems(driver: Driver) -> list[str]:
    """Return missing or under-populated required graph fixtures."""
    problems: list[str] = []
    with _session(driver) as session:
        for fixture in REQUIRED_FIXTURES:
            record = session.run(fixture.query, **dict(fixture.parameters)).single()
            actual = 0 if record is None else record["actual"]
            if actual < fixture.minimum:
                problems.append(
                    f"{fixture.name}: found {actual}, expected at least {fixture.minimum}"
                )
    return problems


def report_readiness(driver: Driver, expected_documents: int) -> list[str]:
    """Print readiness counts and return all graph fixture problems."""
    documents, chunks, labels, relationships = graph_counts(driver)
    print("\nLab 1 readiness report:")
    print(f"  documents: {documents} (expected {expected_documents})")
    print(f"  chunks: {chunks} (expected {documents})")
    print(f"  extracted labels: {labels}")
    print(f"  relationships: {relationships}")

    problems = fixture_problems(driver)
    if documents != expected_documents:
        problems.insert(
            0,
            f"document count is {documents}, expected {expected_documents}",
        )
    if chunks != documents:
        problems.insert(1, f"chunk count is {chunks}, expected {documents}")
    return problems
