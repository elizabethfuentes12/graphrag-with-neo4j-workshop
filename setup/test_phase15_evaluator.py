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
import merge_evidence
import report as phase15_report
import validate_evidence


def valid_sample(
    factuality: str,
    grounding: str,
    rationale: str,
) -> dict[str, object]:
    raw_response = json.dumps(
        {
            "factuality": factuality,
            "grounding": grounding,
            "rationale": rationale,
        }
    )
    return {
        "factuality": factuality,
        "grounding": grounding,
        "rationale": rationale,
        "raw_response": raw_response,
        "parse_error": None,
    }


def valid_trial(
    *,
    question: str = "q",
    arm: str = "vector",
    condition: str = "grounded",
    trial_number: int = 1,
) -> dict[str, object]:
    """Return one internally consistent strict-evaluator trial."""
    rationale = "Every material claim appears in the evidence."
    trial: dict[str, object] = {
        "question_key": question,
        "arm": arm,
        "condition": condition,
        "trial": trial_number,
        "tool_error": None,
        "factuality": "correct",
        "grounding": "grounded",
        "factuality_votes": 3,
        "grounding_votes": 3,
        "factuality_rationale": rationale,
        "grounding_rationale": rationale,
        "rationale": f"Factuality: {rationale} Grounding: {rationale}",
        "judge_evidence_complete": True,
        "judge_samples_valid": True,
        "judge_error": None,
        "judge_samples": [
            valid_sample("correct", "grounded", rationale) for _ in range(3)
        ],
        "retrieval": (
            [
                {
                    "query": "hotel question",
                    "filenames": ["hotel.txt"],
                    "scores": [0.9],
                    "texts": ["complete evidence"],
                }
            ]
            if arm == "vector"
            else [
                {
                    "cypher": "MATCH (h:Hotel) RETURN h.name",
                    "records": [{"name": "Hotel"}],
                    "error": None,
                    "rendered_evidence": "Found 1 results:\n  {'name': 'Hotel'}",
                }
            ]
        ),
    }
    evidence = evaluator_contract.evidence_text_from_trial(trial)
    trial.update(evaluator_contract.evidence_metadata(evidence))
    return trial


