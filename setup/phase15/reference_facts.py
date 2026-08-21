# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Deterministic reference facts for the Phase 1.5 comparison.

Source facts are derived from the committed corpus bytes. Graph facts are read
from Aura. They are kept apart on purpose: an extraction gap makes the two
disagree, and calling a graph aggregate the corpus ground truth would hide
exactly the gap this phase exists to measure.
"""

from __future__ import annotations

import re
from typing import Any

AMENITY_BLOCK = re.compile(r"^## Hotel Amenities\s*\n(.*?)(?=^###|\Z)", re.DOTALL | re.MULTILINE)
ROOM_TYPES = re.compile(
    r"^### Room Types Available\s*\n(.*?)(?=^###|^##|\Z)", re.DOTALL | re.MULTILINE
)
ROOM_TIER = re.compile(r"\*\*(.+?):\*\*.*?\$(\d+)-(\d+)")
SUITE_RATE_CEILING = 600
GUEST_RATING = re.compile(r"\*\*Guest Rating:\*\*\s*([\d.]+)")
TITLE = re.compile(r"^# (.+)$", re.MULTILINE)
POOL_NEGATION = "Pool facilities are not available at this property"


def _amenity_block(text: str) -> str:
    """Return the bullet list under `## Hotel Amenities`, or the empty string."""
    match = AMENITY_BLOCK.search(text)
    return match.group(1) if match else ""


def _rating(text: str) -> float | None:
    """Return the document's stated guest rating."""
    match = GUEST_RATING.search(text)
    return float(match.group(1)) if match else None


def _amenity_names(text: str) -> set[str]:
    """Return the amenity names the document lists, one per bullet."""
    return {
        line.strip().lstrip("- ").split(":")[0].strip()
        for line in _amenity_block(text).splitlines()
        if line.strip().startswith("-")
    }


def _suite_min_rate(text: str) -> int | None:
    """Return the low end of the document's suite nightly rate range."""
    match = ROOM_TYPES.search(text)
    if match is None:
        return None
    for name, low, _high in ROOM_TIER.findall(match.group(1)):
        if "suite" in name.lower():
            return int(low)
    return None


def _title(text: str) -> str:
    """Return the document's hotel name from its top-level heading."""
    match = TITLE.search(text)
    return match.group(1).strip() if match else ""


