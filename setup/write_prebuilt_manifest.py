# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Capture and finalize provenance for a prebuilt graph candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

CRITICAL_FILES = {
    "graph_builder": Path("notebooks/02-connected-context/graph_builder.py"),
    "graph_config": Path("notebooks/02-connected-context/graph_config.py"),
    "prepare_graph": Path("notebooks/02-connected-context/prepare_graph.py"),
    "amenities": Path("notebooks/workshop/amenities.py"),
    "contracts": Path("notebooks/workshop/contracts.py"),
    "graph_schema_contract": Path("notebooks/workshop/graph_schema.py"),
    "retrieval_contract": Path("notebooks/workshop/retrieval_contract.py"),
    "corpus": Path("notebooks/02-connected-context/hotel-faqs.zip"),
    "uv_lock": Path("notebooks/workshop/uv.lock"),
    "build_script": Path("setup/build_prebuilt_graph.sh"),
    "manifest_writer": Path("setup/write_prebuilt_manifest.py"),
}


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 without loading the full artifact into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\n")


def start_snapshot(
    repo_root: Path,
    *,
    started_at: str,
    started_epoch: int,
    resume_mode: bool,
) -> dict[str, Any]:
    """Capture immutable build inputs before the long-running work starts."""
    status = _git(repo_root, "status", "--porcelain=v1", "--untracked-files=normal")
    critical_files = {}
    for name, relative_path in CRITICAL_FILES.items():
        path = repo_root / relative_path
        critical_files[name] = {
            "path": relative_path.as_posix(),
            "sha256": sha256_file(path),
        }

    return {
        "manifest_version": 1,
        "build": {
            "started_at": started_at,
            "started_epoch": started_epoch,
            "resume_mode": resume_mode,
        },
        "git": {
            "commit": _git(repo_root, "rev-parse", "HEAD"),
            "dirty": bool(status),
            "status_porcelain": status.splitlines(),
        },
        "critical_files": critical_files,
    }


def final_manifest(
    snapshot: dict[str, Any],
    candidate: Path,
    *,
    completed_at: str,
    completed_epoch: int,
    image_tag: str,
    image_id: str,
    image_repo_digests: list[str],
) -> dict[str, Any]:
    """Add output identity and completion facts to a start snapshot."""
    manifest = dict(snapshot)
    build = dict(snapshot["build"])
    build.update(
        {
            "completed_at": completed_at,
            "completed_epoch": completed_epoch,
            "duration_seconds": completed_epoch - build["started_epoch"],
        }
    )
    manifest.update(
        {
            "build": build,
            "docker_image": {
                "requested_tag": image_tag,
                "id": image_id,
                "repo_digests": image_repo_digests,
            },
            "candidate": {
                "path": candidate.name,
                "byte_size": candidate.stat().st_size,
                "sha256": sha256_file(candidate),
            },
            "final_success": True,
        }
    )
    return manifest


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    """Publish JSON atomically without replacing an existing manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(value, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.link(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Capture build-start provenance.")
    start.add_argument("--repo-root", type=Path, required=True)
    start.add_argument("--output", type=Path, required=True)
    start.add_argument("--started-at", required=True)
    start.add_argument("--started-epoch", type=int, required=True)
    start.add_argument("--resume", action="store_true")

    finish = subparsers.add_parser("finish", help="Write the final manifest.")
    finish.add_argument("--snapshot", type=Path, required=True)
    finish.add_argument("--candidate", type=Path, required=True)
    finish.add_argument("--manifest", type=Path, required=True)
    finish.add_argument("--completed-at", required=True)
    finish.add_argument("--completed-epoch", type=int, required=True)
    finish.add_argument("--image-tag", required=True)
    finish.add_argument("--image-id", required=True)
    finish.add_argument("--image-repo-digests-json", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "start":
        snapshot = start_snapshot(
            args.repo_root.resolve(),
            started_at=args.started_at,
            started_epoch=args.started_epoch,
            resume_mode=args.resume,
        )
        args.output.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    repo_digests = json.loads(args.image_repo_digests_json)
    if not isinstance(repo_digests, list) or not all(
        isinstance(item, str) for item in repo_digests
    ):
        raise ValueError("image repo digests must be a JSON list of strings")
    manifest = final_manifest(
        snapshot,
        args.candidate,
        completed_at=args.completed_at,
        completed_epoch=args.completed_epoch,
        image_tag=args.image_tag,
        image_id=args.image_id,
        image_repo_digests=repo_digests,
    )
    write_json_exclusive(args.manifest, manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
