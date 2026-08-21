#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Rebuild Module 2's standalone FAISS baseline from Aura chunk vectors.

This is a facilitator task. Workshop participants use the committed artifacts.
The script reads vectors already created by Module 1, so it makes no Bedrock
calls and keeps FAISS on the same embedding contract as Aura.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

MODULE_DIR = Path(__file__).resolve().parent
NOTEBOOKS_DIR = MODULE_DIR.parent
REPO_ROOT = NOTEBOOKS_DIR.parent
if str(NOTEBOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOKS_DIR))

from workshop.faiss_artifacts import (
    FAISS_METRIC,
    VECTOR_NORMALIZATION,
    VECTOR_SOURCE,
    FaissManifest,
    corpus_sha256,
    load_faiss_artifacts,
    read_documents,
    vectors_sha256,
)
from workshop.graph_connection import (
    graph_database,
    neo4j_auth,
    neo4j_uri,
    require_neo4j_env,
)
from workshop.retrieval_contract import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PURPOSE,
)

CHUNK_EMBEDDINGS_QUERY = """
CYPHER 25
UNWIND $filenames AS filename
OPTIONAL MATCH (document:Document {source_filename: filename})
OPTIONAL MATCH (document)<-[:FROM_DOCUMENT]-(chunk:Chunk)
RETURN filename,
       elementId(document) AS document_id,
       elementId(chunk) AS chunk_id,
       chunk.embedding AS embedding
""".strip()


def parse_args() -> argparse.Namespace:
    """Parse facilitator artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus", type=Path, default=MODULE_DIR / "faqs_docs.json"
    )
    parser.add_argument(
        "--index", type=Path, default=MODULE_DIR / "faqs_vector.index"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MODULE_DIR / "faqs_vector.manifest.json",
    )
    return parser.parse_args()


def fetch_chunk_embeddings(
    driver: Driver, filenames: list[str], database: str
) -> list[dict[str, object]]:
    """Read every candidate chunk through a Cypher 25 read transaction."""

    def read_records(transaction) -> list[dict[str, object]]:
        return [
            dict(record)
            for record in transaction.run(
                CHUNK_EMBEDDINGS_QUERY, filenames=filenames
            )
        ]

    with driver.session(database=database) as session:
        return session.execute_read(read_records)


def vectors_in_corpus_order(
    documents: list[dict[str, object]], records: list[dict[str, object]]
) -> np.ndarray:
    """Validate Aura rows and reorder them to match the committed JSON array."""
    filenames = [str(document["filename"]) for document in documents]
    if len(set(filenames)) != len(filenames):
        duplicates = sorted(
            {filename for filename in filenames if filenames.count(filename) > 1}
        )
        raise ValueError(f"FAISS corpus repeats filenames: {duplicates}")

    expected = set(filenames)
    grouped: dict[str, list[dict[str, object]]] = {
        filename: [] for filename in filenames
    }
    unexpected: list[str] = []
    for record in records:
        filename = str(record["filename"])
        if filename not in expected:
            unexpected.append(filename)
            continue
        if record.get("chunk_id") is not None:
            grouped[filename].append(record)
    if unexpected:
        raise ValueError(f"Aura returned unexpected source filenames: {unexpected}")

    vectors = np.empty((len(filenames), EMBEDDING_DIMENSIONS), dtype=np.float32)
    problems: list[str] = []
    for position, filename in enumerate(filenames):
        matches = grouped[filename]
        if not matches:
            problems.append(f"{filename}: no Chunk found")
            continue
        if len(matches) != 1:
            problems.append(f"{filename}: {len(matches)} Chunks found, expected 1")
            continue
        embedding = matches[0].get("embedding")
        if embedding is None:
            problems.append(f"{filename}: Chunk has no embedding")
            continue
        vector = np.asarray(embedding, dtype=np.float32)
        if vector.shape != (EMBEDDING_DIMENSIONS,):
            problems.append(
                f"{filename}: embedding has shape {vector.shape}, expected "
                f"({EMBEDDING_DIMENSIONS},)"
            )
            continue
        if not np.isfinite(vector).all():
            problems.append(f"{filename}: embedding contains a non-finite value")
            continue
        vectors[position] = vector
    if problems:
        raise ValueError("Cannot rebuild FAISS from Aura:\n  - " + "\n  - ".join(problems))

    faiss.normalize_L2(vectors)
    return vectors


def write_artifacts(
    index_path: Path,
    manifest_path: Path,
    corpus_path: Path,
    vectors: np.ndarray,
) -> None:
    """Write the normalized inner-product index and compatibility manifest."""
    index = faiss.IndexFlatIP(EMBEDDING_DIMENSIONS)
    index.add(vectors)
    faiss.write_index(index, str(index_path))

    manifest = FaissManifest(
        embedding_model_id=EMBEDDING_MODEL_ID,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
        embedding_purpose=EMBEDDING_PURPOSE,
        document_count=index.ntotal,
        corpus_sha256=corpus_sha256(corpus_path),
        vectors_sha256=vectors_sha256(index),
        vector_source=VECTOR_SOURCE,
        faiss_metric=FAISS_METRIC,
        vector_normalization=VECTOR_NORMALIZATION,
    )
    manifest_path.write_text(
        json.dumps(manifest.as_dict(), indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    """Rebuild and validate the committed Module 2 baseline."""
    args = parse_args()
    load_dotenv(REPO_ROOT / ".env")
    require_neo4j_env()
    documents = read_documents(args.corpus)
    filenames = [str(document["filename"]) for document in documents]

    print(f"Reading {len(documents)} existing chunk embeddings from Aura.")
    with GraphDatabase.driver(neo4j_uri(), auth=neo4j_auth()) as driver:
        records = fetch_chunk_embeddings(driver, filenames, graph_database())
    vectors = vectors_in_corpus_order(documents, records)
    write_artifacts(args.index, args.manifest, args.corpus, vectors)
    validated_index, validated_documents = load_faiss_artifacts(
        args.index, args.corpus, args.manifest
    )
    print(
        f"Validated {validated_index.ntotal} FAISS rows against "
        f"{len(validated_documents)} corpus documents and {args.manifest}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
