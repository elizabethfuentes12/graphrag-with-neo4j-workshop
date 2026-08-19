# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Make the setup scripts importable by the tests that sit beside them.

`setup/` is a directory of scripts rather than a package, so the tests import
`check_repo`, `verify_setup`, and `run_notebooks` by name. The shared
`workshop` package is added the same way the scripts and notebooks add it, so a
test can import a fixture constant without an installed distribution.
"""

from __future__ import annotations

import sys
from pathlib import Path

SETUP_DIR = Path(__file__).resolve().parent
REPO_ROOT = SETUP_DIR.parent
NOTEBOOKS = REPO_ROOT / "notebooks"

for entry in (SETUP_DIR, NOTEBOOKS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
