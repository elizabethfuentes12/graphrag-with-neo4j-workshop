# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Run the facilitator-only live evidence suite into one explicit directory.

The default sequence captures deterministic Phase 1.5 graph facts, runs the
full vector-versus-graph agent harness, then smoke-tests Modules 1 through 3.
Each stage has its own output and log, and ``release-evidence.json`` records
the exact commands and return codes.

This command uses Bedrock and the configured Neo4j graph. It does not run any
deployment notebook or create AWS infrastructure.

The learner workflow does not call this command. Raw output is local diagnostic
material until it is copied to durable storage and a tracked compact report
records its immutable URI and checksum.

Usage from the workshop environment:

    cd notebooks
    # Release smoke: one trial in each of the 24 cells.
    uv run python ../setup/run_live_evidence.py \
        --output-dir ../evidence/live-20260823 \
        --trials 1 \
        --agent-workers 3 \
        --questions orlando_aggregation pool_counting chicago_criteria \
                    antarctica_no_match chicago_shared_amenities suite_and_spa \
        --arms vector graph \
        --conditions notebook grounded \
        --notebook-modules 1-3 \
        --notebook-timeout 1800

Use ``--trials 10`` for the optional 240-trial benchmark. Evidence gates derive
their expected total from the selected questions, arms, conditions, and trials.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPTURE_FACTS = REPO_ROOT / "setup" / "phase15" / "capture_graph_facts.py"
HARNESS = REPO_ROOT / "setup" / "phase15" / "harness.py"
MERGE_EVIDENCE = REPO_ROOT / "setup" / "phase15" / "merge_evidence.py"
VALIDATE_EVIDENCE = REPO_ROOT / "setup" / "phase15" / "validate_evidence.py"
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
    parser.add_argument(
        "--trials",
        type=int,
        default=10,
        help="Trials per question/arm/condition cell (1 for release smoke; 10 for benchmark).",
    )
    parser.add_argument(
        "--agent-workers",
        type=int,
        default=1,
        help="Question-partitioned harness processes (default: 1).",
    )
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


def question_partitions(questions: list[str], workers: int) -> list[list[str]]:
    """Partition questions deterministically and balance their input order."""
    return [questions[position::workers] for position in range(workers)]


def harness_command(
    args: argparse.Namespace, output_dir: Path, questions: list[str]
) -> list[str]:
    """Build one harness command for an explicit question partition."""
    command = [
        sys.executable,
        str(HARNESS),
        "--trials",
        str(args.trials),
        "--out",
        str(output_dir),
        "--questions",
        *questions,
        "--arms",
        *args.arms,
        "--conditions",
        *args.conditions,
    ]
    if args.skip_judge:
        command.append("--skip-judge")
    return command


