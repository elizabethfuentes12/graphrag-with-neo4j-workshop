# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Test Aura export and row validation for the facilitator FAISS rebuild."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from workshop.retrieval_contract import EMBEDDING_DIMENSIONS

REBUILD_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "02-connected-context"
    / "rebuild_faiss_index.py"
)
SPEC = importlib.util.spec_from_file_location("rebuild_faiss_index", REBUILD_PATH)
assert SPEC and SPEC.loader
rebuild = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rebuild)


def documents(*filenames: str) -> list[dict[str, object]]:
    return [{"filename": filename, "text": filename} for filename in filenames]


def record(filename: str, coordinate: int = 0) -> dict[str, object]:
    embedding = [0.0] * EMBEDDING_DIMENSIONS
    embedding[coordinate] = 1.0
    return {
        "filename": filename,
        "document_id": f"document-{filename}",
        "chunk_id": f"chunk-{filename}",
        "embedding": embedding,
    }


def test_export_uses_configured_database_and_read_transaction() -> None:
    raw_record = record("one.txt")
    transaction = Mock()
    transaction.run.return_value = [raw_record]
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.execute_read.side_effect = lambda work: work(transaction)
    driver = Mock()
    driver.session.return_value = session

    result = rebuild.fetch_chunk_embeddings(driver, ["one.txt"], "workshop")

    assert result == [raw_record]
    driver.session.assert_called_once_with(database="workshop")
    session.execute_read.assert_called_once()
    query, = transaction.run.call_args.args
    assert query.startswith("CYPHER 25")
    assert transaction.run.call_args.kwargs == {"filenames": ["one.txt"]}


def test_vectors_are_reordered_to_exact_corpus_order() -> None:
    vectors = rebuild.vectors_in_corpus_order(
        documents("one.txt", "two.txt"),
        [record("two.txt", 1), record("one.txt", 0)],
    )

    assert vectors.shape == (2, EMBEDDING_DIMENSIONS)
    assert np.linalg.norm(vectors[0]) == pytest.approx(1.0)
    assert vectors[0, 0] == pytest.approx(1.0)
    assert vectors[1, 1] == pytest.approx(1.0)


def test_missing_chunk_is_rejected() -> None:
    missing = {
        "filename": "two.txt",
        "document_id": None,
        "chunk_id": None,
        "embedding": None,
    }

    with pytest.raises(ValueError, match="two.txt: no Chunk found"):
        rebuild.vectors_in_corpus_order(
            documents("one.txt", "two.txt"), [record("one.txt"), missing]
        )


def test_duplicate_chunks_are_rejected() -> None:
    with pytest.raises(ValueError, match="2 Chunks found, expected 1"):
        rebuild.vectors_in_corpus_order(
            documents("one.txt"), [record("one.txt"), record("one.txt")]
        )


def test_wrong_embedding_width_is_rejected() -> None:
    wrong = record("one.txt") | {"embedding": [1.0] * 384}

    with pytest.raises(ValueError, match=r"shape \(384,\).+\(1024,\)"):
        rebuild.vectors_in_corpus_order(documents("one.txt"), [wrong])
