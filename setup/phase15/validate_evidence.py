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


def evidence_problems(
    run: dict[str, Any],
    *,
    questions: list[str],
    arms: list[str],
    conditions: list[str],
    trials_per_cell: int,
) -> list[str]:
    """Return every completeness or trial-quality problem in one run."""
    trials = run.get("trials")
    if not isinstance(trials, list):
        return ["trials must be a list"]

    expected_cells = set(product(questions, arms, conditions))
    expected_trials = len(expected_cells) * trials_per_cell
    problems = []
    if run.get("trials_per_cell") != trials_per_cell:
        problems.append(
            "header trials_per_cell: "
            f"found {run.get('trials_per_cell')!r}, expected {trials_per_cell}"
        )
    if len(trials) != expected_trials:
        problems.append(f"trial count: found {len(trials)}, expected {expected_trials}")

    cells: dict[tuple[str, str, str], list[int]] = {}
    for position, trial in enumerate(trials, start=1):
        try:
            cell = (
                str(trial["question_key"]),
                str(trial["arm"]),
                str(trial["condition"]),
            )
            trial_number = int(trial["trial"])
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
        if trial.get("tool_error") is not None
    ]
    if tool_errors:
        problems.append(f"tool errors in trial positions: {tool_errors}")

    unscored = [
        position
        for position, trial in enumerate(trials, start=1)
        if trial.get("factuality") == "unscored" or trial.get("grounding") == "unscored"
    ]
    if unscored:
        problems.append(f"unscored trial positions: {unscored}")

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
        f"{args.trials_per_cell} trials per cell; no tool errors; all scored"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
