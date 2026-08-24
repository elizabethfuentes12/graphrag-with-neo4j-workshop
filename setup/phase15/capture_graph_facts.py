# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Capture deterministic Phase 1.5 source and graph facts as JSON.

Usage:

    cd notebooks
    uv run python ../setup/phase15/capture_graph_facts.py \
        --out ../evidence/live/phase15/graph-facts.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

PHASE15_DIR = Path(__file__).resolve().parent
SETUP_DIR = PHASE15_DIR.parent
REPO_ROOT = SETUP_DIR.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
MODULE_DIR = NOTEBOOKS_DIR / "02-connected-context"
for entry in (str(NOTEBOOKS_DIR), str(PHASE15_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from reference_facts import graph_facts, source_facts
from workshop.graph_connection import (
    graph_database,
    neo4j_auth,
    neo4j_uri,
    require_neo4j_env,
)

DOCUMENTS_PATH = MODULE_DIR / "faqs_docs.json"


def build_parser() -> argparse.ArgumentParser:
    """Build the graph-fact capture CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="JSON output file. Its parent directory is created.",
    )
    return parser


def main() -> int:
    """Capture corpus facts and read-only graph facts in one record."""
    args = build_parser().parse_args()
    output_path = args.out.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise SystemExit(f"{output_path} already exists; choose a new --out")

    load_dotenv(REPO_ROOT / ".env")
    require_neo4j_env()
    documents = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))
    database = graph_database()
    with (
        GraphDatabase.driver(neo4j_uri(), auth=neo4j_auth()) as driver,
        driver.session(database=database, default_access_mode="READ") as session,
    ):
        graph = graph_facts(session)

    evidence = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "neo4j_uri": neo4j_uri(),
        "neo4j_database": database,
        "source_facts": source_facts(documents),
        "graph_facts": graph,
    }
    output_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote Phase 1.5 graph facts to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
