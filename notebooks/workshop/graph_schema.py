# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""The pinned extraction schema every lab agrees on.

Without a pinned schema `SimpleKGPipeline` lets the LLM invent a fresh set of
labels for every chunk, so one document yields `Address` nodes and another
yields `RoomType`/`BedConfiguration`. Lab 3's retrieval tool promises the agent
a fixed contract, and the graph has to actually honour it.

This module reads no environment and opens no client, so it is safe to import
from tests and from the reservation Lambda.
"""

# Every property name is snake_case, and location lives on `Hotel.address`
# rather than in a separate `Address` node, because that is what the agent is
# told to expect.
GRAPH_SCHEMA: dict[str, object] = {
    "node_types": [
        {
            "label": "Hotel",
            "description": "A hotel property. One per source document.",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Full hotel name."},
                {
                    "name": "address",
                    "type": "STRING",
                    "description": (
                        "Full street address including city and country. "
                        "Never model the address as its own node."
                    ),
                },
                {
                    "name": "guest_rating",
                    "type": "FLOAT",
                    "description": "Guest rating out of 5, e.g. 4.6 from '4.6/5.0'.",
                },
                {"name": "total_rooms", "type": "INTEGER"},
                {"name": "email", "type": "STRING"},
                {"name": "phone", "type": "STRING"},
            ],
        },
        {
            "label": "Room",
            "description": "A room category offered by a hotel.",
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Room category, e.g. 'Standard Room', 'Suite'.",
                },
                {
                    "name": "bed_configuration",
                    "type": "STRING",
                    "description": "Bed layout, e.g. 'One king bed'.",
                },
                {"name": "max_occupancy", "type": "INTEGER"},
                {
                    "name": "min_rate",
                    "type": "FLOAT",
                    "description": "Lower bound of the nightly rate range.",
                },
                {
                    "name": "max_rate",
                    "type": "FLOAT",
                    "description": "Upper bound of the nightly rate range.",
                },
            ],
        },
        {
            "label": "Amenity",
            "description": (
                "A facility or feature the hotel offers, e.g. 'Swimming Pool', "
                "'Spa', 'Fitness Center', 'WiFi'. Only create one when the "
                "document says the hotel actually has it."
            ),
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "description", "type": "STRING"},
                {"name": "fee", "type": "STRING"},
            ],
        },
        {
            "label": "Policy",
            "description": "A hotel rule, e.g. cancellation or pet policy.",
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "description", "type": "STRING"},
            ],
        },
        {
            "label": "Service",
            "description": "A service the hotel provides, e.g. airport shuttle.",
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "description", "type": "STRING"},
                {"name": "cost", "type": "STRING"},
                {"name": "hours", "type": "STRING"},
                {"name": "is_available", "type": "BOOLEAN"},
                {"name": "is_complimentary", "type": "BOOLEAN"},
            ],
        },
    ],
    "relationship_types": [
        {"label": "HAS_ROOM"},
        {"label": "OFFERS_AMENITY"},
        {"label": "HAS_POLICY"},
        {"label": "PROVIDES_SERVICE"},
    ],
    "patterns": [
        ("Hotel", "HAS_ROOM", "Room"),
        ("Hotel", "OFFERS_AMENITY", "Amenity"),
        ("Hotel", "HAS_POLICY", "Policy"),
        ("Hotel", "PROVIDES_SERVICE", "Service"),
    ],
    # The whole point of pinning: refuse anything outside the contract.
    "additional_node_types": False,
    "additional_relationship_types": False,
    "additional_patterns": False,
}

SCHEMA_NODE_LABELS = ("Hotel", "Room", "Amenity", "Policy", "Service")

# Labels produced by earlier unpinned runs. Their presence after a build means
# the schema did not hold.
OFF_SCHEMA_LABELS = (
    "Address",
    "RoomType",
    "BedConfiguration",
    "Fee",
    "PaymentMethod",
    "ContactMethod",
    "ContactInfo",
    "Location",
    "City",
    "Country",
    "Attraction",
)

