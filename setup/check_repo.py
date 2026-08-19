# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Static checks that need no AWS account and no Neo4j instance.

Every check here is one that has already caught a real defect in this repository,
and every one runs offline in a couple of seconds. That is the whole selection
rule. Checks that would need credentials belong in a smoke test, and checks that
would need a live graph belong in the readiness report inside the build.

Deliberately not included: asserting that every filesystem path named in prose
exists, and sweeping for banned wording. Both are valuable and both are several
times the size of everything below, so they were left out until the maintenance
burden justifies them.

Run from anywhere:

    python setup/check_repo.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = REPO_ROOT / "notebooks"
CONTENT = REPO_ROOT / "workshop-content" / "content"

# Cells beginning with a shell escape or a line magic are not Python and never
# parse. Cells using top-level `await` are valid in ipykernel but not in
# `ast.parse`, so they are retried wrapped in a coroutine.
NON_PYTHON_PREFIXES = ("!", "%")


def notebook_cells_parse() -> list[str]:
    """Every code cell in every module notebook must be parseable Python."""
    problems: list[str] = []
    for path in sorted(NOTEBOOKS.glob("*/[0-9]*.ipynb")):
        cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
        for index, cell in enumerate(cells):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            if not source.strip() or source.lstrip().startswith(NON_PYTHON_PREFIXES):
                continue
            try:
                ast.parse(source)
            except SyntaxError:
                indented = "\n".join(
                    f"    {line}" for line in source.splitlines()
                )
                try:
                    ast.parse(f"async def _wrapper():\n{indented}")
                except SyntaxError as exc:
                    rel = path.relative_to(REPO_ROOT)
                    problems.append(f"{rel} cell {index} does not parse: {exc.msg}")
    return problems


def python_files_compile() -> list[str]:
    """Every tracked .py file must byte-compile."""
    problems: list[str] = []
    for path in sorted(REPO_ROOT.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            problems.append(f"{path.relative_to(REPO_ROOT)} does not compile: {exc.msg}")
    return problems


def contracts_import_without_neo4j() -> list[str]:
    """`import workshop.contracts` must succeed with the Neo4j environment unset.

    A module that raises at import time when a credential is missing makes itself
    unimportable to the reservation Lambda and to anything running offline, and
    turns a missing variable into an ImportError from several modules away.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("NEO4J_")}
    env["PYTHONPATH"] = str(NOTEBOOKS)
    result = subprocess.run(
        [sys.executable, "-c", "import workshop.contracts, workshop.aws_region"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        tail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "?"
        return [f"workshop.contracts does not import with Neo4j env unset: {tail}"]
    return []


LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")
SRC_PATTERN = re.compile(r'src="([^"]+)"')


def content_references_resolve() -> list[str]:
    """Every relative markdown link and image src in the content tree must exist."""
    problems: list[str] = []
    for path in sorted(CONTENT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        targets = LINK_PATTERN.findall(text) + SRC_PATTERN.findall(text)
        for target in targets:
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                rel = path.relative_to(REPO_ROOT)
                problems.append(f"{rel} references missing path: {target}")
    return problems


WEIGHT_PATTERN = re.compile(r"^weight:\s*(\d+)\s*$", re.MULTILINE)


def content_weights_unique() -> list[str]:
    """Two pages sharing a weight order unpredictably in Workshop Studio."""
    problems: list[str] = []
    seen: dict[int, str] = {}
    for path in sorted(CONTENT.glob("*/index.en.md")):
        match = WEIGHT_PATTERN.search(path.read_text(encoding="utf-8"))
        if match is None:
            problems.append(f"{path.relative_to(REPO_ROOT)} has no weight in its frontmatter")
            continue
        weight = int(match.group(1))
        folder = path.parent.name
        if weight in seen:
            problems.append(f"weight {weight} is used by both {seen[weight]} and {folder}")
        else:
            seen[weight] = folder
    return problems


def module_folders_have_pages() -> list[str]:
    """Every numbered notebook folder needs a content page of the same name.

    Only in that direction. The content tree also carries setup, summary, wrap-up
    and cleanup pages, and none of those has a notebook.
    """
    problems: list[str] = []
    for path in sorted(NOTEBOOKS.glob("[0-9]*/")):
        if not (CONTENT / path.name).is_dir():
            problems.append(f"notebooks/{path.name} has no page at content/{path.name}")
    return problems


CHECKS = (
    ("notebook code cells parse", notebook_cells_parse),
    ("python files compile", python_files_compile),
    ("workshop.contracts imports offline", contracts_import_without_neo4j),
    ("content references resolve", content_references_resolve),
    ("content weights are unique", content_weights_unique),
    ("module folders have content pages", module_folders_have_pages),
)


def main() -> int:
    failures = 0
    for name, check in CHECKS:
        problems = check()
        if problems:
            failures += len(problems)
            print(f"FAIL  {name}")
            for problem in problems:
                print(f"        {problem}")
        else:
            print(f"ok    {name}")
    print()
    if failures:
        print(f"{failures} problem(s) found.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
