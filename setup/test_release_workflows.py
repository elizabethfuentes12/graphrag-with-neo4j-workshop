# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Offline tests for the reusable additive and live-evidence operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest
import run_additive_validation
import run_live_evidence
import run_notebook_smoke

PHASE15_DIR = Path(__file__).with_name("phase15")
if str(PHASE15_DIR) not in sys.path:
    sys.path.insert(0, str(PHASE15_DIR))
import validate_evidence

ADDITIVE_WRAPPER = Path(__file__).with_name("run_additive_validation.sh")


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


def test_live_question_partitions_are_deterministic_and_balanced() -> None:
    questions = list(run_live_evidence.QUESTION_KEYS)

    assert run_live_evidence.question_partitions(questions, 3) == [
        [questions[0], questions[3]],
        [questions[1], questions[4]],
        [questions[2], questions[5]],
    ]


def test_live_worker_and_gate_commands_use_distinct_dynamic_contracts(
    tmp_path: Path,
) -> None:
    args = live_args(
        tmp_path,
        "--trials",
        "1",
        "--agent-workers",
        "2",
        "--questions",
        "orlando_aggregation",
        "pool_counting",
    )
    partitions = run_live_evidence.question_partitions(
        args.questions, args.agent_workers
    )
    commands = [
        run_live_evidence.harness_command(args, tmp_path / f"worker-{index}", part)
        for index, part in enumerate(partitions, start=1)
    ]

    assert commands[0] != commands[1]
    assert str(tmp_path / "worker-1") in commands[0]
    assert str(tmp_path / "worker-2") in commands[1]
    gate = run_live_evidence.gate_command(args, tmp_path / "merged.json")
    assert gate[gate.index("--trials-per-cell") + 1] == "1"
    assert "orlando_aggregation" in gate
    assert "pool_counting" in gate


def test_release_smoke_gate_derives_24_trials_and_rejects_quality_gaps() -> None:
    questions = list(run_live_evidence.QUESTION_KEYS)
    trials = [
        {
            "question_key": question,
            "arm": arm,
            "condition": condition,
            "trial": 1,
            "tool_error": None,
            "factuality": "correct",
            "grounding": "grounded",
        }
        for question in questions
        for arm in run_live_evidence.ARMS
        for condition in run_live_evidence.CONDITIONS
    ]
    run = {"trials_per_cell": 1, "trials": trials}

    assert len(trials) == 24
    assert (
        validate_evidence.evidence_problems(
            run,
            questions=questions,
            arms=list(run_live_evidence.ARMS),
            conditions=list(run_live_evidence.CONDITIONS),
            trials_per_cell=1,
        )
        == []
    )

    broken = json.loads(json.dumps(run))
    broken["trials"][0]["tool_error"] = "ThrottlingException"
    broken["trials"][1]["factuality"] = "unscored"
    problems = validate_evidence.evidence_problems(
        broken,
        questions=questions,
        arms=list(run_live_evidence.ARMS),
        conditions=list(run_live_evidence.CONDITIONS),
        trials_per_cell=1,
    )
    assert any("tool errors" in problem for problem in problems)
    assert any("unscored" in problem for problem in problems)


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


def test_additive_wrapper_restores_locally_and_can_retain_result() -> None:
    script = ADDITIVE_WRAPPER.read_text(encoding="utf-8")

    assert 'if [[ "${1:-}" == "--retain" ]]' in script
    assert "neo4j-admin database load" in script
    assert "validate_prebuilt_candidate.py" in script
    assert "run_additive_validation.py" in script
    assert "NEO4J_PLUGINS" in script
    assert 'docker volume rm "$VOLUME"' in script
    assert 'if [[ "$RETAIN" == true ]]' in script
    assert '"password": password' not in script
    assert '"credential_note"' in script


def test_additive_wrapper_help_needs_no_candidate_or_docker() -> None:
    result = __import__("subprocess").run(
        [str(ADDITIVE_WRAPPER), "--help"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "[--retain] [candidate.dump] [output-dir]" in result.stdout
