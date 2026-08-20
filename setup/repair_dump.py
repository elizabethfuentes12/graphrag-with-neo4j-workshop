# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Reapply the 2026-08-18 live repair to a freshly restored dump.

The shipped `.dump` predates two pieces of graph state that Modules 3.2, 4.1,
and 5.1 depend on, and neither is written by anything in this repository:

1. `Document.source_filename`. `graph_builder.ingest()` has attached it to
   every document it writes for a while now, but the dump's original 300
   documents were bulk-loaded before that existed, so they carry no
   `source_filename` at all. Nothing else on those nodes says which corpus
   file they came from, so this script recovers it by content: chunk 0 of
   each untagged `Document` is compared against every file in the committed
   `hotel-faqs.zip`, and a `Document` whose chunk 0 text is a prefix of
   exactly one file's text is tagged with that file's name. A `Document`
   that matches zero or more than one file is left alone and reported
   instead of guessed at.
2. `Hotel.hotel_id` and the `demo-06-maximum-guests` `Rule`. These are
   already handled by the committed, idempotent `workshop.fixtures` module,
   which this script calls. `fixtures.py` only pins the two Cairo fixture
   hotels by name; every other hotel just needs *some* unique ID, since
   hybrid retrieval selects `hotel.hotel_id` for every hotel it returns, so
   this script also backfills a `randomUUID()` onto any hotel `fixtures.py`
   didn't touch.

Safe to re-run: every step here only acts on nodes that still need it.

Run it once after restoring the dump and before testing Modules 3 through 6:

    cd notebooks
    uv run python ../setup/repair_dump.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = REPO_ROOT / "notebooks"
MODULE_2 = NOTEBOOKS / "02-vector-rag-hallucinates"

for _path in (NOTEBOOKS, MODULE_2):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

CORPUS_ARCHIVE = MODULE_2 / "hotel-faqs.zip"

FIND_UNTAGGED_DOCUMENTS_QUERY = """
CYPHER 25
MATCH (d:Document)
WHERE d.source_filename IS NULL
OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk {index: 0})
RETURN elementId(d) AS element_id, c.text AS first_chunk_text
""".strip()

SET_SOURCE_FILENAME_QUERY = """
CYPHER 25
MATCH (d:Document)
WHERE elementId(d) = $element_id
SET d.source_filename = $source_filename
""".strip()

BACKFILL_HOTEL_IDS_QUERY = """
CYPHER 25
MATCH (hotel:Hotel)
WHERE hotel.hotel_id IS NULL
SET hotel.hotel_id = randomUUID()
RETURN count(hotel) AS updated
""".strip()


def _load_corpus_texts() -> dict[str, str]:
    """Map every shipped source filename to its full document text."""
    if not CORPUS_ARCHIVE.exists():
        raise FileNotFoundError(
            f"The source corpus is missing: {CORPUS_ARCHIVE.resolve()}. It "
            "ships in the repository next to prepare_graph.py."
        )
    with zipfile.ZipFile(CORPUS_ARCHIVE) as corpus:
        return {name: corpus.read(name).decode("utf-8") for name in corpus.namelist()}


def backfill_source_filenames(session) -> tuple[int, list[str]]:
    """Tag every untagged Document with the corpus file it was built from."""
    corpus = _load_corpus_texts()
    untagged = list(session.run(FIND_UNTAGGED_DOCUMENTS_QUERY))

    updated = 0
    problems: list[str] = []
    for record in untagged:
        element_id = record["element_id"]
        chunk_text = record["first_chunk_text"]
        if not chunk_text:
            problems.append(f"{element_id} has no chunk 0 to match against")
            continue
        matches = [
            filename for filename, text in corpus.items() if text.startswith(chunk_text)
        ]
        if len(matches) != 1:
            problems.append(f"{element_id} matched {len(matches)} corpus files: {matches}")
            continue
        session.execute_write(
            lambda tx, eid=element_id, fn=matches[0]: tx.run(
                SET_SOURCE_FILENAME_QUERY, element_id=eid, source_filename=fn
            ).consume()
        )
        updated += 1
    return updated, problems


def backfill_hotel_ids(session) -> int:
    """Give every Hotel node without one an opaque `hotel_id`."""
    return session.execute_write(
        lambda tx: tx.run(BACKFILL_HOTEL_IDS_QUERY).single()["updated"]
    )


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")

    from workshop import fixtures
    from workshop.graph_connection import graph_database, neo4j_auth, neo4j_uri, require_neo4j_env

    require_neo4j_env()

    from neo4j import GraphDatabase

    manifest = fixtures.load_manifest()
    driver = GraphDatabase.driver(
        neo4j_uri(), auth=neo4j_auth(), notifications_min_severity="OFF"
    )
    try:
        with driver.session(database=graph_database()) as session:
            doc_updated, doc_problems = backfill_source_filenames(session)
            print(f"Tagged {doc_updated} Document(s) with source_filename.")
            for problem in doc_problems:
                print(f"  - {problem}")

            hotel_updated = backfill_hotel_ids(session)
            print(f"Backfilled hotel_id on {hotel_updated} Hotel node(s).")

        fixture_problems = fixtures.apply_reservation_fixtures(driver, graph_database(), manifest)
        if fixture_problems:
            print("Could not apply the Module 3.2 fixtures:")
            for problem in fixture_problems:
                print(f"  - {problem}")
            return 1

        readiness_problems = fixtures.readiness_problems(driver, graph_database(), manifest)
    finally:
        driver.close()

    if doc_problems or readiness_problems:
        print("\nRepair finished with unresolved problems:")
        for problem in readiness_problems:
            print(f"  - {problem}")
        return 1

    print("\nRepair complete. Module 3.2 fixtures are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
