# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Strict response and voting contract for the Phase 1.5 evaluator."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from typing import Any

FACTUALITY_LABELS = frozenset({"correct", "partial", "incorrect"})
GROUNDING_LABELS = frozenset(
    {"grounded", "insufficient", "unsupported_correct", "fabricated"}
)
JUDGE_RESPONSE_FIELDS = frozenset({"factuality", "grounding", "rationale"})
UNSCORED = "unscored"
EVALUATOR_GENERATION = 3
BENCHMARK_TRIALS_PER_CELL = 10
EVIDENCE_HASH_ALGORITHM = "sha256"


class JudgeResponseError(ValueError):
    """Raised when a judge response violates the exact response contract."""


def parse_judge_response(raw: str) -> dict[str, str]:
    """Parse one exact JSON object with allowed labels and a rationale."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JudgeResponseError(f"judge response is not exact JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise JudgeResponseError("judge response must be a JSON object")
    fields = set(payload)
    if fields != JUDGE_RESPONSE_FIELDS:
        missing = sorted(JUDGE_RESPONSE_FIELDS - fields)
        extra = sorted(fields - JUDGE_RESPONSE_FIELDS)
        raise JudgeResponseError(
            f"judge response fields differ from the contract; "
            f"missing={missing}, extra={extra}"
        )

    factuality = payload["factuality"]
    grounding = payload["grounding"]
    rationale = payload["rationale"]
    if not isinstance(factuality, str):
        raise JudgeResponseError("judge factuality label must be a string")
    if not isinstance(grounding, str):
        raise JudgeResponseError("judge grounding label must be a string")
    if factuality not in FACTUALITY_LABELS:
        raise JudgeResponseError(f"invalid factuality label: {factuality!r}")
    if grounding not in GROUNDING_LABELS:
        raise JudgeResponseError(f"invalid grounding label: {grounding!r}")
    if not isinstance(rationale, str) or not rationale.strip():
        raise JudgeResponseError("judge rationale must be a non-empty string")
    return {
        "factuality": factuality,
        "grounding": grounding,
        "rationale": rationale.strip(),
    }


def unscored_sample(raw: str, error: str) -> dict[str, str]:
    """Return a preserved invalid sample that cannot enter a scored report."""
    return {
        "factuality": UNSCORED,
        "grounding": UNSCORED,
        "rationale": error,
        "raw_response": raw,
        "parse_error": error,
    }


def winning_label(
    samples: Sequence[Mapping[str, Any]],
    field: str,
) -> tuple[str, int]:
    """Return the unique most frequent label or unscored for a tie."""
    counts = Counter(str(sample.get(field, UNSCORED)) for sample in samples)
    if not counts:
        return UNSCORED, 0
    top_count = max(counts.values())
    winners = sorted(label for label, count in counts.items() if count == top_count)
    if len(winners) != 1:
        return UNSCORED, top_count
    return winners[0], top_count


def rationale_for_label(
    samples: Sequence[Mapping[str, Any]],
    field: str,
    label: str,
) -> str:
    """Return a rationale from a sample that cast the winning label."""
    if label == UNSCORED:
        return f"unresolved {field} vote"
    for sample in samples:
        if sample.get(field) == label:
            return str(sample.get("rationale", ""))
    return f"no rationale recorded for winning {field} label {label!r}"


def evidence_text_from_trial(trial: Mapping[str, Any]) -> str:
    """Rebuild the exact tool evidence sent to the judge for one trial."""
    retrieval = trial.get("retrieval")
    if not isinstance(retrieval, list):
        raise TypeError("retrieval must be a list")

    arm = trial.get("arm")
    if arm == "vector":
        if not retrieval:
            return "(the agent made no retrieval call)"
        blocks = []
        for position, item in enumerate(retrieval, start=1):
            if not isinstance(item, Mapping):
                raise TypeError(f"retrieval {position} must be an object")
            query = item.get("query")
            filenames = item.get("filenames")
            texts = item.get("texts")
            if not isinstance(query, str):
                raise TypeError(f"retrieval {position} query must be a string")
            if not isinstance(filenames, list) or not all(
                isinstance(value, str) for value in filenames
            ):
                raise TypeError(
                    f"retrieval {position} filenames must be a list of strings"
                )
            if not isinstance(texts, list) or not all(
                isinstance(value, str) for value in texts
            ):
                raise TypeError(
                    f"retrieval {position} texts must be a list of strings"
                )
            if len(filenames) != len(texts):
                raise ValueError(
                    f"retrieval {position} has {len(filenames)} filenames and "
                    f"{len(texts)} texts"
                )
            body = "\n\n".join(
                f"[{name}]\n{text}" for name, text in zip(filenames, texts)
            )
            blocks.append(f"search_faqs({query!r}) returned:\n{body}")
        return "\n\n".join(blocks)

    if arm == "graph":
        if not retrieval:
            return "(the agent made no graph call)"
        blocks = []
        for position, item in enumerate(retrieval, start=1):
            if not isinstance(item, Mapping):
                raise TypeError(f"retrieval {position} must be an object")
            cypher = item.get("cypher")
            error = item.get("error")
            detail = error if error else item.get("rendered_evidence")
            if not isinstance(cypher, str):
                raise TypeError(f"retrieval {position} cypher must be a string")
            if not isinstance(detail, str):
                raise TypeError(
                    f"retrieval {position} rendered evidence must be a string"
                )
            blocks.append(f"cypher:\n{cypher}\nresult:\n{detail}")
        return "\n\n".join(blocks)

    raise ValueError(f"unsupported arm: {arm!r}")


def evidence_metadata(evidence: str) -> dict[str, Any]:
    """Return the retained size and integrity metadata for judge evidence."""
    return {
        "judge_evidence_characters": len(evidence),
        "judge_evidence_sha256": sha256(evidence.encode("utf-8")).hexdigest(),
    }


def trial_judge_problems(
    trial: Mapping[str, Any],
    *,
    expected_sample_count: int | None,
    evidence_budget: int | None,
) -> list[str]:
    """Recompute one trial's judge result and return contract violations."""
    problems: list[str] = []
    samples = trial.get("judge_samples")
    if not isinstance(samples, list) or not samples:
        return ["judge_samples must be a non-empty list"]
    if expected_sample_count is not None and len(samples) != expected_sample_count:
        problems.append(
            f"judge sample count is {len(samples)}, expected {expected_sample_count}"
        )

    parsed_samples: list[dict[str, str]] = []
    for position, sample in enumerate(samples, start=1):
        if not isinstance(sample, Mapping):
            problems.append(f"judge sample {position} must be an object")
            continue
        raw = sample.get("raw_response")
        if not isinstance(raw, str):
            problems.append(f"judge sample {position} raw_response must be a string")
            continue
        try:
            parsed = parse_judge_response(raw)
        except JudgeResponseError as exc:
            problems.append(f"judge sample {position} raw response: {exc}")
            continue
        recorded = {
            "factuality": sample.get("factuality"),
            "grounding": sample.get("grounding"),
            "rationale": sample.get("rationale"),
        }
        if recorded != parsed:
            problems.append(
                f"judge sample {position} parsed values differ from recorded values"
            )
            continue
        if sample.get("parse_error") is not None:
            problems.append(
                f"judge sample {position} has a parse_error despite valid raw JSON"
            )
            continue
        parsed_samples.append(parsed)

    if len(parsed_samples) == len(samples):
        for field in ("factuality", "grounding"):
            winner, votes = winning_label(parsed_samples, field)
            if winner == UNSCORED:
                problems.append(f"{field} vote has no unique winner")
                continue
            if trial.get(field) != winner:
                problems.append(
                    f"{field} winner is {winner!r}, recorded {trial.get(field)!r}"
                )
            vote_field = f"{field}_votes"
            if trial.get(vote_field) != votes:
                problems.append(
                    f"{vote_field} is {trial.get(vote_field)!r}, expected {votes}"
                )
            rationale_field = f"{field}_rationale"
            rationale = trial.get(rationale_field)
            winning_rationales = {
                sample["rationale"]
                for sample in parsed_samples
                if sample[field] == winner
            }
            if rationale not in winning_rationales:
                problems.append(
                    f"{rationale_field} does not belong to a sample voting {winner!r}"
                )

        expected_rationale = (
            f"Factuality: {trial.get('factuality_rationale')} "
            f"Grounding: {trial.get('grounding_rationale')}"
        )
        if trial.get("rationale") != expected_rationale:
            problems.append("combined rationale differs from the winning rationales")

    if trial.get("judge_samples_valid") is not True:
        problems.append("judge_samples_valid must be true")
    if trial.get("judge_evidence_complete") is not True:
        problems.append("judge_evidence_complete must be true")
    try:
        evidence = evidence_text_from_trial(trial)
    except (TypeError, ValueError) as exc:
        problems.append(f"judge evidence cannot be reconstructed: {exc}")
    else:
        metadata = evidence_metadata(evidence)
        for field, expected in metadata.items():
            if trial.get(field) != expected:
                problems.append(
                    f"{field} is {trial.get(field)!r}, expected {expected!r}"
                )
        if evidence_budget is None:
            problems.append("judge evidence budget is invalid")
        elif len(evidence) > evidence_budget:
            problems.append(
                f"judge evidence has {len(evidence)} characters, "
                f"exceeding budget {evidence_budget}"
            )
    return problems
