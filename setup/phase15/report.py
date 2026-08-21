# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Turn a Phase 1.5 evidence file into the markdown report the gate needs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ARMS = ("vector", "graph")
CONDITIONS = ("notebook", "grounded")
QUESTION_ORDER = (
    "orlando_aggregation",
    "pool_counting",
    "chicago_criteria",
    "antarctica_no_match",
    "chicago_shared_amenities",
    "suite_and_spa",
)
QUESTION_TITLES = {
    "orlando_aggregation": "Orlando aggregation",
    "pool_counting": "Pool counting",
    "chicago_criteria": "Chicago multiple criteria",
    "antarctica_no_match": "Antarctica no match",
    "chicago_shared_amenities": "Chicago shared amenities (bounded traversal)",
    "suite_and_spa": "Suite under $600 with a spa (traversal at scale)",
}


def tally(trials: list[dict[str, Any]], field: str) -> str:
    """Render a label distribution as a compact `a x2, b x1` string."""
    counts = Counter(trial[field] for trial in trials)
    return ", ".join(f"{label} x{count}" for label, count in counts.most_common())


def orlando_coverage(trials: list[dict[str, Any]]) -> list[str]:
    """Report how many of the five Orlando documents each k=3 retrieval saw."""
    lines = []
    for trial in trials:
        seen: set[str] = set()
        hits = 0
        for retrieval in trial["retrieval"]:
            for filename in retrieval["filenames"]:
                hits += 1
                if "orlando" in filename:
                    seen.add(filename)
        lines.append(
            f"  trial {trial['trial']}: {hits} retrieved rows, "
            f"{len(seen)} of the 5 Orlando documents "
            f"({', '.join(sorted(seen)) or 'none'})"
        )
    return lines


