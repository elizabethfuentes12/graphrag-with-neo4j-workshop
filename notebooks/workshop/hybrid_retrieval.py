# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Fixed graph-enriched hybrid retrieval for Module 3.2's grounded booking agent.

The public tool accepts only ``query``. Index names, fusion behavior, result
count, and graph traversal are deliberately fixed rather than caller-tunable.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

import boto3
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.types import HybridSearchRanker, RetrieverResultItem

from workshop import contracts, graph_connection
from workshop.bedrock_providers import BedrockEmbeddings

MAX_EVIDENCE_CHARS = 1_200
MAX_EXACT_TERMS = 20

GROUNDING_INSTRUCTIONS = """
Answer hotel questions only from the returned chunk evidence and graph fields.
Do not infer live room inventory, guaranteed availability, or a completed
booking. Wording such as "subject to availability" describes a policy and is
not evidence that rooms are currently available. If the evidence does not
support the requested fact, say it cannot determine the answer from the
available hotel knowledge.
""".strip()

# ``node`` and ``score`` are supplied by HybridCypherRetriever. The traversal
# is reviewed, static Cypher: no query text is interpolated and no model writes
# or generates any part of it.
#
# The only two interpolated values are MAX_AMENITIES and MAX_EVIDENCE_CHARS,
# the named constants the rest of this module already trims to. Written as
# literals they agreed with the constants by coincidence, so changing a constant
# left the query returning the old bound. Both are module-level ints, never
# caller input. The doubled braces are the f-string escape for the Cypher
# subquery block.
RETRIEVAL_QUERY = f"""
OPTIONAL MATCH (node:Chunk)<-[:FROM_CHUNK]-(candidate:Hotel)
WITH node, score, candidate
WHERE score IS NOT NULL
ORDER BY score DESC,
         coalesce(candidate.hotel_id, '\uffff'),
         coalesce(candidate.name, '\uffff')
WITH node, score, head(collect(candidate)) AS hotel
CALL (hotel) {{
    MATCH (hotel)-[:OFFERS_AMENITY]->(amenity:Amenity)
    WHERE amenity.name IS NOT NULL
    WITH DISTINCT amenity.name AS amenity_name
    ORDER BY amenity_name
    LIMIT {contracts.MAX_AMENITIES}
    RETURN collect(amenity_name) AS amenities
}}
RETURN left(coalesce(node.text, ''), {MAX_EVIDENCE_CHARS}) AS chunk_evidence,
       score AS combined_score,
       hotel.hotel_id AS hotel_id,
       hotel.name AS hotel_name,
       hotel.address AS address,
       hotel.guest_rating AS guest_rating,
       amenities
ORDER BY combined_score DESC,
         coalesce(hotel_id, '\uffff'),
         coalesce(hotel_name, '\uffff')
""".strip()

_TERM_PATTERN = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)


@dataclass(frozen=True)
class Neo4jConfig:
    """Connection values shared by local and deployed retrieval paths.

    ``reservation_command.Neo4jCommandConfig`` is a near-duplicate of this
    class, and merging the two would break the reservation Lambda. That module
    documents why.
    """

    uri: str
    username: str
    password: str
    database: str

    @classmethod
    def from_environment(cls) -> "Neo4jConfig":
        """Load a participant's Aura connection from local environment values."""
        values = {name: os.environ.get(name) for name in contracts.REQUIRED_NEO4J_ENV}
        missing = [name for name, value in values.items() if not value]
        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Missing required Neo4j environment values: {names}")
        return cls(
            uri=values["NEO4J_URI"] or "",
            username=values["NEO4J_USERNAME"] or "",
            password=values["NEO4J_PASSWORD"] or "",
            database=graph_connection.graph_database(),
        )

    @classmethod
    def from_secret(
        cls,
        secret_id: str,
        *,
        secrets_client: Any | None = None,
    ) -> "Neo4jConfig":
        """Load the deployed read connection from an AWS Secrets Manager value."""
        client = secrets_client or boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_id)
        secret = json.loads(response["SecretString"])
        if not isinstance(secret, dict):
            raise ValueError("Neo4j secret must contain a JSON object")
        missing = [name for name in contracts.SECRET_FIELDS if not secret.get(name)]
        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Neo4j secret is missing required fields: {names}")
        return cls(**{name: secret[name] for name in contracts.SECRET_FIELDS})


