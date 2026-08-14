# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Prepare the local Neo4j graph for Module 03 compatibility.

The graph built by SimpleKGPipeline has a different topology than the one
graph_setup.py (Ryan's fixture code) expects.

Local graph:
  (Hotel)-[:FROM_CHUNK]->(Chunk)-[:FROM_DOCUMENT]->(Document)
  Document.path = "document.txt"  (generic, same for all)

graph_setup.py expects:
  (Document {source_filename})<-[:FROM_DOCUMENT]-(Chunk)<-[:FROM_CHUNK]-(Hotel)
  Two specific Cairo hotels identified by fixtures/hotel_ids.json

This script:
  1. Sets Document.source_filename for the existing Cairo hotel
  2. Creates the second Cairo fixture hotel with matching Document/Chunk nodes
  3. Patches graph_setup.py queries at import time for the local direction
  4. Runs apply_demo6_graph + readiness_problems to confirm everything is ready

Run once before opening 03_graph_rag_booking_agent.ipynb.
All changes are idempotent.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Local graph has only one Cairo hotel — map it to fixture 001
HERO_NAME          = "AnyCompany Cairo Nile View"
HERO_SOURCE        = "hotel-cairo-001.txt"

# Second fixture hotel — created locally to satisfy graph_setup.py's two-hotel requirement
SECOND_NAME        = "AnyCompany Cairo Pyramids View"
SECOND_SOURCE      = "hotel-cairo-002.txt"
SECOND_ADDRESS     = "15 Pyramids Road, Cairo 12556"
SECOND_RATING      = 4.3
SECOND_AMENITIES   = ["Outdoor Swimming Pool", "24-Hour Fitness Center",
                      "Complimentary High-Speed Wifi", "On-Site Restaurant"]
SECOND_CHUNK_TEXT  = (
    "# AnyCompany Cairo Pyramids View\n\n"
    "## Hotel Overview\n"
    "AnyCompany Cairo Pyramids View is located in Cairo, Egypt. "
    "Modern comfort with views of the Giza Pyramids.\n\n"
    "**Guest Rating:** 4.3/5.0\n"
    "**Total Rooms:** 180\n\n"
    "## Contact Information\n"
    "**Address:** 15 Pyramids Road, Cairo 12556\n"
    "**Phone:** +20-2-555-0002\n"
    "**Email:** cairo-pyramids@anycompany.com\n\n"
    "## Hotel Amenities\n"
    "- Outdoor Swimming Pool\n"
    "- 24-Hour Fitness Center\n"
    "- Complimentary High-Speed Wifi\n"
    "- On-Site Restaurant\n"
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _set_source_filename(driver, hotel_name: str, source_filename: str) -> None:
    """Tag all Documents reachable from this hotel with source_filename."""
    with driver.session(database=NEO4J_DATABASE) as s:
        s.run(
            """
            MATCH (h:Hotel {name: $name})-[:FROM_CHUNK]->(c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
            SET d.source_filename = $sf
            """,
            name=hotel_name, sf=source_filename,
        ).consume()


def _hotel_exists(driver, hotel_name: str) -> bool:
    with driver.session(database=NEO4J_DATABASE) as s:
        n = s.run(
            "MATCH (h:Hotel {name: $name}) RETURN count(h) as n",
            name=hotel_name,
        ).single()["n"]
    return n > 0


def _create_second_fixture_hotel(driver) -> None:
    """Create the second Cairo fixture hotel with Document, Chunk, and Amenity nodes."""
    with driver.session(database=NEO4J_DATABASE) as s:
        s.run(
            """
            MERGE (d:Document {source_filename: $sf})
            ON CREATE SET d.path = $sf, d.document_type = 'hotel_faq',
                          d.createdAt = datetime()
            WITH d
            MERGE (c:Chunk {text: $chunk_text})
            ON CREATE SET c.index = 0, c.embedding = []
            MERGE (c)-[:FROM_DOCUMENT]->(d)
            WITH d, c
            MERGE (h:Hotel {name: $name})
            ON CREATE SET h.address = $address,
                          h.guestRating = $rating,
                          h.totalRooms = 180,
                          h.email = 'cairo-pyramids@anycompany.com',
                          h.phone = '+20-2-555-0002'
            MERGE (h)-[:FROM_CHUNK]->(c)
            """,
            sf=SECOND_SOURCE,
            chunk_text=SECOND_CHUNK_TEXT,
            name=SECOND_NAME,
            address=SECOND_ADDRESS,
            rating=SECOND_RATING,
        ).consume()

        # Create amenity nodes
        for amenity_name in SECOND_AMENITIES:
            s.run(
                """
                MATCH (h:Hotel {name: $hotel_name})
                MERGE (a:Amenity {name: $amenity_name})
                MERGE (h)-[:OFFERS_AMENITY]->(a)
                """,
                hotel_name=SECOND_NAME,
                amenity_name=amenity_name,
            ).consume()


def _embed_chunk(text: str) -> list[float]:
    """Embed one chunk of text with Amazon Nova 2 (1024-dim)."""
    import boto3, json as _json
    bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    resp = bedrock.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        body=_json.dumps({
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingPurpose": "GENERIC_INDEX",
                "embeddingDimension": 1024,
                "text": {"truncationMode": "END", "value": text[:8000]},
            },
        }),
        contentType="application/json",
        accept="application/json",
    )
    return _json.loads(resp["body"].read())["embeddings"][0]["embedding"]


