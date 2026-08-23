# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Run the live post-build evidence suite into one explicit directory.

The default sequence captures deterministic Phase 1.5 graph facts, runs the
full vector-versus-graph agent harness, then smoke-tests Modules 1 through 3.
Each stage has its own output and log, and ``release-evidence.json`` records
the exact commands and return codes.

This command uses Bedrock and the configured Neo4j graph. It does not run any
deployment notebook or create AWS infrastructure.

Usage from the workshop environment:

    cd notebooks
    uv run python ../setup/run_live_evidence.py \
        --output-dir ../setup/release-evidence/live-20260823 \
        --trials 10 \
        --questions orlando_aggregation pool_counting chicago_criteria \
                    antarctica_no_match chicago_shared_amenities suite_and_spa \
        --arms vector graph \
        --conditions notebook grounded \
        --notebook-modules 1-3 \
        --notebook-timeout 1800
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPTURE_FACTS = REPO_ROOT / "setup" / "phase15" / "capture_graph_facts.py"
HARNESS = REPO_ROOT / "setup" / "phase15" / "harness.py"
NOTEBOOK_SMOKE = REPO_ROOT / "setup" / "run_notebook_smoke.py"

QUESTION_KEYS = (
    "orlando_aggregation",
    "pool_counting",
    "chicago_criteria",
    "antarctica_no_match",
    "chicago_shared_amenities",
    "suite_and_spa",
)
ARMS = ("vector", "graph")
CONDITIONS = ("notebook", "grounded")


def utc_now() -> str:
    """Return an evidence-friendly UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    """Build the live evidence orchestration CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="New directory for the manifest, evidence, notebooks, and logs.",
    )
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument(
        "--questions",
        nargs="+",
        choices=QUESTION_KEYS,
        default=list(QUESTION_KEYS),
    )
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=CONDITIONS,
        default=list(CONDITIONS),
    )
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--notebook-modules", default="1-3")
    parser.add_argument("--notebook-timeout", type=int, default=1800)
    parser.add_argument("--skip-graph-facts", action="store_true")
    parser.add_argument("--skip-agent-evidence", action="store_true")
    parser.add_argument("--skip-notebooks", action="store_true")
    return parser


def stage_commands(
    args: argparse.Namespace, output_dir: Path
) -> list[tuple[str, list[str]]]:
    """Build the exact stage commands with explicit output locations."""
    commands: list[tuple[str, list[str]]] = []
    phase15_dir = output_dir / "phase15"
    if not args.skip_graph_facts:
        commands.append(
            (
                "graph_facts",
                [
                    sys.executable,
                    str(CAPTURE_FACTS),
                    "--out",
                    str(phase15_dir / "graph-facts.json"),
                ],
            )
        )
    if not args.skip_agent_evidence:
        command = [
            sys.executable,
            str(HARNESS),
            "--trials",
            str(args.trials),
            "--out",
            str(phase15_dir / "trials"),
            "--questions",
            *args.questions,
            "--arms",
            *args.arms,
            "--conditions",
            *args.conditions,
        ]
        if args.skip_judge:
            command.append("--skip-judge")
        commands.append(("agent_evidence", command))
    if not args.skip_notebooks:
        commands.append(
            (
                "notebook_smoke",
                [
                    sys.executable,
                    str(NOTEBOOK_SMOKE),
                    "--modules",
                    args.notebook_modules,
                    "--output-dir",
                    str(output_dir / "notebooks"),
                    "--timeout",
                    str(args.notebook_timeout),
                ],
            )
        )
    return commands


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Persist stage progress after every external command."""
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Run the selected evidence stages in order and stop on first failure."""
    parser = build_parser()
    args = parser.parse_args()
    if args.trials <= 0:
        parser.error("--trials must be greater than zero")
    if args.notebook_timeout <= 0:
        parser.error("--notebook-timeout must be greater than zero")

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "release-evidence.json"
    if manifest_path.exists():
        raise SystemExit(f"{manifest_path} already exists; choose a new --output-dir")
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    commands = stage_commands(args, output_dir)
    if not commands:
        parser.error("all evidence stages were skipped")
    manifest: dict[str, Any] = {
        "started_utc": utc_now(),
        "status": "running",
        "configuration": {
            "trials": args.trials,
            "questions": args.questions,
            "arms": args.arms,
            "conditions": args.conditions,
            "skip_judge": args.skip_judge,
            "notebook_modules": args.notebook_modules,
            "notebook_timeout": args.notebook_timeout,
        },
        "stages": [],
    }
    write_manifest(manifest_path, manifest)

    for name, command in commands:
        log_path = logs_dir / f"{name}.log"
        print(f"Running {name}; log: {log_path}", flush=True)
        started = utc_now()
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        manifest["stages"].append(
            {
                "name": name,
                "started_utc": started,
                "completed_utc": utc_now(),
                "command": command,
                "log": str(log_path),
                "returncode": result.returncode,
                "passed": result.returncode == 0,
            }
        )
        write_manifest(manifest_path, manifest)
        if result.returncode != 0:
            manifest["status"] = "failed"
            manifest["completed_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(f"{name} failed; retained evidence in {output_dir}")
            return 1

    manifest["status"] = "passed"
    manifest["completed_utc"] = utc_now()
    write_manifest(manifest_path, manifest)
    print(f"Live evidence passed: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
