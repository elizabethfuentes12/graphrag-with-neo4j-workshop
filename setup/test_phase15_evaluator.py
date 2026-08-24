# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Offline regressions for the repaired Phase 1.5 evaluator contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PHASE15_DIR = Path(__file__).with_name("phase15")
if str(PHASE15_DIR) not in sys.path:
    sys.path.insert(0, str(PHASE15_DIR))

import evaluator_contract
import harness
import report as phase15_report
import validate_evidence


def valid_sample(
    factuality: str,
    grounding: str,
    rationale: str,
) -> dict[str, object]:
    return {
        "factuality": factuality,
        "grounding": grounding,
        "rationale": rationale,
        "raw_response": "{}",
        "parse_error": None,
    }


def test_parser_accepts_only_the_exact_allowed_json_schema() -> None:
    raw = json.dumps(
        {
            "factuality": "correct",
            "grounding": "grounded",
            "rationale": "Every material claim appears in the evidence.",
        }
    )

    assert evaluator_contract.parse_judge_response(raw) == {
        "factuality": "correct",
        "grounding": "grounded",
        "rationale": "Every material claim appears in the evidence.",
    }


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (
            '```json\n{"factuality":"correct","grounding":"grounded",'
            '"rationale":"ok"}\n```',
            "not exact JSON",
        ),
        (
            'Result: {"factuality":"correct","grounding":"grounded",'
            '"rationale":"ok"}',
            "not exact JSON",
        ),
        ('{"factuality":', "not exact JSON"),
        (
            '{"factuality":"correct","grounding":"grounded",'
            '"rationale":"ok","confidence":1}',
            "fields differ from the contract",
        ),
        (
            '{"factuality":"mostly","grounding":"grounded",'
            '"rationale":"ok"}',
            "invalid factuality label",
        ),
        (
            '{"factuality":[],"grounding":"grounded","rationale":"ok"}',
            "factuality label must be a string",
        ),
        (
            '{"factuality":"correct","grounding":{},"rationale":"ok"}',
            "grounding label must be a string",
        ),
    ],
)
def test_parser_rejects_fenced_prefixed_malformed_and_extra_responses(
    raw: str,
    message: str,
) -> None:
    with pytest.raises(evaluator_contract.JudgeResponseError, match=message):
        evaluator_contract.parse_judge_response(raw)


def test_complete_judge_evidence_rejects_instead_of_truncating() -> None:
    accepted = "x" * harness.JUDGE_EVIDENCE_BUDGET

    assert harness.complete_judge_evidence(accepted) == accepted
    with pytest.raises(harness.JudgeEvidenceError, match="must remain unscored"):
        harness.complete_judge_evidence(accepted + "x")


def test_graph_judge_evidence_matches_rendered_agent_evidence() -> None:
    call = harness.CypherCall(
        cypher="MATCH (n) RETURN n",
        records=[{"private_full_record": "judge must not see this"}],
        rendered_evidence="Found 1 results:\n  {'shown': 'to agent'}",
    )

    evidence = harness.graph_evidence_text([call])

    assert "shown" in evidence
    assert "private_full_record" not in evidence


def test_unresolved_vote_tie_is_unscored(monkeypatch) -> None:
    samples = iter(
        [
            valid_sample("correct", "grounded", "first"),
            valid_sample("partial", "grounded", "second"),
            valid_sample("incorrect", "insufficient", "third"),
        ]
    )
    monkeypatch.setattr(harness, "judge_once", lambda *args: next(samples))

    result = harness.judge("region", "question", {}, "evidence", "answer")

    assert result["factuality"] == "unscored"
    assert result["factuality_rationale"] == "unresolved factuality vote"
    assert result["grounding"] == "grounded"
    assert result["grounding_votes"] == 2


def test_winning_rationales_match_labels_and_all_samples_are_preserved(
    monkeypatch,
) -> None:
    expected_samples = [
        valid_sample("partial", "insufficient", "losing rationale"),
        valid_sample("correct", "grounded", "first winning rationale"),
        valid_sample("correct", "grounded", "second winning rationale"),
    ]
    samples = iter(expected_samples)
    monkeypatch.setattr(harness, "judge_once", lambda *args: next(samples))

    result = harness.judge("region", "question", {}, "evidence", "answer")

    assert result["factuality_rationale"] == "first winning rationale"
    assert result["grounding_rationale"] == "first winning rationale"
    assert result["judge_samples"] == expected_samples


def test_report_divisor_includes_question_arm_and_condition() -> None:
    trials = [
        {
            "question_key": question,
            "arm": arm,
            "condition": condition,
        }
        for question in phase15_report.QUESTION_ORDER
        for arm in phase15_report.ARMS
        for condition in phase15_report.CONDITIONS
        for _ in range(10)
    ]

    assert len(trials) == 240
    assert phase15_report.trials_per_evaluation_cell(trials) == 10


def test_evidence_gate_rejects_incomplete_evidence_and_invalid_samples() -> None:
    trial = {
        "question_key": "q",
        "arm": "vector",
        "condition": "grounded",
        "trial": 1,
        "tool_error": None,
        "factuality": "correct",
        "grounding": "grounded",
        "judge_evidence_complete": False,
        "judge_samples_valid": False,
        "judge_error": "evidence exceeded budget",
        "judge_samples": [
            evaluator_contract.unscored_sample("```json", "fenced response")
        ],
    }
    run = {"trials_per_cell": 1, "trials": [trial]}

    problems = validate_evidence.evidence_problems(
        run,
        questions=["q"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )

    assert any("incomplete judge evidence" in problem for problem in problems)
    assert any("invalid judge samples" in problem for problem in problems)
    assert any("judge errors" in problem for problem in problems)


@pytest.mark.parametrize(
    "samples",
    [
        [],
        [valid_sample("unknown", "grounded", "invalid label")],
        [valid_sample("correct", "grounded", "")],
        [valid_sample("correct", "grounded", "one sample")],
    ],
)
def test_evidence_gate_rejects_invalid_or_wrong_count_sample_sets(
    samples: list[dict[str, object]],
) -> None:
    trial = {
        "question_key": "q",
        "arm": "vector",
        "condition": "grounded",
        "trial": 1,
        "tool_error": None,
        "factuality": "correct",
        "grounding": "grounded",
        "judge_evidence_complete": True,
        "judge_samples_valid": True,
        "judge_error": None,
        "judge_samples": samples,
    }
    run = {"trials_per_cell": 1, "judge_samples": 3, "trials": [trial]}

    problems = validate_evidence.evidence_problems(
        run,
        questions=["q"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )

    assert any("invalid judge samples" in problem for problem in problems)
