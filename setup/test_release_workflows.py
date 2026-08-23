# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Offline tests for the reusable additive and live-evidence operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest
import run_additive_validation
import run_live_evidence
import run_notebook_smoke


def test_additive_contract_requires_exact_before_after_and_delta() -> None:
    before = dict(run_additive_validation.PREBUILT_COUNTS)
    after = dict(run_additive_validation.FULL_COUNTS)

    assert (
        run_additive_validation.comparison_problems(
            before, run_additive_validation.PREBUILT_COUNTS, "before"
        )
        == []
    )
    delta = run_additive_validation.count_delta(before, after)
    assert delta == run_additive_validation.HELD_OUT_DELTA


def test_additive_contract_reports_each_mismatch() -> None:
    actual = dict(run_additive_validation.FULL_COUNTS)
    actual["documents"] = 299
    actual["amenity_assertions"] = 1631

    problems = run_additive_validation.comparison_problems(
        actual, run_additive_validation.FULL_COUNTS, "after"
    )

    assert problems == [
        "after documents: found 299, expected 300",
        "after amenity_assertions: found 1631, expected 1632",
    ]


def live_args(tmp_path: Path, *extra: str) -> argparse.Namespace:
    """Parse a representative live-evidence invocation."""
    return run_live_evidence.build_parser().parse_args(
        ["--output-dir", str(tmp_path), *extra]
    )


def test_live_commands_send_every_output_to_requested_directory(
    tmp_path: Path,
) -> None:
    args = live_args(tmp_path)

    commands = dict(run_live_evidence.stage_commands(args, tmp_path))

    assert commands["graph_facts"][-1] == str(tmp_path / "phase15/graph-facts.json")
    assert str(tmp_path / "phase15/trials") in commands["agent_evidence"]
    assert str(tmp_path / "notebooks") in commands["notebook_smoke"]
    assert commands["agent_evidence"][0] == sys.executable


def test_live_commands_preserve_explicit_harness_options(tmp_path: Path) -> None:
    args = live_args(
        tmp_path,
        "--trials",
        "2",
        "--questions",
        "pool_counting",
        "chicago_criteria",
        "--arms",
        "graph",
        "--conditions",
        "grounded",
        "--skip-judge",
        "--notebook-modules",
        "2,3",
        "--notebook-timeout",
        "900",
    )

    commands = dict(run_live_evidence.stage_commands(args, tmp_path))

    assert commands["agent_evidence"] == [
        sys.executable,
        str(run_live_evidence.HARNESS),
        "--trials",
        "2",
        "--out",
        str(tmp_path / "phase15/trials"),
        "--questions",
        "pool_counting",
        "chicago_criteria",
        "--arms",
        "graph",
        "--conditions",
        "grounded",
        "--skip-judge",
    ]
    assert "2,3" in commands["notebook_smoke"]
    assert "900" in commands["notebook_smoke"]


def test_live_stages_can_be_selected_independently(tmp_path: Path) -> None:
    args = live_args(
        tmp_path,
        "--skip-graph-facts",
        "--skip-agent-evidence",
    )
    assert [name for name, _ in run_live_evidence.stage_commands(args, tmp_path)] == [
        "notebook_smoke"
    ]


def test_notebook_smoke_defaults_to_affected_modules(tmp_path: Path) -> None:
    args = run_notebook_smoke.build_parser().parse_args(["--output-dir", str(tmp_path)])
    assert args.modules == "1-3"
    assert args.timeout == 1800


def test_output_directories_refuse_to_replace_evidence(tmp_path: Path) -> None:
    (tmp_path / "additive-validation.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        run_additive_validation.prepare_output_dir(tmp_path)

    notebook_dir = tmp_path / "notebooks"
    notebook_dir.mkdir()
    (notebook_dir / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        run_notebook_smoke.prepare_output_dir(notebook_dir)
