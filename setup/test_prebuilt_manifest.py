# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Offline tests for prebuilt candidate provenance manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SETUP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SETUP_DIR))

import write_prebuilt_manifest


def test_start_snapshot_captures_git_state_and_critical_hashes(
    tmp_path: Path, monkeypatch
) -> None:
    critical = tmp_path / "builder.py"
    critical.write_text("build input\n", encoding="utf-8")
    monkeypatch.setattr(
        write_prebuilt_manifest,
        "CRITICAL_FILES",
        {"graph_builder": Path("builder.py")},
    )

    def fake_git(repo_root: Path, *args: str) -> str:
        assert repo_root == tmp_path
        if args[0] == "status":
            return " M builder.py\n?? notes.txt"
        return "0123456789abcdef"

    monkeypatch.setattr(write_prebuilt_manifest, "_git", fake_git)

    snapshot = write_prebuilt_manifest.start_snapshot(
        tmp_path,
        started_at="2026-08-23T10:00:00Z",
        started_epoch=100,
        resume_mode=True,
    )

    assert snapshot["build"] == {
        "started_at": "2026-08-23T10:00:00Z",
        "started_epoch": 100,
        "resume_mode": True,
    }
    assert snapshot["git"] == {
        "commit": "0123456789abcdef",
        "dirty": True,
        "status_porcelain": [" M builder.py", "?? notes.txt"],
    }
    assert snapshot["critical_files"]["graph_builder"] == {
        "path": "builder.py",
        "sha256": write_prebuilt_manifest.sha256_file(critical),
    }


def test_final_manifest_is_complete_and_never_overwrites(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.dump"
    candidate.write_bytes(b"neo4j candidate")
    snapshot = {
        "manifest_version": 1,
        "build": {
            "started_at": "2026-08-23T10:00:00Z",
            "started_epoch": 100,
            "resume_mode": False,
        },
        "git": {"commit": "abc", "dirty": False, "status_porcelain": []},
        "critical_files": {},
    }

    manifest = write_prebuilt_manifest.final_manifest(
        snapshot,
        candidate,
        completed_at="2026-08-23T10:02:03Z",
        completed_epoch=223,
        image_tag="neo4j:latest",
        image_id="sha256:image-id",
        image_repo_digests=["neo4j@sha256:repo-digest"],
    )
    output = tmp_path / "candidate.manifest.json"
    write_prebuilt_manifest.write_json_exclusive(output, manifest)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["final_success"] is True
    assert written["build"]["duration_seconds"] == 123
    assert written["build"]["resume_mode"] is False
    assert written["docker_image"] == {
        "requested_tag": "neo4j:latest",
        "id": "sha256:image-id",
        "repo_digests": ["neo4j@sha256:repo-digest"],
    }
    assert written["candidate"] == {
        "path": candidate.name,
        "byte_size": len(b"neo4j candidate"),
        "sha256": write_prebuilt_manifest.sha256_file(candidate),
    }

    with pytest.raises(FileExistsError):
        write_prebuilt_manifest.write_json_exclusive(output, {"final_success": False})
    assert json.loads(output.read_text(encoding="utf-8")) == written
