# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Merge the per-slice evidence files one run produced into a single record.

Run 2 is sliced by question so it can run six processes at once. Each slice
writes its own file with an identical header, so merging is a concatenation of
`trials` plus a check that the headers really do agree. A disagreement means the
slices did not measure the same thing and must not be pooled.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Fields that must be identical across slices for the merge to be meaningful.
# `run_utc` and `trials_per_cell` are expected to differ or repeat, so they are
# not checked here.
PINNED_FIELDS = (
    "model_id",
    "embedding_model_id",
    "region",
    "top_k",
    "judge_samples",
    "run_generation",
    "neo4j_uri",
    "neo4j_database",
    "corpus_sha256_now",
    "index_dimensions",
    "index_vectors",
)


def check_headers(runs: list[dict[str, Any]]) -> None:
    """Raise when the slices disagree on anything that would invalidate pooling."""
    first = runs[0]
    for field in PINNED_FIELDS:
        values = {json.dumps(run.get(field), sort_keys=True) for run in runs}
        if len(values) > 1:
            raise ValueError(f"slices disagree on {field}: {sorted(values)}")
    for field in ("source_facts", "graph_facts"):
        reference = json.dumps(first.get(field), sort_keys=True, default=str)
        for run in runs[1:]:
            if json.dumps(run.get(field), sort_keys=True, default=str) != reference:
                raise ValueError(f"slices disagree on {field}")


def main() -> int:
    """Merge every evidence file in a directory into one file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    paths = sorted(p for p in args.directory.glob("phase15-*.json") if "merged" not in p.name)
    if not paths:
        raise SystemExit(f"no slice files in {args.directory}")

    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    check_headers(runs)

    merged = dict(runs[0])
    merged["run_utc"] = min(run["run_utc"] for run in runs)
    merged["slice_files"] = [path.name for path in paths]
    merged["slice_count"] = len(paths)
    merged["conditions"] = sorted({c for run in runs for c in run.get("conditions", [])})
    merged["trials"] = [trial for run in runs for trial in run["trials"]]

    output = args.out or args.directory / "phase15-run2-merged.json"
    output.write_text(json.dumps(merged, indent=2, default=str) + "\n", encoding="utf-8")

    cells: dict[tuple[str, str, str], int] = {}
    for trial in merged["trials"]:
        key = (trial["question_key"], trial["arm"], trial.get("condition", "notebook"))
        cells[key] = cells.get(key, 0) + 1
    sizes = sorted(set(cells.values()))
    print(f"Wrote {output}: {len(merged['trials'])} trials in {len(cells)} cells")
    print(f"Cell sizes: {sizes}")
    if len(sizes) > 1:
        print("WARNING: cells are unbalanced, some slice did not finish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
