# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Validate that merged Phase 1.5 evidence is complete and release-grade."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Any

from evaluator_contract import (
    EVALUATOR_GENERATION,
    EVIDENCE_HASH_ALGORITHM,
    FACTUALITY_LABELS,
    GROUNDING_LABELS,
    trial_judge_problems,
)

FAISS_MANIFEST_FIELDS = frozenset(
    {
        "embedding_model_id",
        "embedding_dimensions",
        "embedding_purpose",
        "document_count",
        "corpus_sha256",
        "vectors_sha256",
        "vector_source",
        "faiss_metric",
        "vector_normalization",
    }
)
EVALUATOR_SETTING_FIELDS = frozenset(
    {
        "top_k",
        "judge_samples",
        "judge_evidence_budget",
        "judge_evidence_hash",
        "graph_result_budget",
        "questions",
        "conditions",
        "vector_prompt",
        "graph_prompt",
        "grounding_suffix",
        "judge_system_prompt",
        "judge_response_fields",
        "factuality_labels",
        "grounding_labels",
    }
)


def positive_integer(value: Any) -> int | None:
    """Return a positive integer, excluding Booleans, or ``None``."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def run_header_problems(run: dict[str, Any]) -> list[str]:
    """Validate pinned evaluator and FAISS header consistency."""
    problems: list[str] = []
    if run.get("evaluator_generation") != EVALUATOR_GENERATION:
        problems.append(
            "evaluator_generation: "
            f"found {run.get('evaluator_generation')!r}, "
            f"expected {EVALUATOR_GENERATION}"
        )

    settings = run.get("evaluator_settings")
    if not isinstance(settings, dict):
        problems.append("evaluator_settings must be an object")
    else:
        if set(settings) != EVALUATOR_SETTING_FIELDS:
            problems.append(
                "evaluator_settings fields differ from the strict contract; "
                f"missing={sorted(EVALUATOR_SETTING_FIELDS - set(settings))}, "
                f"extra={sorted(set(settings) - EVALUATOR_SETTING_FIELDS)}"
            )
        shared_settings = {
            "top_k": run.get("top_k"),
            "judge_samples": run.get("judge_samples"),
            "judge_evidence_budget": run.get("judge_evidence_budget"),
        }
        for field, top_level_value in shared_settings.items():
            if settings.get(field) != top_level_value:
                problems.append(
                    f"evaluator setting {field} differs from the run header"
                )
        if settings.get("judge_evidence_hash") != EVIDENCE_HASH_ALGORITHM:
            problems.append(
                "evaluator setting judge_evidence_hash must be "
                f"{EVIDENCE_HASH_ALGORITHM!r}"
            )

    manifest = run.get("faiss_manifest")
    if not isinstance(manifest, dict):
        problems.append("faiss_manifest must be an object")
    else:
        if set(manifest) != FAISS_MANIFEST_FIELDS:
            problems.append(
                "faiss_manifest fields differ from the compatibility contract; "
                f"missing={sorted(FAISS_MANIFEST_FIELDS - set(manifest))}, "
                f"extra={sorted(set(manifest) - FAISS_MANIFEST_FIELDS)}"
            )
        manifest_matches = {
            "embedding_model_id": run.get("embedding_model_id"),
            "embedding_dimensions": run.get("index_dimensions"),
            "document_count": run.get("index_vectors"),
            "corpus_sha256": run.get("corpus_sha256_now"),
        }
        for field, observed in manifest_matches.items():
            if manifest.get(field) != observed:
                problems.append(f"FAISS manifest {field} differs from loaded evidence")
    return problems


def evidence_problems(
    run: dict[str, Any],
    *,
    questions: list[str],
    arms: list[str],
    conditions: list[str],
    trials_per_cell: int,
) -> list[str]:
    """Return every topology, evidence-integrity, and judge-result problem."""
    trials = run.get("trials")
    if not isinstance(trials, list):
        return ["trials must be a list"]

    problems = run_header_problems(run)
    expected_cells = set(product(questions, arms, conditions))
    expected_trials = len(expected_cells) * trials_per_cell
    if run.get("arms") != arms:
        problems.append(f"arms header: found {run.get('arms')!r}, expected {arms!r}")
    if run.get("conditions") != conditions:
        problems.append(
            f"conditions header: found {run.get('conditions')!r}, "
            f"expected {conditions!r}"
        )
    if run.get("trials_per_cell") != trials_per_cell:
        problems.append(
            "header trials_per_cell: "
            f"found {run.get('trials_per_cell')!r}, expected {trials_per_cell}"
        )
    if len(trials) != expected_trials:
        problems.append(f"trial count: found {len(trials)}, expected {expected_trials}")

    cells: dict[tuple[str, str, str], list[int]] = {}
    for position, trial in enumerate(trials, start=1):
        if not isinstance(trial, dict):
            problems.append(f"trial {position} must be an object")
            continue
        try:
            cell = (
                str(trial["question_key"]),
                str(trial["arm"]),
                str(trial["condition"]),
            )
            trial_number = positive_integer(trial["trial"])
            if trial_number is None:
                raise ValueError("trial number must be a positive integer")
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(
                f"trial {position} has an invalid cell or trial number: {exc}"
            )
            continue
        cells.setdefault(cell, []).append(trial_number)

    actual_cells = set(cells)
    for cell in sorted(expected_cells - actual_cells):
        problems.append(f"missing cell: {cell}")
    for cell in sorted(actual_cells - expected_cells):
        problems.append(f"unexpected cell: {cell}")

    expected_numbers = list(range(1, trials_per_cell + 1))
    for cell in sorted(expected_cells & actual_cells):
        numbers = sorted(cells[cell])
        if numbers != expected_numbers:
            problems.append(
                f"cell {cell} trial numbers: found {numbers}, expected {expected_numbers}"
            )

    tool_errors = [
        position
        for position, trial in enumerate(trials, start=1)
        if isinstance(trial, dict) and trial.get("tool_error") is not None
    ]
    if tool_errors:
        problems.append(f"tool errors in trial positions: {tool_errors}")

    judge_errors = [
        position
        for position, trial in enumerate(trials, start=1)
        if isinstance(trial, dict) and trial.get("judge_error") is not None
    ]
    if judge_errors:
        problems.append(f"judge errors in trial positions: {judge_errors}")

    invalid_labels = []
    for position, trial in enumerate(trials, start=1):
        if not isinstance(trial, dict):
            continue
        if (
            trial.get("factuality") not in FACTUALITY_LABELS
            or trial.get("grounding") not in GROUNDING_LABELS
        ):
            invalid_labels.append(position)
    if invalid_labels:
        problems.append(f"invalid judge labels in trial positions: {invalid_labels}")

    sample_count = positive_integer(run.get("judge_samples"))
    if sample_count is None:
        problems.append(
            "judge_samples header must be a positive integer, found "
            f"{run.get('judge_samples')!r}"
        )
    evidence_budget = positive_integer(run.get("judge_evidence_budget"))
    if evidence_budget is None:
        problems.append(
            "judge_evidence_budget header must be a positive integer, found "
            f"{run.get('judge_evidence_budget')!r}"
        )

    for position, trial in enumerate(trials, start=1):
        if not isinstance(trial, dict):
            continue
        for problem in trial_judge_problems(
            trial,
            expected_sample_count=sample_count,
            evidence_budget=evidence_budget,
        ):
            problems.append(f"trial {position} judge contract: {problem}")
    return problems


def build_parser() -> argparse.ArgumentParser:
    """Build the evidence-gate CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--trials-per-cell", type=int, required=True)
    parser.add_argument("--questions", nargs="+", required=True)
    parser.add_argument("--arms", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="+", required=True)
    return parser


def main() -> int:
    """Validate an evidence file and print a compact cell summary."""
    args = build_parser().parse_args()
    if args.trials_per_cell <= 0:
        raise SystemExit("--trials-per-cell must be greater than zero")
    run = json.loads(args.evidence.read_text(encoding="utf-8"))
    problems = evidence_problems(
        run,
        questions=args.questions,
        arms=args.arms,
        conditions=args.conditions,
        trials_per_cell=args.trials_per_cell,
    )
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1

    cell_sizes = Counter(
        (trial["question_key"], trial["arm"], trial["condition"])
        for trial in run["trials"]
    )
    print(
        f"Evidence passed: {len(run['trials'])} trials in {len(cell_sizes)} cells; "
        f"{args.trials_per_cell} trials per cell; strict judge evidence verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