def valid_run(
    *,
    questions: tuple[str, ...] = ("q",),
    arms: tuple[str, ...] = ("vector",),
    conditions: tuple[str, ...] = ("grounded",),
    trials_per_cell: int = 1,
) -> dict[str, object]:
    """Return a complete run for a requested offline validation matrix."""
    manifest = {
        "embedding_model_id": "embedding-model",
        "embedding_dimensions": 2,
        "embedding_purpose": "GENERIC_INDEX",
        "document_count": 1,
        "corpus_sha256": "a" * 64,
        "vectors_sha256": "b" * 64,
        "vector_source": "test",
        "faiss_metric": "inner_product",
        "vector_normalization": "l2",
    }
    return {
        "evaluator_generation": evaluator_contract.EVALUATOR_GENERATION,
        "run_generation": 3,
        "model_id": "chat-model",
        "region": "us-west-2",
        "neo4j_uri": "neo4j+s://example.invalid",
        "neo4j_database": "neo4j",
        "trials_per_cell": trials_per_cell,
        "top_k": 3,
        "judge_samples": 3,
        "judge_evidence_budget": 60_000,
        "conditions": list(conditions),
        "arms": list(arms),
        "evaluator_settings": {
            "top_k": 3,
            "judge_samples": 3,
            "judge_evidence_budget": 60_000,
            "judge_evidence_hash": "sha256",
            "graph_result_budget": 60_000,
            "questions": [{"key": question} for question in questions],
            "conditions": list(conditions),
            "vector_prompt": "vector prompt",
            "graph_prompt": "graph prompt",
            "grounding_suffix": " grounding suffix",
            "judge_system_prompt": "judge prompt",
            "judge_response_fields": ["factuality", "grounding", "rationale"],
            "factuality_labels": ["correct", "incorrect", "partial"],
            "grounding_labels": [
                "fabricated",
                "grounded",
                "insufficient",
                "unsupported_correct",
            ],
        },
        "embedding_model_id": "embedding-model",
        "index_dimensions": 2,
        "index_vectors": 1,
        "corpus_sha256_now": "a" * 64,
        "faiss_manifest": manifest,
        "source_facts": {"source": "facts"},
        "graph_facts": {"graph": "facts"},
        "trials": [
            valid_trial(
                question=question,
                arm=arm,
                condition=condition,
                trial_number=trial_number,
            )
            for question in questions
            for arm in arms
            for condition in conditions
            for trial_number in range(1, trials_per_cell + 1)
        ],
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
            (
                '```json\n{"factuality":"correct","grounding":"grounded",'
                '"rationale":"ok"}\n```'
            ),
            "not exact JSON",
        ),
        (
            (
                'Result: {"factuality":"correct","grounding":"grounded",'
                '"rationale":"ok"}'
            ),
            "not exact JSON",
        ),
        ('{"factuality":', "not exact JSON"),
        (
            (
                '{"factuality":"correct","grounding":"grounded",'
                '"rationale":"ok","confidence":1}'
            ),
            "fields differ from the contract",
        ),
        (
            (
                '{"factuality":"mostly","grounding":"grounded",'
                '"rationale":"ok"}'
            ),
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
    run = valid_run()
    trial = run["trials"][0]
    trial["judge_evidence_complete"] = False
    trial["judge_samples_valid"] = False
    trial["judge_error"] = "evidence exceeded budget"
    trial["judge_samples"][0] = evaluator_contract.unscored_sample(
        "```json", "fenced response"
    )

    problems = validate_evidence.evidence_problems(
        run,
        questions=["q"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )

    assert any("judge_evidence_complete" in problem for problem in problems)
    assert any("raw response" in problem for problem in problems)
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
    run = valid_run()
    run["trials"][0]["judge_samples"] = samples

    problems = validate_evidence.evidence_problems(
        run,
        questions=["q"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )

    assert any("judge_sample" in problem or "judge sample" in problem for problem in problems)


def strict_problems(run: dict[str, object]) -> list[str]:
    """Validate the one-cell fixture used by mutation tests."""
    return validate_evidence.evidence_problems(
        run,
        questions=["q"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )


def test_authoritative_gate_accepts_recomputed_evidence() -> None:
    assert strict_problems(valid_run()) == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda trial: trial["judge_samples"][0].update(
                {"raw_response": '{"factuality":"incorrect"}'}
            ),
            "raw response",
        ),
        (
            lambda trial: trial.update({"judge_samples_valid": False}),
            "judge_samples_valid",
        ),
        (
            lambda trial: trial.update({"factuality": "partial"}),
            "factuality winner",
        ),
        (
            lambda trial: trial.update({"grounding_votes": 2}),
            "grounding_votes",
        ),
        (
            lambda trial: trial.update(
                {"grounding_rationale": "not cast by a winning sample"}
            ),
            "grounding_rationale",
        ),
        (
            lambda trial: trial.update({"judge_evidence_characters": 1}),
            "judge_evidence_characters",
        ),
        (
            lambda trial: trial.update({"judge_evidence_sha256": "0" * 64}),
            "judge_evidence_sha256",
        ),
    ],
)
def test_gate_rejects_mutated_judge_derivations(
    mutation: object,
    message: str,
) -> None:
    run = valid_run()
    mutation(run["trials"][0])

    assert any(message in problem for problem in strict_problems(run))


def test_gate_rejects_manifest_drift_and_unbalanced_cells() -> None:
    run = valid_run(questions=("q", "q2"))
    run["faiss_manifest"]["corpus_sha256"] = "c" * 64
    run["trials"].pop()

    problems = validate_evidence.evidence_problems(
        run,
        questions=["q", "q2"],
        arms=["vector"],
        conditions=["grounded"],
        trials_per_cell=1,
    )

    assert any("FAISS manifest corpus_sha256" in problem for problem in problems)
    assert any("missing cell" in problem for problem in problems)


def test_merge_pins_complete_manifest_and_evaluator_settings() -> None:
    first = valid_run()
    second = json.loads(json.dumps(first))
    second["faiss_manifest"]["vectors_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="faiss_manifest"):
        merge_evidence.check_headers([first, second])

    second = json.loads(json.dumps(first))
    second["evaluator_settings"]["judge_system_prompt"] = "changed"
    with pytest.raises(ValueError, match="evaluator_settings"):
        merge_evidence.check_headers([first, second])


def test_report_and_gate_agree_on_publishable_ten_trial_cells() -> None:
    run = valid_run(
        questions=phase15_report.QUESTION_ORDER,
        arms=phase15_report.ARMS,
        conditions=phase15_report.CONDITIONS,
        trials_per_cell=evaluator_contract.BENCHMARK_TRIALS_PER_CELL,
    )

    assert len(run["trials"]) == 240
    assert phase15_report.publication_problems(run) == []
    assert phase15_report.grounding_labels_are_publishable(run)

    run["trials"][0]["factuality_votes"] = 1
    assert phase15_report.publication_problems(run)
    assert not phase15_report.grounding_labels_are_publishable(run)


def test_historical_generation_can_never_become_publishable() -> None:
    run = valid_run(
        questions=phase15_report.QUESTION_ORDER,
        arms=phase15_report.ARMS,
        conditions=phase15_report.CONDITIONS,
        trials_per_cell=evaluator_contract.BENCHMARK_TRIALS_PER_CELL,
    )
    run["evaluator_generation"] = evaluator_contract.EVALUATOR_GENERATION - 1

    assert not phase15_report.grounding_labels_are_publishable(run)


def test_report_refuses_a_current_run_that_fails_the_strict_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    evidence = tmp_path / "invalid-current-run.json"
    output = tmp_path / "report.md"
    evidence.write_text(json.dumps(valid_run()), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["report.py", str(evidence), "--out", str(output)],
    )

    assert phase15_report.main() == 1
    assert not output.exists()
