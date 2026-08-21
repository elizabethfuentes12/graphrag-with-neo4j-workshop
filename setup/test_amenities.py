# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for deterministic amenity parsing and materialization."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from workshop.amenities import (
    AMENITY_NAME_CONSTRAINT,
    AmenityMaterializationError,
    AmenitySectionError,
    ParsedAmenities,
    ensure_amenity_constraint,
    materialize_amenities,
    parse_amenity_section,
)

CORPUS_ARCHIVE = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "02-connected-context"
    / "hotel-faqs.zip"
)


def _read_corpus() -> dict[str, str]:
    with ZipFile(CORPUS_ARCHIVE) as corpus:
        return {
            name: corpus.read(name).decode("utf-8")
            for name in corpus.namelist()
            if name.endswith(".txt")
        }


def _driver_for(transaction: Mock) -> tuple[Mock, Mock]:
    neo4j_session = Mock()
    neo4j_session.__enter__ = Mock(return_value=neo4j_session)
    neo4j_session.__exit__ = Mock(return_value=False)
    neo4j_session.execute_write.side_effect = lambda work: work(transaction)
    driver = Mock()
    driver.session.return_value = neo4j_session
    return driver, neo4j_session


def _result(record: dict[str, object]) -> Mock:
    result = Mock()
    result.single.return_value = record
    return result


def test_complete_corpus_matches_authoritative_amenity_inventory() -> None:
    documents = _read_corpus()

    parsed = [
        parse_amenity_section(text, filename) for filename, text in documents.items()
    ]

    assert len(parsed) == 300
    assert sum(len(document.names) for document in parsed) == 1_632
    assert len({name for document in parsed for name in document.names}) == 65


def test_chicago_wifi_is_exact_and_pool_negation_is_not_parsed() -> None:
    documents = _read_corpus()

    chicago = [
        parse_amenity_section(documents[filename], filename)
        for filename in ("hotel-chicago-001.txt", "hotel-chicago-002.txt")
    ]

    assert all("Complimentary High-Speed Wifi" in item.names for item in chicago)
    assert "Outdoor Swimming Pool" not in chicago[0].names
    assert all(
        "Pool facilities are not available" not in item.names for item in chicago
    )


def test_parser_is_deterministic_and_preserves_authored_order() -> None:
    text = """# Hotel

## Hotel Amenities

- First Authored Label\t
- Second Authored Label

### Details
- Not part of the authoritative list
"""

    first = parse_amenity_section(text, "hotel.txt")
    second = parse_amenity_section(text, "hotel.txt")

    assert first == second
    assert first.names == ("First Authored Label", "Second Authored Label")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("# Hotel\n", "found 0"),
        (
            "## Hotel Amenities\n- WiFi\n## Hotel Amenities\n- Pool\n",
            "found 2",
        ),
        ("## Hotel Amenities\n\n### Details\n", "has no amenity bullets"),
        ("## Hotel Amenities\n-Not a direct bullet\n", "expected a direct"),
        ("## Hotel Amenities\nAmenities include WiFi\n", "expected a direct"),
        ("## Hotel Amenities\n- WiFi\n- WiFi\n", "duplicate amenity"),
    ],
)
def test_malformed_sections_fail_with_filename(text: str, message: str) -> None:
    with pytest.raises(AmenitySectionError, match=message) as error:
        parse_amenity_section(text, "broken-hotel.txt")

    assert "broken-hotel.txt" in str(error.value)


def test_constraint_is_idempotent_and_uses_configured_database() -> None:
    consume = Mock()
    neo4j_session = Mock()
    neo4j_session.__enter__ = Mock(return_value=neo4j_session)
    neo4j_session.__exit__ = Mock(return_value=False)
    neo4j_session.run.return_value.consume = consume
    driver = Mock()
    driver.session.return_value = neo4j_session

    ensure_amenity_constraint(driver, "workshop")

    driver.session.assert_called_once_with(database="workshop")
    neo4j_session.run.assert_called_once_with(AMENITY_NAME_CONSTRAINT)
    assert "IF NOT EXISTS" in AMENITY_NAME_CONSTRAINT
    consume.assert_called_once_with()


