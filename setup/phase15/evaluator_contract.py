# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Strict response and voting contract for the Phase 1.5 evaluator."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

FACTUALITY_LABELS = frozenset({"correct", "partial", "incorrect"})
GROUNDING_LABELS = frozenset(
    {"grounded", "insufficient", "unsupported_correct", "fabricated"}
)
JUDGE_RESPONSE_FIELDS = frozenset({"factuality", "grounding", "rationale"})
UNSCORED = "unscored"


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