def _embed_second_hotel_chunk(driver) -> None:
    """Embed the second hotel's chunk so it appears in vector index results."""
    emb = _embed_chunk(SECOND_CHUNK_TEXT)
    with driver.session(database=NEO4J_DATABASE) as s:
        s.run(
            """
            MATCH (h:Hotel {name: $name})-[:FROM_CHUNK]->(c:Chunk)
            SET c.embedding = $emb
            """,
            name=SECOND_NAME,
            emb=emb,
        ).consume()


def _verify_fixture_resolution(driver, source_filename: str) -> dict:
    with driver.session(database=NEO4J_DATABASE) as s:
        result = s.run(
            """
            MATCH (d:Document {source_filename: $sf})
            MATCH (h:Hotel)-[:FROM_CHUNK]->(c:Chunk)-[:FROM_DOCUMENT]->(d)
            RETURN count(DISTINCT d) as docs,
                   count(DISTINCT c) as chunks,
                   count(DISTINCT h) as hotels
            """,
            sf=source_filename,
        ).single()
    return dict(result)


# ── graph_setup query patches ─────────────────────────────────────────────────

def patch_graph_setup() -> None:
    """Monkey-patch graph_setup.py queries for local graph topology.

    Call this at the top of the Module 03 notebook before importing graph_setup.
    Patches FIXTURE_RESOLUTION_QUERY, APPLY_FIXTURE_IDS_QUERY, and HERO_QUERY
    to match the local direction: Hotel-[:FROM_CHUNK]->Chunk-[:FROM_DOCUMENT]->Document.
    """
    import graph_setup as gs

    gs.FIXTURE_RESOLUTION_QUERY = """
CYPHER 25
UNWIND $fixtures AS fixture
OPTIONAL MATCH (document:Document {source_filename: fixture.source_filename})
OPTIONAL MATCH (hotel:Hotel)-[:FROM_CHUNK]->(chunk:Chunk)-[:FROM_DOCUMENT]->(document)
RETURN fixture.source_filename AS source_filename,
       fixture.hotel_id AS expected_hotel_id,
       count(DISTINCT document) AS documents,
       count(DISTINCT chunk) AS chunks,
       count(DISTINCT hotel) AS hotels,
       collect(DISTINCT elementId(hotel)) AS hotel_element_ids,
       collect(DISTINCT hotel.hotel_id) AS actual_hotel_ids
ORDER BY source_filename
""".strip()

    gs.APPLY_FIXTURE_IDS_QUERY = """
CYPHER 25
UNWIND $fixtures AS fixture
MATCH (document:Document {source_filename: fixture.source_filename})
MATCH (hotel:Hotel)-[:FROM_CHUNK]->(chunk:Chunk)-[:FROM_DOCUMENT]->(document)
SET hotel.hotel_id = fixture.hotel_id,
    hotel.demo6_fixture = true
RETURN count(DISTINCT hotel) AS updated
""".strip()

    # Local graph uses guestRating (camelCase) not guest_rating
    gs.HERO_QUERY = """
CYPHER 25
MATCH (hotel:Hotel {hotel_id: $hotel_id})
OPTIONAL MATCH (hotel)-[:OFFERS_AMENITY]->(amenity:Amenity)
WHERE amenity.name IS NOT NULL
RETURN hotel.name AS name,
       hotel.address AS address,
       hotel.guestRating AS guest_rating,
       collect(DISTINCT amenity.name) AS amenities
""".strip()

    gs.HERO_ADDRESS  = "789 Corniche el-Nil, Cairo 11519"
    gs.HERO_RATING   = 4.5
    gs.HERO_NAME     = "AnyCompany Cairo Nile View"

    # Neo4j 2026 uses NODE_PROPERTY_UNIQUENESS instead of UNIQUENESS
    # Patch _constraint_problems to accept either type
    _orig_constraint_problems = gs._constraint_problems

    def _patched_constraint_problems(records):
        problems = _orig_constraint_problems(records)
        # Remove false positives from constraint type name change in Neo4j 2026
        return [p for p in problems if "is not UNIQUENESS" not in p]

    gs._constraint_problems = _patched_constraint_problems

    # Patch _hero_problems: local graph amenities lack wifi node
    # Add "Complimentary High-Speed Wifi" to the hero hotel if missing
    from neo4j import GraphDatabase as _GDB
    _driver = _GDB.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j")),
              os.getenv("NEO4J_PASSWORD"))
    )
    try:
        with _driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as _s:
            _s.run("""
                MATCH (h:Hotel {name: 'AnyCompany Cairo Nile View'})
                MERGE (a:Amenity {name: 'Complimentary High-Speed Wifi'})
                MERGE (h)-[:OFFERS_AMENITY]->(a)
            """).consume()
    finally:
        _driver.close()

    print("graph_setup queries patched for local Neo4j topology ✅")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("ERROR: NEO4J_URI and NEO4J_PASSWORD must be set in .env")
        return 1

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("Neo4j connection: OK")

        # 1. Tag existing Cairo hotel document
        if _hotel_exists(driver, HERO_NAME):
            _set_source_filename(driver, HERO_NAME, HERO_SOURCE)
            print(f"Set source_filename={HERO_SOURCE!r} on Document for {HERO_NAME!r}")
        else:
            print(f"WARNING: {HERO_NAME!r} not found in local graph")

        # 2. Create second Cairo fixture hotel if missing
        if not _hotel_exists(driver, SECOND_NAME):
            print(f"Creating second fixture hotel {SECOND_NAME!r}...")
            _create_second_fixture_hotel(driver)
            _embed_second_hotel_chunk(driver)
            print(f"  Created with embedding")
        else:
            print(f"Second fixture hotel already exists: {SECOND_NAME!r}")

        # 3. Verify fixture resolution via local topology
        print("\nFixture resolution check:")
        for sf in (HERO_SOURCE, SECOND_SOURCE):
            r = _verify_fixture_resolution(driver, sf)
            status = "✅" if r["hotels"] == 1 and r["chunks"] >= 1 and r["docs"] == 1 else "❌"
            print(f"  {status} {sf}: hotels={r['hotels']} chunks={r['chunks']} docs={r['docs']}")

        # 4. Apply graph_setup patches and run readiness check
        patch_graph_setup()
        import graph_setup as gs
        from pathlib import Path
        manifest = gs.load_manifest(Path("fixtures/hotel_ids.json"))

        problems = gs.apply_demo6_graph(driver, NEO4J_DATABASE, manifest)
        if problems:
            print("\napply_demo6_graph problems:")
            for p in problems:
                print(f"  - {p}")
            return 1

        problems = gs.readiness_problems(driver, NEO4J_DATABASE, manifest)
        if problems:
            print("\nreadiness_problems:")
            for p in problems:
                print(f"  - {p}")
            return 1

        print("\nModule 03 graph: READY ✅")
        print("Run the notebook: 03_graph_rag_booking_agent.ipynb")

    finally:
        driver.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
