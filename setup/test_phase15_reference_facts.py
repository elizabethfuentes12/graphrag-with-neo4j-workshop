# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Offline recheck of Phase 1.5 facts affected by amenity handling."""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

PHASE15_DIR = Path(__file__).resolve().parent / "phase15"
if str(PHASE15_DIR) not in sys.path:
    sys.path.insert(0, str(PHASE15_DIR))

from reference_facts import source_facts

CORPUS_ARCHIVE = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "02-connected-context"
    / "hotel-faqs.zip"
)


def test_amenity_reference_facts_reproduce_the_committed_corpus() -> None:
    with ZipFile(CORPUS_ARCHIVE) as corpus:
        documents = [
            {
                "filename": filename,
                "text": corpus.read(filename).decode("utf-8"),
            }
            for filename in corpus.namelist()
            if filename.endswith(".txt")
        ]

    facts = source_facts(documents)

    assert facts["document_count"] == 300
    assert facts["amenity_inventory"] == {
        "assertions": 1_632,
        "distinct_names": 65,
    }
    assert facts["pool"] == {
        "listed_in_amenities": 175,
        "explicitly_unavailable": 125,
        "overlap": 0,
        "sum": 300,
    }
    assert facts["chicago"]["candidates"] == 2
    assert facts["chicago"]["matches"] == 1
    assert facts["chicago_shared_amenities"]["hotels"] == 2
    assert (
        "Complimentary High-Speed Wifi" in facts["chicago_shared_amenities"]["shared"]
    )
