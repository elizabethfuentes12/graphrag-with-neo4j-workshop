# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Build and validate Module 2's standalone FAISS artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from workshop.retrieval_contract import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PURPOSE,
)

FAISS_METRIC = "inner_product"
VECTOR_NORMALIZATION = "l2"
VECTOR_SOURCE = "neo4j-aura:Document<-[:FROM_DOCUMENT]-Chunk.embedding"


class FaissArtifactError(ValueError):
    """Raised when the committed FAISS baseline is internally inconsistent."""


@dataclass(frozen=True)
class FaissManifest:
    """Compatibility contract stored beside the Module 2 FAISS index."""

    embedding_model_id: str
    embedding_dimensions: int
    embedding_purpose: str
    document_count: int
    corpus_sha256: str
    vectors_sha256: str
    vector_source: str
    faiss_metric: str
    vector_normalization: str

    @classmethod
    def from_path(cls, path: Path) -> FaissManifest:
        """Read a manifest and reject missing, extra, or invalid fields."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FaissArtifactError(f"Cannot read FAISS manifest {path}: {exc}") from exc

        if not isinstance(payload, dict):
            raise FaissArtifactError(f"FAISS manifest {path} must be a JSON object")

        expected = set(cls.__dataclass_fields__)
        actual = set(payload)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise FaissArtifactError(
                f"FAISS manifest {path} has wrong fields; "
                f"missing={missing}, extra={extra}"
            )

        string_fields = (
            "embedding_model_id",
            "embedding_purpose",
            "corpus_sha256",
            "vectors_sha256",
            "vector_source",
            "faiss_metric",
            "vector_normalization",
        )
        for field in string_fields:
            if not isinstance(payload[field], str) or not payload[field]:
                raise FaissArtifactError(
                    f"FAISS manifest field {field} must be a non-empty string"
                )
        for field in ("embedding_dimensions", "document_count"):
            value = payload[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise FaissArtifactError(
                    f"FAISS manifest field {field} must be a positive integer"
                )
        for field in ("corpus_sha256", "vectors_sha256"):
            checksum = payload[field]
            if len(checksum) != 64 or any(
                character not in "0123456789abcdef" for character in checksum
            ):
                raise FaissArtifactError(
                    f"FAISS manifest field {field} must be a lowercase SHA-256 digest"
                )
        return cls(**payload)

    def as_dict(self) -> dict[str, str | int]:
        """Return the stable JSON representation written by the rebuild script."""
        return {
            "embedding_model_id": self.embedding_model_id,
            "embedding_dimensions": self.embedding_dimensions,
            "embedding_purpose": self.embedding_purpose,
            "document_count": self.document_count,
            "corpus_sha256": self.corpus_sha256,
            "vectors_sha256": self.vectors_sha256,
            "vector_source": self.vector_source,
            "faiss_metric": self.faiss_metric,
            "vector_normalization": self.vector_normalization,
        }


def corpus_sha256(path: Path) -> str:
    """Return SHA-256 over the exact corpus bytes committed to the repository."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FaissArtifactError(f"Cannot read FAISS corpus {path}: {exc}") from exc


def vectors_sha256(index: Any) -> str:
    """Hash normalized float32 FAISS rows in deterministic corpus order.

    Little-endian float32 is the canonical byte representation, so the digest
    is stable across hosts with different native byte order.
    """
    vectors = np.asarray(
        index.reconstruct_n(0, index.ntotal), dtype=np.float32, order="C"
    ).copy()
    faiss.normalize_L2(vectors)
    canonical = vectors.astype("<f4", copy=False)
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def read_documents(path: Path) -> list[dict[str, Any]]:
    """Read the ordered FAQ document list used to map FAISS rows to text."""
    try:
        documents = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FaissArtifactError(f"Cannot read FAISS corpus {path}: {exc}") from exc

    if not isinstance(documents, list) or not documents:
        raise FaissArtifactError(f"FAISS corpus {path} must be a non-empty JSON array")
    for position, document in enumerate(documents):
        if not isinstance(document, dict):
            raise FaissArtifactError(
                f"FAISS corpus document {position} must be a JSON object"
            )
        for field in ("filename", "text"):
            if not isinstance(document.get(field), str) or not document[field]:
                raise FaissArtifactError(
                    f"FAISS corpus document {position} needs non-empty {field}"
                )
    return documents