def gate_command(args: argparse.Namespace, evidence: Path) -> list[str]:
    """Build the strict post-harness evidence validation command."""
    command = [
        sys.executable,
        str(VALIDATE_EVIDENCE),
        str(evidence),
        "--trials-per-cell",
        str(args.trials),
        "--questions",
        *args.questions,
        "--arms",
        *args.arms,
        "--conditions",
        *args.conditions,
    ]
    return command


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Persist stage progress after every external command."""
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_command(command: list[str], log_path: Path) -> int:
    """Run one logged child process and return its status."""
    with log_path.open("w", encoding="utf-8") as log:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return result.returncode


def stage_record(name: str, command: list[str], log_path: Path) -> dict[str, Any]:
    """Create a running manifest record for one external command."""
    return {
        "name": name,
        "started_utc": utc_now(),
        "command": command,
        "log": str(log_path),
        "returncode": None,
        "passed": None,
    }


def complete_stage(record: dict[str, Any], returncode: int) -> None:
    """Complete one manifest stage record in place."""
    record.update(
        {
            "completed_utc": utc_now(),
            "returncode": returncode,
            "passed": returncode == 0,
        }
    )


def evidence_file(directory: Path) -> Path:
    """Return the sole harness evidence file in a fresh output directory."""
    paths = sorted(directory.glob("phase15-*.json"))
    if len(paths) != 1:
        raise ValueError(
            f"expected one harness evidence file in {directory}, found {len(paths)}"
        )
    return paths[0]


def run_parallel_agent_evidence(
    args: argparse.Namespace,
    output_dir: Path,
    logs_dir: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
) -> Path | None:
    """Run question slices concurrently, merge them, and return merged evidence."""
    trials_dir = output_dir / "phase15" / "trials"
    slices_dir = trials_dir / "slices"
    slices_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for position, questions in enumerate(
        question_partitions(args.questions, args.agent_workers), start=1
    ):
        worker_name = f"agent_evidence_worker_{position:02d}"
        worker_dir = slices_dir / f"worker-{position:02d}"
        worker_dir.mkdir(parents=True, exist_ok=True)
        record = stage_record(
            worker_name,
            harness_command(args, worker_dir, questions),
            logs_dir / f"{worker_name}.log",
        )
        record["questions"] = questions
        records.append(record)
    manifest["stages"].extend(records)
    write_manifest(manifest_path, manifest)

    with ThreadPoolExecutor(max_workers=args.agent_workers) as executor:
        futures = {
            executor.submit(run_command, record["command"], Path(record["log"])): record
            for record in records
        }
        for future in as_completed(futures):
            record = futures[future]
            complete_stage(record, future.result())
            write_manifest(manifest_path, manifest)

    if any(not record["passed"] for record in records):
        return None

    merge_input = trials_dir / "merge-input"
    merge_input.mkdir(parents=True, exist_ok=True)
    try:
        for position, record in enumerate(records, start=1):
            source = evidence_file(slices_dir / f"worker-{position:02d}")
            shutil.copy2(source, merge_input / f"phase15-worker-{position:02d}.json")
    except (OSError, ValueError) as exc:
        log_path = logs_dir / "agent_evidence_merge.log"
        log_path.write_text(f"ERROR: {exc}\n", encoding="utf-8")
        record = stage_record("agent_evidence_merge", [], log_path)
        complete_stage(record, 1)
        manifest["stages"].append(record)
        write_manifest(manifest_path, manifest)
        return None

    merged = trials_dir / "phase15-merged.json"
    merge_command = [
        sys.executable,
        str(MERGE_EVIDENCE),
        str(merge_input),
        "--out",
        str(merged),
    ]
    merge_record = stage_record(
        "agent_evidence_merge", merge_command, logs_dir / "agent_evidence_merge.log"
    )
    manifest["stages"].append(merge_record)
    write_manifest(manifest_path, manifest)
    complete_stage(
        merge_record,
        run_command(merge_command, Path(merge_record["log"])),
    )
    write_manifest(manifest_path, manifest)
    return merged if merge_record["passed"] else None


def run_evidence_gate(
    args: argparse.Namespace,
    evidence: Path,
    logs_dir: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
) -> bool:
    """Run and record the strict agent-evidence acceptance gate."""
    command = gate_command(args, evidence)
    record = stage_record(
        "agent_evidence_gate", command, logs_dir / "agent_evidence_gate.log"
    )
    manifest["stages"].append(record)
    write_manifest(manifest_path, manifest)
    complete_stage(record, run_command(command, Path(record["log"])))
    write_manifest(manifest_path, manifest)
    return bool(record["passed"])


def main() -> int:
    """Run the selected evidence stages in order and stop on first failure."""
    parser = build_parser()
    args = parser.parse_args()
    if args.trials <= 0:
        parser.error("--trials must be greater than zero")
    if args.agent_workers <= 0:
        parser.error("--agent-workers must be greater than zero")
    if args.agent_workers > len(args.questions):
        parser.error("--agent-workers cannot exceed the selected question count")
    if args.notebook_timeout <= 0:
        parser.error("--notebook-timeout must be greater than zero")
    for option in ("questions", "arms", "conditions"):
        values = getattr(args, option)
        if len(values) != len(set(values)):
            parser.error(f"--{option} cannot contain duplicates")

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
            "agent_workers": args.agent_workers,
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
        if name == "agent_evidence" and args.agent_workers > 1:
            print(
                f"Running agent evidence with {args.agent_workers} workers; "
                f"logs: {logs_dir}",
                flush=True,
            )
            evidence = run_parallel_agent_evidence(
                args, output_dir, logs_dir, manifest, manifest_path
            )
            if evidence is None or not run_evidence_gate(
                args, evidence, logs_dir, manifest, manifest_path
            ):
                manifest["status"] = "failed"
                manifest["completed_utc"] = utc_now()
                write_manifest(manifest_path, manifest)
                print(f"agent evidence failed; retained evidence in {output_dir}")
                return 1
            continue

        log_path = logs_dir / f"{name}.log"
        print(f"Running {name}; log: {log_path}", flush=True)
        record = stage_record(name, command, log_path)
        manifest["stages"].append(record)
        write_manifest(manifest_path, manifest)
        complete_stage(record, run_command(command, log_path))
        write_manifest(manifest_path, manifest)
        if not record["passed"]:
            manifest["status"] = "failed"
            manifest["completed_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(f"{name} failed; retained evidence in {output_dir}")
            return 1
        if name == "agent_evidence":
            try:
                evidence = evidence_file(output_dir / "phase15" / "trials")
            except ValueError as exc:
                log_path = logs_dir / "agent_evidence_gate.log"
                log_path.write_text(f"ERROR: {exc}\n", encoding="utf-8")
                gate_record = stage_record("agent_evidence_gate", [], log_path)
                complete_stage(gate_record, 1)
                manifest["stages"].append(gate_record)
                manifest["status"] = "failed"
                manifest["completed_utc"] = utc_now()
                write_manifest(manifest_path, manifest)
                return 1
            if not run_evidence_gate(args, evidence, logs_dir, manifest, manifest_path):
                manifest["status"] = "failed"
                manifest["completed_utc"] = utc_now()
                write_manifest(manifest_path, manifest)
                print(f"agent evidence gate failed; retained evidence in {output_dir}")
                return 1

    manifest["status"] = "passed"
    manifest["completed_utc"] = utc_now()
    write_manifest(manifest_path, manifest)
    print(f"Live evidence passed: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