def main() -> int:
    """Write the markdown evidence report beside the JSON it summarizes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    run = json.loads(args.evidence.read_text(encoding="utf-8"))
    trials = run["trials"]
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trial in trials:
        by_cell[
        (trial["question_key"], trial["arm"], trial.get("condition", "notebook"))
    ].append(trial)

    source = run["source_facts"]
    graph = run["graph_facts"]
    lines: list[str] = []
    add = lines.append

    add("# Phase 1.5 evidence report")
    add("")
    add(f"Run: {run['run_utc']}")
    add(f"Chat model: `{run['model_id']}`")
    add(f"Embedding model: `{run['embedding_model_id']}`")
    add(f"Region: {run['region']}")
    add(f"Neo4j: {run['neo4j_uri']} database `{run['neo4j_database']}`")
    add(
        f"FAISS: {run['index_vectors']} vectors at {run['index_dimensions']} "
        f"dimensions, metric `{run['faiss_manifest']['faiss_metric']}`, "
        f"normalization `{run['faiss_manifest']['vector_normalization']}`"
    )
    add(f"Corpus checksum: `{run['corpus_sha256_now']}`")
    batches = run.get("source_files", [])
    per_cell = len(trials) // (len(QUESTION_ORDER) * len(ARMS))
    add(f"Trials: {len(trials)} ({per_cell} per question per arm), k={run['top_k']}")
    if batches:
        add("")
        add(
            f"Collected in {len(batches)} independent processes, so no trial shares a "
            "client, a session, or an agent with any other: "
            + ", ".join(f"`{name}`" for name in batches)
        )
    add("")

    add("## Deterministic reference facts")
    add("")
    add("Source facts come from the committed corpus bytes. Graph facts come from Aura.")
    add("They are reported separately so an extraction gap stays visible.")
    add("")
    add("| Fact | Source corpus | Live graph |")
    add("| --- | --- | --- |")
    orl = source["orlando"]
    graph_orl = graph["orlando_mean"][0] if graph["orlando_mean"] else {}
    add(
        f"| Orlando hotels | {orl['count']} | "
        f"{graph_orl.get('rated_hotels', 'n/a')} rated |"
    )
    add(
        f"| Orlando mean guest rating | {orl['mean_guest_rating']} | "
        f"{graph_orl.get('mean_guest_rating', 'n/a')} |"
    )
    pool = source["pool"]
    graph_pool = graph["pool_hotels"][0]["hotels_with_pool"] if graph["pool_hotels"] else "n/a"
    add(
        f"| Hotels with a pool | {pool['listed_in_amenities']} listed, "
        f"{pool['explicitly_unavailable']} explicitly unavailable | {graph_pool} |"
    )
    chi = source["chicago"]
    add(
        f"| Chicago spa-and-pool matches | {chi['matches']} of {chi['candidates']} "
        f"candidates | {len(graph['chicago_spa_and_pool'])} |"
    )
    add(
        f"| Antarctica | {source['antarctica']['documents']} documents | "
        f"{graph['antarctica'][0]['hotels'] if graph['antarctica'] else 'n/a'} hotels |"
    )
    add(f"| Total hotels | {source['document_count']} documents | "
        f"{graph['total_hotels'][0]['hotels'] if graph['total_hotels'] else 'n/a'} |")
    add("")

    gap = pool["listed_in_amenities"] - (graph_pool if isinstance(graph_pool, int) else 0)
    if gap:
        add(
            f"The graph reports {graph_pool} hotels with a pool against "
            f"{pool['listed_in_amenities']} in the source. The extraction gap is "
            f"{gap}. The graph count is not the corpus ground truth."
        )
        add("")

    add("## Results by question, arm and prompt condition")
    add("")
    add("The `notebook` condition uses each arm's own system prompt verbatim. The")
    add("`grounded` condition appends the same grounding sentence to both arms.")
    add("")
    add(
        "| Question | Arm | Condition | Factuality | Grounding | Mean tokens "
        "| Mean tool calls |"
    )
    add("| --- | --- | --- | --- | --- | --- | --- |")
    for key in QUESTION_ORDER:
        for condition in CONDITIONS:
            for arm in ARMS:
                cell = by_cell.get((key, arm, condition))
                if not cell:
                    continue
                tokens = [
                    t["token_usage"]["totalTokens"]
                    for t in cell
                    if t.get("token_usage") and "totalTokens" in t["token_usage"]
                ]
                mean_tokens = round(sum(tokens) / len(tokens)) if tokens else "n/a"
                mean_calls = round(sum(t["tool_calls"] for t in cell) / len(cell), 1)
                add(
                    f"| {QUESTION_TITLES[key]} | {arm} | {condition} | "
                    f"{tally(cell, 'factuality')} | "
                    f"{tally(cell, 'grounding')} | {mean_tokens} | {mean_calls} |"
                )
    add("")

    errors = [t for t in trials if t["tool_error"]]
    add(f"Trials that raised instead of returning a swallowed error string: {len(errors)}.")
    add("")

    add("## Orlando top-k coverage")
    add("")
    add("```")
    orlando_vector = [
        t for t in trials
        if t["question_key"] == "orlando_aggregation" and t["arm"] == "vector"
    ]
    for line in orlando_coverage(orlando_vector):
        add(line)
    add("```")
    add("")

    add("## Per-trial detail")
    add("")
    for key in QUESTION_ORDER:
        add(f"### {QUESTION_TITLES[key]}")
        add("")
        for condition in CONDITIONS:
            for arm in ARMS:
              for trial in by_cell.get((key, arm, condition), []):
                  add(f"**{arm} / {condition} trial {trial['trial']}** "
                      f"({trial['factuality']} / {trial['grounding']}, "
                      f"{trial['tool_calls']} tool calls, {trial['elapsed_seconds']}s)")
                  add("")
                  if arm == "vector":
                      for retrieval in trial["retrieval"]:
                          pairs = ", ".join(
                              f"{name} {score:.3f}"
                              for name, score in zip(retrieval["filenames"], retrieval["scores"])
                          )
                          add(f"- retrieved: {pairs}")
                  else:
                      for call in trial["retrieval"]:
                          first = call["cypher"].replace("\n", " ").strip()
                          outcome = call["error"] or f"{len(call['records'])} rows"
                          add(f"- cypher: `{first[:180]}` -> {outcome}")
                  add("")
                  add(f"- judge: {trial['rationale']}")
                  add("")
                  add("<details><summary>answer</summary>")
                  add("")
                  add("```")
                  add(trial["answer"][:2500])
                  add("```")
                  add("")
                  add("</details>")
                  add("")

    output = args.out or args.evidence.with_suffix(".md")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