def source_facts(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive every Phase 1.5 reference fact from the committed corpus alone."""
    orlando = [
        {
            "filename": document["filename"],
            "name": _title(document["text"]),
            "guest_rating": _rating(document["text"]),
        }
        for document in documents
        if re.search(r"orlando", document["text"], re.IGNORECASE)
    ]
    ratings = [hotel["guest_rating"] for hotel in orlando]
    orlando_mean = round(sum(ratings) / len(ratings), 2) if ratings else None

    pool_listed = [
        document["filename"]
        for document in documents
        if re.search(r"pool", _amenity_block(document["text"]), re.IGNORECASE)
    ]
    pool_negated = [
        document["filename"]
        for document in documents
        if POOL_NEGATION in document["text"]
    ]

    chicago = []
    for document in documents:
        if not re.search(r"Chicago", document["text"]):
            continue
        block = _amenity_block(document["text"])
        chicago.append(
            {
                "filename": document["filename"],
                "name": _title(document["text"]),
                "guest_rating": _rating(document["text"]),
                "has_pool": bool(re.search(r"pool", block, re.IGNORECASE)),
                "has_spa": bool(re.search(r"spa", block, re.IGNORECASE)),
            }
        )

    chicago_amenity_sets = [
        _amenity_names(document["text"])
        for document in documents
        if re.search(r"Chicago", document["text"])
    ]
    shared_amenities = (
        sorted(set.intersection(*chicago_amenity_sets)) if chicago_amenity_sets else []
    )
    all_chicago_amenities = (
        sorted(set.union(*chicago_amenity_sets)) if chicago_amenity_sets else []
    )

    suite_and_spa = [
        {
            "filename": document["filename"],
            "name": _title(document["text"]),
            "suite_min_rate": _suite_min_rate(document["text"]),
        }
        for document in documents
        if "Full-Service Spa" in _amenity_names(document["text"])
        and (_suite_min_rate(document["text"]) or SUITE_RATE_CEILING)
        < SUITE_RATE_CEILING
    ]

    antarctica = [
        document["filename"]
        for document in documents
        if re.search(r"antarctic", document["text"], re.IGNORECASE)
    ]

    return {
        "document_count": len(documents),
        "orlando": {
            "hotels": orlando,
            "count": len(orlando),
            "mean_guest_rating": orlando_mean,
        },
        "pool": {
            "listed_in_amenities": len(pool_listed),
            "explicitly_unavailable": len(pool_negated),
            "overlap": len(set(pool_listed) & set(pool_negated)),
            "sum": len(pool_listed) + len(pool_negated),
        },
        "chicago": {
            "hotels": chicago,
            "candidates": len(chicago),
            "matches": sum(1 for h in chicago if h["has_pool"] and h["has_spa"]),
            "exclusions": sum(
                1 for h in chicago if not (h["has_pool"] and h["has_spa"])
            ),
        },
        "chicago_shared_amenities": {
            "hotels": len(chicago_amenity_sets),
            "shared": shared_amenities,
            "not_shared": [
                name for name in all_chicago_amenities if name not in shared_amenities
            ],
        },
        "suite_and_spa": {
            "ceiling": SUITE_RATE_CEILING,
            "count": len(suite_and_spa),
            "hotels": suite_and_spa,
        },
        "antarctica": {"documents": len(antarctica)},
    }


GRAPH_FACT_QUERIES: dict[str, str] = {
    "node_counts": """
CYPHER 25
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS count
ORDER BY count DESC
""".strip(),
    "orlando": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'orlando'
RETURN h.name AS name, h.guest_rating AS guest_rating
ORDER BY name
""".strip(),
    "orlando_mean": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'orlando' AND h.guest_rating IS NOT NULL
RETURN count(h) AS rated_hotels, round(avg(h.guest_rating), 2) AS mean_guest_rating
""".strip(),
    "pool_hotels": """
CYPHER 25
MATCH (h:Hotel)-[:OFFERS_AMENITY]->(a:Amenity)
WHERE toLower(a.name) CONTAINS 'pool'
RETURN count(DISTINCT h) AS hotels_with_pool
""".strip(),
    "chicago": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'chicago'
RETURN h.name AS name,
       h.guest_rating AS guest_rating,
       [(h)-[:OFFERS_AMENITY]->(a:Amenity) | a.name] AS amenities
ORDER BY name
""".strip(),
    "chicago_spa_and_pool": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'chicago'
  AND EXISTS { (h)-[:OFFERS_AMENITY]->(a:Amenity) WHERE toLower(a.name) CONTAINS 'pool' }
  AND EXISTS { (h)-[:OFFERS_AMENITY]->(a:Amenity) WHERE toLower(a.name) CONTAINS 'spa' }
RETURN h.name AS name, h.guest_rating AS guest_rating
ORDER BY name
""".strip(),
    "antarctica": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'antarctica'
RETURN count(h) AS hotels
""".strip(),
    "chicago_shared_amenities": """
CYPHER 25
MATCH (h:Hotel)
WHERE toLower(h.address) CONTAINS 'chicago'
MATCH (h)-[:OFFERS_AMENITY]->(a:Amenity)
WITH count(DISTINCT h) AS chicago_hotels, a.name AS amenity, count(DISTINCT h) AS holders
WITH collect({amenity: amenity, holders: holders}) AS rows, max(chicago_hotels) AS total
RETURN total AS chicago_hotels,
       [row IN rows WHERE row.holders = total | row.amenity] AS shared,
       [row IN rows WHERE row.holders < total | row.amenity] AS not_shared
""".strip(),
    "suite_and_spa": """
CYPHER 25
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)
WHERE toLower(r.type) CONTAINS 'suite' AND r.min_rate < 600
  AND EXISTS { (h)-[:OFFERS_AMENITY]->(a:Amenity) WHERE toLower(a.name) CONTAINS 'spa' }
RETURN count(DISTINCT h) AS hotels
""".strip(),
    "total_hotels": """
CYPHER 25
MATCH (h:Hotel) RETURN count(h) AS hotels
""".strip(),
}


def graph_facts(session: Any) -> dict[str, Any]:
    """Run every reference query against a read session and return raw rows."""
    facts: dict[str, Any] = {}
    for name, query in GRAPH_FACT_QUERIES.items():
        facts[name] = [dict(record) for record in session.run(query)]
    return facts
