# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Idempotent self-paced preparation of the Lab 1 graph and its indexes."""

import argparse
import asyncio
import os
import sys
import zipfile
from pathlib import Path

# Add notebooks/ root to path so the workshop package can be found
sys.path.insert(0, str(Path(__file__).parent.parent))


os.environ["OTEL_SDK_DISABLED"] = "true"

from dotenv import load_dotenv

load_dotenv()

from neo4j import Driver  # noqa: E402

from graph_builder import connect, graph_database, report, run_build  # noqa: E402
from graph_config import select_lite_files  # noqa: E402
from workshop.graph_setup import (  # noqa: E402
    apply_lab4_fixtures,
    load_manifest,
    readiness_problems,
)
from workshop.retrieval_setup import (  # noqa: E402
    ReadinessError,
    ensure_retrieval_indexes,
    report_readiness,
    verify_retrieval_indexes,
)

DATA_DIR = Path("data")
CORPUS_ZIP = Path("hotel-faqs.zip")
LITE_DOCUMENTS = 30


def ensure_corpus_extracted(data_dir: Path = DATA_DIR) -> int:
    """Extract the committed corpus zip when no documents are present yet.

    `data/` is gitignored, so a fresh clone has only `hotel-faqs.zip`. The
    notebook's first cell extracts it, and the script path has to do the same
    or a participant who starts here stops at an empty directory. Returns the
    number of source documents now on disk.
    """
    extracted = sorted(data_dir.glob("*.txt"))
    if extracted or not CORPUS_ZIP.exists():
        return len(extracted)

    with zipfile.ZipFile(CORPUS_ZIP) as archive:
        archive.extractall(data_dir)
    extracted = sorted(data_dir.glob("*.txt"))
    print(f"Extracted {len(extracted)} source documents into {data_dir}/")
    return len(extracted)


def selected_paths(mode: str) -> list[Path]:
    """Return the deterministic source paths for the requested build mode."""
    if mode == "lite":
        names = select_lite_files(DATA_DIR, LITE_DOCUMENTS)
        return [DATA_DIR / name for name in names]
    return sorted(DATA_DIR.glob("*.txt"))


def lab4_problems(driver: Driver, *, apply_fixtures: bool) -> list[str]:
    """Return what still stands between this graph and Lab 4.

    Step 7 of the notebook seeds the fixture hotel IDs, the three `demo06_*`
    constraints, and the `max_guests` rule. The script path has to do the same,
    or a facilitator who builds here hands Lab 4 a graph that cannot run. The
    seed is `MERGE` and `SET` throughout, so repeating it changes nothing.
    """
    database = graph_database()
    manifest = load_manifest()
    if apply_fixtures:
        blockers = apply_lab4_fixtures(driver, database, manifest)
        if blockers:
            return blockers
    return readiness_problems(driver, database, manifest)


def seed_lab4_fixtures() -> int:
    """Apply and verify the graph-owned data Labs 4 and 5 read.

    `run_build` closes its own driver, so this opens a fresh one after the
    build and leaves the graph in the same state the notebook's step 7 does.
    """
    print("\nSeeding the fixtures Labs 4 and 5 depend on...")
    driver = connect()
    try:
        problems = lab4_problems(driver, apply_fixtures=True)
    finally:
        driver.close()

    if problems:
        print("\n❌ The graph is not ready for Lab 4:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "✅ Fixture hotel IDs, the demo06_* constraints, and the maximum-guests "
        "rule are in the graph"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and verify the Lab 1 graph and its retrieval indexes."
    )
    parser.add_argument(
        "--mode",
        choices=("lite", "full"),
        default="lite",
        help=(
            "lite builds the 30-document sample in about 15 minutes; "
            "full builds all 300 in about 2 hours. Default: lite."
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Report readiness without rebuilding an incomplete graph.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild even when the selected graph is already ready.",
    )
    args = parser.parse_args()
    if args.check_only and args.rebuild:
        # --check-only writes nothing and --rebuild discards the graph, so a
        # run carrying both used to silently honour --rebuild alone.
        parser.error(
            "--check-only and --rebuild cannot be combined: --check-only "
            "reports readiness without writing, --rebuild discards the graph "
            "and builds it again"
        )
    return args


def main() -> int:
    args = parse_args()
    ensure_corpus_extracted()
    paths = selected_paths(args.mode)
    if not paths:
        print(f"No source documents found in {DATA_DIR.resolve()}.")
        return 1

    driver = connect()
    needs_build = args.rebuild
    try:
        # The index contract is checked before the build decision, never after
        # it. An index that exists at the wrong dimension cannot serve the
        # vectors a build writes, and --rebuild used to skip this check and
        # surface the same failure fifteen minutes later.
        if args.check_only:
            problems = []
            try:
                verify_retrieval_indexes(driver)
            except ReadinessError as exc:
                problems.append(str(exc))
        else:
            try:
                ensure_retrieval_indexes(driver)
            except ReadinessError as exc:
                print(f"\n❌ {exc}")
                return 1
            problems = []

        if not args.rebuild:
            problems.extend(report_readiness(driver, expected_documents=len(paths)))
            problems.extend(
                lab4_problems(driver, apply_fixtures=not args.check_only)
            )
            needs_build = bool(problems)
            # The acceptance queries print whether or not a build runs, so a
            # ready graph still shows what Lab 2 will be asking it.
            if not problems:
                report(driver)
    finally:
        driver.close()

    if not needs_build:
        print("\n✅ Lab 1 is ready; no rebuild needed.")
        return 0
    if not args.rebuild:
        print("\nGraph preparation is incomplete:")
        for problem in problems:
            print(f"  - {problem}")
        if args.check_only:
            return 1

    title = "🚀 LITE BUILD" if args.mode == "lite" else "FULL BUILD"
    exit_code = asyncio.run(run_build(paths, title))
    if exit_code != 0:
        return exit_code
    return seed_lab4_fixtures()


if __name__ == "__main__":
    sys.exit(main())