def validate_faiss_artifacts(
    index: Any,
    documents: list[dict[str, Any]],
    manifest: FaissManifest,
    corpus_path: Path,
) -> None:
    """Validate the index, ordered corpus, manifest, and shared contract."""
    contract_values = {
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "embedding_purpose": EMBEDDING_PURPOSE,
        "vector_source": VECTOR_SOURCE,
        "faiss_metric": FAISS_METRIC,
        "vector_normalization": VECTOR_NORMALIZATION,
    }
    for field, expected in contract_values.items():
        actual = getattr(manifest, field)
        if actual != expected:
            raise FaissArtifactError(
                f"FAISS manifest {field} is {actual!r}; shared contract requires "
                f"{expected!r}. Rebuild the committed Module 2 artifacts."
            )

    if index.d != manifest.embedding_dimensions:
        raise FaissArtifactError(
            f"FAISS index has {index.d} dimensions; manifest requires "
            f"{manifest.embedding_dimensions}"
        )
    if index.metric_type != faiss.METRIC_INNER_PRODUCT:
        raise FaissArtifactError(
            "FAISS index must use inner product over L2-normalized vectors "
            "to match the Aura cosine index"
        )
    if index.ntotal != manifest.document_count:
        raise FaissArtifactError(
            f"FAISS index has {index.ntotal} rows; manifest requires "
            f"{manifest.document_count}"
        )
    if len(documents) != manifest.document_count:
        raise FaissArtifactError(
            f"FAISS corpus has {len(documents)} documents; manifest requires "
            f"{manifest.document_count}"
        )

    checksum = corpus_sha256(corpus_path)
    if checksum != manifest.corpus_sha256:
        raise FaissArtifactError(
            f"FAISS corpus checksum is {checksum}; manifest requires "
            f"{manifest.corpus_sha256}"
        )

    stored_vectors = index.reconstruct_n(0, index.ntotal)
    norms = np.linalg.norm(stored_vectors, axis=1)
    if not np.allclose(norms, 1.0, rtol=1e-5, atol=1e-6):
        bad_row = int(np.flatnonzero(~np.isclose(norms, 1.0, rtol=1e-5, atol=1e-6))[0])
        raise FaissArtifactError(
            f"FAISS row {bad_row} has L2 norm {norms[bad_row]:.8f}; expected 1.0"
        )

    vector_checksum = vectors_sha256(index)
    if vector_checksum != manifest.vectors_sha256:
        raise FaissArtifactError(
            f"FAISS vector checksum is {vector_checksum}; manifest requires "
            f"{manifest.vectors_sha256}"
        )


def prepare_faiss_query(vector: list[float] | np.ndarray) -> np.ndarray:
    """Return one unit-length float32 query compatible with the FAISS baseline."""
    query = np.asarray(vector, dtype=np.float32)
    if query.shape != (EMBEDDING_DIMENSIONS,):
        raise FaissArtifactError(
            f"FAISS query has shape {query.shape}; expected ({EMBEDDING_DIMENSIONS},)"
        )
    if not np.isfinite(query).all():
        raise FaissArtifactError("FAISS query contains a non-finite value")
    norm = float(np.linalg.norm(query))
    if norm == 0.0:
        raise FaissArtifactError("FAISS query cannot be a zero vector")
    return np.ascontiguousarray((query / norm).reshape(1, -1), dtype=np.float32)


def load_faiss_artifacts(
    index_path: Path,
    corpus_path: Path,
    manifest_path: Path,
) -> tuple[Any, list[dict[str, Any]]]:
    """Load Module 2's baseline only after validating every compatibility edge."""
    manifest = FaissManifest.from_path(manifest_path)
    documents = read_documents(corpus_path)
    try:
        index = faiss.read_index(str(index_path))
    except RuntimeError as exc:
        raise FaissArtifactError(f"Cannot read FAISS index {index_path}: {exc}") from exc
    validate_faiss_artifacts(index, documents, manifest, corpus_path)
    return index, documents