@lru_cache(maxsize=2)
def _get_driver(config: Neo4jConfig):
    """Create once per connection and reuse the driver on warm invocations."""
    return GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password),
        notifications_min_severity="OFF",
    )


def _format_record(record: Mapping[str, Any]) -> RetrieverResultItem:
    """Preserve evidence separately from its structured graph enrichment."""
    return RetrieverResultItem(
        content=record.get("chunk_evidence") or "",
        metadata={
            "combined_score": record.get("combined_score"),
            "hotel_id": record.get("hotel_id"),
            "hotel_name": record.get("hotel_name"),
            "address": record.get("address"),
            "guest_rating": record.get("guest_rating"),
            "amenities": record.get("amenities") or [],
        },
    )


def build_retriever(
    config: Neo4jConfig,
    *,
    embedder: Embedder | None = None,
) -> HybridCypherRetriever:
    """Build the one fixed workshop retriever around the cached driver."""
    return HybridCypherRetriever(
        driver=_get_driver(config),
        vector_index_name=contracts.CHUNK_VECTOR_INDEX,
        fulltext_index_name=contracts.CHUNK_FULLTEXT_INDEX,
        retrieval_query=RETRIEVAL_QUERY,
        # The same class Module 1 wrote the chunk vectors with, so the query and
        # the stored vectors cannot drift onto different models or widths.
        embedder=embedder or BedrockEmbeddings(),
        result_formatter=_format_record,
        neo4j_database=config.database,
    )


@lru_cache(maxsize=1)
def _get_retriever() -> HybridCypherRetriever:
    secret_id = os.environ.get(contracts.READ_SECRET_ID_ENV)
    config = (
        Neo4jConfig.from_secret(secret_id)
        if secret_id
        else Neo4jConfig.from_environment()
    )
    return build_retriever(config)


def _exact_terms(query: str, evidence: str) -> list[str]:
    """Return bounded query terms using their verbatim spelling in evidence."""
    matches: list[str] = []
    seen: set[str] = set()
    for query_match in _TERM_PATTERN.finditer(query):
        term = query_match.group(0)
        evidence_match = re.search(
            rf"(?<!\w){re.escape(term)}(?!\w)",
            evidence,
            flags=re.IGNORECASE,
        )
        if evidence_match is None:
            continue
        verbatim = evidence_match.group(0)
        key = verbatim.casefold()
        if key in seen:
            continue
        seen.add(key)
        matches.append(verbatim)
        if len(matches) == MAX_EXACT_TERMS:
            break
    return matches


def _clean_amenities(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    unique = {
        amenity.strip()
        for amenity in value
        if isinstance(amenity, str) and amenity.strip()
    }
    return sorted(unique, key=str.casefold)[: contracts.MAX_AMENITIES]


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string or null")
    return value


def _number(value: Any, field: str, *, nullable: bool) -> float | None:
    if value is None:
        if nullable:
            return None
        raise ValueError(f"{field} must be numeric")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be numeric")
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{field} must be numeric") from error


def _to_evidence(query: str, item: RetrieverResultItem) -> contracts.HotelEvidence:
    evidence = str(item.content or "")[:MAX_EVIDENCE_CHARS]
    metadata = item.metadata or {}
    score = metadata.get("combined_score")
    rating = metadata.get("guest_rating")
    return {
        "chunk_evidence": evidence,
        "combined_score": _number(
            score,
            "combined_score",
            nullable=False,
        ),
        "exact_terms": _exact_terms(query, evidence),
        "hotel_id": _optional_string(metadata.get("hotel_id"), "hotel_id"),
        "hotel_name": _optional_string(
            metadata.get("hotel_name"),
            "hotel_name",
        ),
        "address": _optional_string(metadata.get("address"), "address"),
        "guest_rating": _number(
            rating,
            "guest_rating",
            nullable=True,
        ),
        "amenities": _clean_amenities(metadata.get("amenities")),
    }


def search_hotel_knowledge(query: str) -> list[contracts.HotelEvidence]:
    """Search hotel knowledge using the frozen, one-field tool contract."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    result = _get_retriever().search(
        query_text=query,
        top_k=contracts.HYBRID_TOP_K,
        ranker=HybridSearchRanker.NAIVE,
    )
    evidence = [
        _to_evidence(query, item)
        for item in result.items[: contracts.HYBRID_TOP_K]
    ]
    return sorted(
        evidence,
        key=lambda item: (
            -item["combined_score"],
            item["hotel_id"] or "\uffff",
            item["hotel_name"] or "\uffff",
        ),
    )
