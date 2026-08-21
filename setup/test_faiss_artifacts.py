# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Focused tests for Module 2's committed FAISS compatibility contract."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pytest
from workshop.faiss_artifacts import (
    FAISS_METRIC,
    VECTOR_NORMALIZATION,
    VECTOR_SOURCE,
    FaissArtifactError,
    FaissManifest,
    corpus_sha256,
    load_faiss_artifacts,
    prepare_faiss_query,
    vectors_sha256,
)
from workshop.retrieval_contract import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PURPOSE,
)


def write_fixture(
    tmp_path: Path,
    *,
    dimensions: int = EMBEDDING_DIMENSIONS,
    index_count: int = 2,
    manifest_count: int = 2,
    manifest_checksum: str | None = None,
    manifest_vectors_checksum: str | None = None,
    model_id: str = EMBEDDING_MODEL_ID,
    vector_source: str = VECTOR_SOURCE,
) -> tuple[Path, Path, Path]:
    """Write a small but real FAISS artifact set for one validation test."""
    corpus_path = tmp_path / "faqs_docs.json"
    corpus_path.write_text(
        json.dumps(
            [
                {"filename": "one.txt", "text": "first"},
                {"filename": "two.txt", "text": "second"},
            ]
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "faqs_vector.index"
    index = faiss.IndexFlatIP(dimensions)
    vectors = np.zeros((index_count, dimensions), dtype=np.float32)
    vectors[:, 0] = 1.0
    index.add(vectors)
    faiss.write_index(index, str(index_path))

    manifest_path = tmp_path / "faqs_vector.manifest.json"
    manifest = FaissManifest(
        embedding_model_id=model_id,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
        embedding_purpose=EMBEDDING_PURPOSE,
        document_count=manifest_count,
        corpus_sha256=manifest_checksum or corpus_sha256(corpus_path),
        vectors_sha256=manifest_vectors_checksum or vectors_sha256(index),
        vector_source=vector_source,
        faiss_metric=FAISS_METRIC,
        vector_normalization=VECTOR_NORMALIZATION,
    )
    manifest_path.write_text(
        json.dumps(manifest.as_dict()), encoding="utf-8"
    )
    return index_path, corpus_path, manifest_path


def test_valid_artifacts_load_in_corpus_order(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path)

    index, documents = load_faiss_artifacts(*paths)

    assert index.d == EMBEDDING_DIMENSIONS
    assert index.ntotal == 2
    assert [document["filename"] for document in documents] == [
        "one.txt",
        "two.txt",
    ]


def test_contract_model_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path, model_id="wrong-model")

    with pytest.raises(FaissArtifactError, match="shared contract requires"):
        load_faiss_artifacts(*paths)


def test_index_dimension_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path, dimensions=384)

    with pytest.raises(FaissArtifactError, match="index has 384 dimensions"):
        load_faiss_artifacts(*paths)


def test_index_count_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path, index_count=1)

    with pytest.raises(FaissArtifactError, match="index has 1 rows"):
        load_faiss_artifacts(*paths)


def test_corpus_count_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path, manifest_count=3, index_count=3)

    with pytest.raises(FaissArtifactError, match="corpus has 2 documents"):
        load_faiss_artifacts(*paths)


def test_exact_corpus_byte_change_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path)
    paths[1].write_bytes(paths[1].read_bytes() + b"\n")

    with pytest.raises(FaissArtifactError, match="corpus checksum"):
        load_faiss_artifacts(*paths)


def test_wrong_graph_vector_source_is_rejected(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path, vector_source="bedrock-direct")

    with pytest.raises(FaissArtifactError, match="vector_source.+shared contract"):
        load_faiss_artifacts(*paths)


def test_same_shape_modified_vector_content_is_rejected(tmp_path: Path) -> None:
    index_path, corpus_path, manifest_path = write_fixture(tmp_path)
    index = faiss.read_index(str(index_path))
    vectors = index.reconstruct_n(0, index.ntotal)
    vectors[0] = 0.0
    vectors[0, 1] = 1.0
    modified = faiss.IndexFlatIP(EMBEDDING_DIMENSIONS)
    modified.add(vectors)
    faiss.write_index(modified, str(index_path))

    with pytest.raises(FaissArtifactError, match="vector checksum"):
        load_faiss_artifacts(index_path, corpus_path, manifest_path)


def test_query_is_normalized_for_inner_product_search() -> None:
    query = prepare_faiss_query([2.0] * EMBEDDING_DIMENSIONS)

    assert query.shape == (1, EMBEDDING_DIMENSIONS)
    assert query.dtype == np.float32
    assert np.linalg.norm(query[0]) == pytest.approx(1.0)


def test_wrong_faiss_metric_is_rejected(tmp_path: Path) -> None:
    index_path, corpus_path, manifest_path = write_fixture(tmp_path)
    index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
    vector = np.zeros((2, EMBEDDING_DIMENSIONS), dtype=np.float32)
    vector[:, 0] = 1.0
    index.add(vector)
    faiss.write_index(index, str(index_path))

    with pytest.raises(FaissArtifactError, match="must use inner product"):
        load_faiss_artifacts(index_path, corpus_path, manifest_path)
