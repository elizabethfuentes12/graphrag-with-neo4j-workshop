# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Reconcile a restored graph's amenities with the committed source archive."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from neo4j import Driver, GraphDatabase

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
if str(NOTEBOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOKS_DIR))

from workshop.amenities import AmenitySectionError, parse_amenity_section
from workshop.graph_connection import (
    graph_database,
    neo4j_auth,
    neo4j_uri,
    require_neo4j_env,
)

CORPUS_ARCHIVE = NOTEBOOKS_DIR / "02-connected-context" / "hotel-faqs.zip"

DOCUMENT_QUERY = """
CYPHER 25
MATCH (document:Document)
RETURN document.source_filename AS filename,
       count(document) AS document_count
ORDER BY filename
""".strip()

ASSERTION_QUERY = """
CYPHER 25
MATCH (document:Document)<-[:FROM_DOCUMENT]-(chunk:Chunk)<-[:FROM_CHUNK]-(hotel:Hotel)
MATCH (hotel)-[offer:OFFERS_AMENITY]->(amenity:Amenity)
RETURN document.source_filename AS filename,
       amenity.name AS amenity_name,
       count(DISTINCT offer) AS relationship_count
ORDER BY filename, amenity_name
""".strip()

AMENITY_QUERY = """
CYPHER 25
MATCH (amenity:Amenity)
RETURN amenity.name AS amenity_name,
       count(amenity) AS node_count
ORDER BY amenity_name
""".strip()


def _read_graph_rows(
    driver: Driver,
    database: str,
) -> tuple[list[Any], list[Any], list[Any]]:
    with driver.session(database=database) as session:
        documents = list(session.run(DOCUMENT_QUERY))
        assertions = list(session.run(ASSERTION_QUERY))
        amenities = list(session.run(AMENITY_QUERY))
    return documents, assertions, amenities


def amenity_reconciliation_problems(
    driver: Driver,
    database: str,
    corpus_archive: Path = CORPUS_ARCHIVE,
) -> list[str]:
    """Return exact source-to-graph reconciliation defects.

    The graph supplies the loaded source filenames. The same validator can
    therefore check lite, prebuilt, and complete artifacts without receiving
    the original build paths.
    """
    document_rows, assertion_rows, amenity_rows = _read_graph_rows(driver, database)

    problems: list[str] = []
    source_filenames: set[str] = set()
    for row in document_rows:
        filename = row["filename"]
        document_count = row["document_count"]
        if not filename:
            problems.append(
                f"{document_count} Document node(s) have no source_filename"
            )
            continue
        if document_count != 1:
            problems.append(
                f"{filename} has {document_count} Document nodes, expected 1"
            )
            continue
        source_filenames.add(filename)

    try:
        with ZipFile(corpus_archive) as corpus:
            archive_names = set(corpus.namelist())
            missing_sources = source_filenames - archive_names
            if missing_sources:
                examples = ", ".join(sorted(missing_sources)[:5])
                problems.append(
                    f"{len(missing_sources)} graph source files are absent from the "
                    f"committed corpus archive; examples: {examples}"
                )
            expected = {
                (filename, amenity_name)
                for filename in source_filenames & archive_names
                for amenity_name in parse_amenity_section(
                    corpus.read(filename).decode("utf-8"), filename
                ).names
            }
    except (BadZipFile, FileNotFoundError, UnicodeDecodeError, AmenitySectionError) as exc:
        problems.append(f"could not read authoritative amenity sources: {exc}")
        return problems

    actual = {
        (row["filename"], row["amenity_name"])
        for row in assertion_rows
        if row["filename"] is not None and row["amenity_name"] is not None
    }
    missing = expected - actual
    unexpected = actual - expected
    if missing:
        examples = ", ".join(
            f"{filename}: {name}" for filename, name in sorted(missing)[:5]
        )
        problems.append(
            f"{len(missing)} source amenity assertions are missing; examples: "
            f"{examples}"
        )
    if unexpected:
        examples = ", ".join(
            f"{filename}: {name}"
            for filename, name in sorted(
                unexpected,
                key=lambda pair: (str(pair[0]), str(pair[1])),
            )[:5]
        )
        problems.append(
            f"{len(unexpected)} unexpected amenity assertions exist; examples: "
            f"{examples}"
        )

    for row in assertion_rows:
        if row["relationship_count"] != 1:
            problems.append(
                f"{row['filename']}: {row['amenity_name']} has "
                f"{row['relationship_count']} OFFERS_AMENITY relationships, "
                "expected 1"
            )

    expected_names = {name for _, name in expected}
    actual_names = {
        row["amenity_name"] for row in amenity_rows if row["amenity_name"] is not None
    }
    missing_names = expected_names - actual_names
    unexpected_names = actual_names - expected_names
    if missing_names:
        problems.append(
            "Amenity nodes are missing for: " + ", ".join(sorted(missing_names)[:5])
        )
    if unexpected_names:
        problems.append(
            "unexpected Amenity nodes exist for: "
            + ", ".join(sorted(unexpected_names)[:5])
        )
    for row in amenity_rows:
        if row["node_count"] != 1:
            problems.append(
                f"Amenity {row['amenity_name']!r} has {row['node_count']} nodes, "
                "expected 1 shared node"
            )

    print(
        f"Amenity reconciliation: {len(source_filenames)} sources, "
        f"{len(expected_names)} names, {len(actual)} graph assertions, "
        f"{len(expected)} expected assertions"
    )
    return problems


def main() -> int:
    """Validate the configured restored graph and print actionable defects."""
    require_neo4j_env()
    with GraphDatabase.driver(neo4j_uri(), auth=neo4j_auth()) as driver:
        problems = amenity_reconciliation_problems(driver, graph_database())
    if problems:
        print("Amenity reconciliation failed:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Amenity reconciliation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
