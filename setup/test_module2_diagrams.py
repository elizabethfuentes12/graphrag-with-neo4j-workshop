"""Protect the active Module 2 retrieval diagram contract."""

from __future__ import annotations

import json
from pathlib import Path
import struct


REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_IMAGES = REPO_ROOT / "static" / "images"
WORKSHOP_IMAGES = REPO_ROOT / "workshop-content" / "images"
SOURCE_NAME = "02-retrieval-decision-tree.excalidraw"
EXPORT_NAME = "02-retrieval-decision-tree.png"


def _source_text() -> str:
    return (STATIC_IMAGES / SOURCE_NAME).read_text(encoding="utf-8")


def test_decision_tree_source_and_export_are_synchronized() -> None:
    """Both published image trees must contain identical editable and PNG files."""
    for name in (SOURCE_NAME, EXPORT_NAME):
        static_file = STATIC_IMAGES / name
        workshop_file = WORKSHOP_IMAGES / name
        assert static_file.is_file()
        assert workshop_file.is_file()
        assert static_file.read_bytes() == workshop_file.read_bytes()


def test_decision_tree_has_one_authoritative_editable_source() -> None:
    """The retired drawio file must not compete with the Excalidraw source."""
    for tree in (STATIC_IMAGES, WORKSHOP_IMAGES):
        assert not (tree / "02-retrieval-decision-tree.drawio").exists()
        sources = list(tree.glob("02-retrieval-decision-tree.*"))
        editable = [path for path in sources if path.suffix != ".png"]
        assert [path.name for path in editable] == [SOURCE_NAME]


def test_unsupported_retrieval_comparison_is_not_active() -> None:
    """Unsupported speed and accuracy ratings stay out of active image trees."""
    for tree in (STATIC_IMAGES, WORKSHOP_IMAGES):
        assert not (tree / "02-retrieval-patterns-comparison.png").exists()


def test_decision_tree_teaches_the_locked_retrieval_roles() -> None:
    """The editable source must state the Phase 5 teaching contract."""
    source = _source_text()
    document = json.loads(source)
    diagram_text = " ".join(
        element["text"].replace("\n", " ")
        for element in document["elements"]
        if element["type"] == "text"
    )
    required_text = (
        "VectorRetriever",
        "HybridRetriever",
        "VectorCypherRetriever",
        "Text2CypherRetriever",
        "Semantic match finds a Chunk node",
        "Reviewed traversal expands the graph",
        "Named fields include provenance",
        "Flexible structured filtering",
        "Database selection over named fields",
        "Chicago hotels with a spa and pool",
    )
    for phrase in required_text:
        assert phrase in diagram_text

    forbidden_text = (
        "Count or aggregate",
        "how many hotels have a pool",
        "Speed:",
        "Accuracy:",
    )
    for phrase in forbidden_text:
        assert phrase not in diagram_text


def test_decision_tree_uses_clean_excalidraw_styles() -> None:
    """The editable source follows the repository's Excalidraw conventions."""
    document = json.loads(_source_text())
    assert document["type"] == "excalidraw"
    assert document["version"] == 2
    assert document["appState"]["currentItemFontFamily"] == 5
    assert document["appState"]["currentItemRoughness"] == 0
    assert document["appState"]["exportBackground"] is True
    for element in document["elements"]:
        assert element["roughness"] == 0
        assert element["fillStyle"] == "solid"
        if element["type"] == "text":
            assert element["fontFamily"] == 5


def test_decision_tree_png_is_the_expected_canvas_size() -> None:
    """The checked-in export remains a 1600 by 900 PNG."""
    data = (STATIC_IMAGES / EXPORT_NAME).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (1600, 900)
