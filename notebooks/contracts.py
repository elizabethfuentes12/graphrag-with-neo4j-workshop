# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Frozen service and graph contracts for Module 03.

This module intentionally contains no AWS or Neo4j clients. It is safe to
import from local tests, notebooks, and the reservation command without
causing network calls or resource changes.
"""

from enum import StrEnum
from typing import Final, Literal, NotRequired, TypedDict

EMBEDDING_MODEL_ID: Final = "amazon.nova-2-multimodal-embeddings-v1:0"
EMBEDDING_PURPOSE: Final = "GENERIC_INDEX"
EMBEDDING_DIMENSIONS: Final = 1024
CHUNK_VECTOR_INDEX: Final = "hotel_chunk_embeddings"
CHUNK_FULLTEXT_INDEX: Final = "hotel_chunk_fulltext"
HYBRID_RANKER: Final = "NAIVE"
HYBRID_TOP_K: Final = 5
MAX_AMENITIES: Final = 12

WORKSHOP_OWNER: Final = "neo4j-ftw-demo-6"
FIXTURE_MANIFEST_VERSION: Final = 1
MAX_GUESTS_RULE_ID: Final = "demo-06-maximum-guests"
MAX_GUESTS: Final = 10
OVER_LIMIT_GUESTS: Final = 15

LOCAL_NEO4J_ENV: Final = (
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
)
READ_SECRET_ID_ENV: Final = "NEO4J_READ_SECRET_ID"
COMMAND_SECRET_ID_ENV: Final = "NEO4J_COMMAND_SECRET_ID"
SECRET_FIELDS: Final = ("uri", "username", "password", "database")


class ReservationStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"


class ReservationReason(StrEnum):
    MAX_GUESTS_EXCEEDED = "max_guests_exceeded"
    UNKNOWN_HOTEL = "unknown_hotel"
    INVALID_DATES = "invalid_dates"
    UNAUTHORIZED = "unauthorized"
    SERVICE_ERROR = "service_error"


class HotelEvidence(TypedDict):
    chunk_evidence: str
    combined_score: float
    exact_terms: list[str]
    hotel_id: str | None
    hotel_name: str | None
    address: str | None
    guest_rating: float | None
    amenities: list[str]


class ReservationCommandInput(TypedDict):
    request_id: str
    hotel_id: str
    check_in: str
    check_out: str
    guests: int


class ReservationCommandResponse(TypedDict):
    status: Literal["accepted", "rejected", "error"]
    request_id: str
    hotel_id: str
    duplicate: bool
    message: str
    reason_code: NotRequired[
        Literal[
            "max_guests_exceeded",
            "unknown_hotel",
            "invalid_dates",
            "unauthorized",
            "service_error",
        ]
    ]
    max_guests: NotRequired[int]
    created_at: NotRequired[str]


def retrieval_input_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 1,
                "description": "Natural-language hotel question.",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    }


def reservation_input_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "format": "uuid",
                "description": "Caller-created UUID. Reuse it if this command is retried.",
            },
            "hotel_id": {
                "type": "string",
                "minLength": 1,
                "description": "Opaque stable hotel ID returned by grounded retrieval.",
            },
            "check_in": {
                "type": "string",
                "format": "date",
                "description": "Check-in date in YYYY-MM-DD format.",
            },
            "check_out": {
                "type": "string",
                "format": "date",
                "description": "Check-out date in YYYY-MM-DD format.",
            },
            "guests": {
                "type": "integer",
                "minimum": 1,
                "description": "Requested number of guests.",
            },
        },
        "required": ["request_id", "hotel_id", "check_in", "check_out", "guests"],
        "additionalProperties": False,
    }
