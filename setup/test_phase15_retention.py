# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Retention and ownership checks for facilitator-only Phase 1.5 assets."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE15_EVIDENCE = REPO_ROOT / "evidence" / "phase15"

COMPACT_REPORTS = (
    PHASE15_EVIDENCE / "README.md",
    PHASE15_EVIDENCE / "PHASE-1.5-FINDINGS.md",
    PHASE15_EVIDENCE / "PHASE-1.5-AMENITY-RECHECK.md",
)
LOCAL_ONLY_PATHS = (
    "evidence/phase15/PHASE-1.5-REPORT.md",
    "evidence/phase15/PHASE-1.5-REPORT-RUN2.md",
    "evidence/phase15/evidence/phase15-merged.json",
    "evidence/phase15/archive/2.1_vector_rag_hallucinates.ipynb",
)


def is_ignored(path: str | Path) -> bool:
    """Return whether Git policy excludes a path, even when it is absent."""
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", str(path)],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


def test_compact_reports_are_trackable_and_raw_artifacts_stay_excluded() -> None:
    assert all(path.is_file() for path in COMPACT_REPORTS)
    assert all(not is_ignored(path.relative_to(REPO_ROOT)) for path in COMPACT_REPORTS)
    assert all(is_ignored(path) for path in LOCAL_ONLY_PATHS)


def test_every_compact_report_marks_historical_grounding_invalid() -> None:
    for path in COMPACT_REPORTS:
        text = path.read_text(encoding="utf-8").lower()
        assert "grounding" in text
        assert "invalid" in text
        assert "setup/release-evidence/" not in text


def test_retention_policy_disclaims_local_raw_and_archived_notebook() -> None:
    policy = (PHASE15_EVIDENCE / "README.md").read_text(encoding="utf-8")

    assert "no recorded durable external URI" in policy
    assert "not release evidence" in policy
    assert "archived `2.1_vector_rag_hallucinates.ipynb` notebook" in policy


def test_faiss_is_complete_facilitator_infrastructure_outside_learner_path() -> None:
    required = (
        "notebooks/02-connected-context/faqs_docs.json",
        "notebooks/02-connected-context/faqs_vector.index",
        "notebooks/02-connected-context/faqs_vector.manifest.json",
        "notebooks/02-connected-context/rebuild_faiss_index.py",
        "notebooks/workshop/faiss_artifacts.py",
        "setup/phase15/harness.py",
        "setup/run_live_evidence.py",
        "setup/test_faiss_artifacts.py",
        "setup/test_rebuild_faiss_index.py",
    )
    assert all((REPO_ROOT / path).is_file() for path in required)

    notebook = (
        REPO_ROOT
        / "notebooks"
        / "02-connected-context"
        / "2.1_connected_context.ipynb"
    ).read_text(encoding="utf-8").lower()
    assert "faqs_vector" not in notebook
    assert "load_faiss" not in notebook