def test_materializer_uses_provenance_and_parameterized_merges() -> None:
    transaction = Mock()
    transaction.run.side_effect = [
        _result(
            {
                "document_count": 1,
                "hotel_count": 1,
                "hotel_element_ids": ["hotel-element-id"],
            }
        ),
        _result({"amenity_count": 2}),
    ]
    driver, neo4j_session = _driver_for(transaction)
    parsed = ParsedAmenities("hotel.txt", ("WiFi", "Pool"))

    count = materialize_amenities(driver, "workshop", parsed)

    assert count == 2
    driver.session.assert_called_once_with(database="workshop")
    neo4j_session.execute_write.assert_called_once()
    lookup_call, write_call = transaction.run.call_args_list
    lookup_query = lookup_call.args[0]
    write_query = write_call.args[0]
    assert "Document {source_filename: $source_filename}" in lookup_query
    assert "[:FROM_DOCUMENT]" in lookup_query
    assert "[:FROM_CHUNK]" in lookup_query
    assert "UNWIND $amenity_names" in write_query
    assert "MERGE (amenity:Amenity {name: amenity_name})" in write_query
    assert "MERGE (hotel)-[offer:OFFERS_AMENITY]->(amenity)" in write_query
    assert "SET offer.source_filename = $source_filename" in write_query
    assert "MERGE (amenity)-[:FROM_CHUNK]->(chunk)" in write_query
    assert "description" not in write_query
    assert "fee" not in write_query
    assert write_call.kwargs == {
        "source_filename": "hotel.txt",
        "hotel_element_id": "hotel-element-id",
        "amenity_names": ["WiFi", "Pool"],
    }


@pytest.mark.parametrize(
    ("document_count", "hotel_count", "message"),
    [
        (0, 0, "found 0 Document nodes"),
        (2, 1, "found 2 Document nodes"),
        (1, 0, "found 0 Hotels"),
        (1, 2, "found 2 Hotels"),
    ],
)
def test_materializer_rejects_ambiguous_provenance_before_writing(
    document_count: int,
    hotel_count: int,
    message: str,
) -> None:
    transaction = Mock()
    transaction.run.return_value = _result(
        {
            "document_count": document_count,
            "hotel_count": hotel_count,
            "hotel_element_ids": ["hotel-element-id"] * hotel_count,
        }
    )
    driver, _ = _driver_for(transaction)

    with pytest.raises(AmenityMaterializationError, match=message):
        materialize_amenities(
            driver,
            "workshop",
            ParsedAmenities("hotel.txt", ("WiFi",)),
        )

    transaction.run.assert_called_once()


def test_repeated_materialization_uses_only_idempotent_graph_writes() -> None:
    transaction = Mock()
    transaction.run.side_effect = [
        _result(
            {
                "document_count": 1,
                "hotel_count": 1,
                "hotel_element_ids": ["hotel-element-id"],
            }
        ),
        _result({"amenity_count": 1}),
        _result(
            {
                "document_count": 1,
                "hotel_count": 1,
                "hotel_element_ids": ["hotel-element-id"],
            }
        ),
        _result({"amenity_count": 1}),
    ]
    driver, _ = _driver_for(transaction)
    parsed = ParsedAmenities("hotel.txt", ("WiFi",))

    materialize_amenities(driver, "workshop", parsed)
    materialize_amenities(driver, "workshop", parsed)

    write_queries = [call.args[0] for call in transaction.run.call_args_list[1::2]]
    assert len(write_queries) == 2
    assert write_queries[0] == write_queries[1]
    assert "CREATE (" not in write_queries[0]
    assert write_queries[0].count("MERGE (") == 3
