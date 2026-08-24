"""Offline contract checks for the evidence-first Module 2 notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path


NOTEBOOK = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "02-connected-context"
    / "2.1_connected_context.ipynb"
)


def notebook_sources() -> tuple[str, str]:
    """Return all notebook text and executable code as stable strings."""
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    all_text = "\n".join("".join(cell["source"]) for cell in cells)
    code = "\n".join(
        "".join(cell["source"])
        for cell in cells
        if cell["cell_type"] == "code"
    )
    return all_text, code


def test_notebook_code_cells_parse() -> None:
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        ast.parse("".join(cell["source"]), filename=f"cell-{index}")


def test_locked_questions_and_evidence_fields_are_present() -> None:
    text, code = notebook_sources()
    assert (
        "When does standard arrival processing begin at "
        "AnyCompany Cairo Nile View?"
    ) in text
    assert "What is the cancellation policy for the hotel at 60611?" in text
    assert (
        "What amenities and guest rating does AnyCompany Cairo Nile View have?"
    ) in text
    assert "Which hotels in Chicago offer both a spa and a swimming pool?" in text

    for field in (
        "hotel_name",
        "hotel_id",
        "guest_rating",
        "source_filename",
        "amenities",
        "source_chunk",
        "semantic_score",
        "relationship_types",
        "field_provenance",
        "missing_requested_fields",
        "approx_context_chars",
    ):
        assert field in code


def test_notebook_consumes_shared_readiness_and_chicago_contracts() -> None:
    _, code = notebook_sources()
    for shared_name in (
        "source_fixture_problems",
        "chicago_filter_records",
        "chicago_filter_problems",
        "CHICAGO_FILTER_QUERY",
        "CHICAGO_SOURCE_FILES",
        "CHICAGO_QUALIFIER",
        "CHICAGO_EXCLUSION",
    ):
        assert shared_name in code

    assert "hotel_schema =" not in code
    assert "Tell me about the hotel at 789 Avenue" not in code


def test_cairo_vector_search_precedes_vector_cypher_comparison() -> None:
    _, code = notebook_sources()
    vector_search = code.index(
        "graph_vector_result = vector_retriever.search(\n"
        "    query_text=CAIRO_GRAPH_QUESTION"
    )
    graph_search = code.index(
        "graph_result = vector_cypher_retriever.search(\n"
        "    query_text=CAIRO_GRAPH_QUESTION"
    )
    assert vector_search < graph_search
    assert "source_filename: '(:Chunk)-[:FROM_DOCUMENT]->(:Document)'" in code


def test_database_and_optional_text2cypher_boundaries_are_visible() -> None:
    text, code = notebook_sources()
    assert code.count("neo4j_database=DATABASE") >= 3
    assert "default_access_mode=READ_ACCESS" in code
    assert "pinned_schema_text()" in code
    assert "EXPLAIN {cypher}" in code
    assert "TEXT2CYPHER_TIMEOUT_SECONDS = 15" in code
    assert "NEO4J_READ_USERNAME" in code
    assert "NEO4J_READ_PASSWORD" in code
    assert "SHOW CURRENT USER" in code
    assert "'reader' not in roles or roles & write_roles" in code
    assert "with read_driver.session(" in code
    assert "generated_cypher" in code
    assert "read_only_validation" in code
    assert "result_count" in code
    assert "execution_error" in code
    assert "Fixed Cypher remains the acceptance path" in code
    assert "read-only Neo4j user" in text


def test_module3_handoff_and_prose_style_are_explicit() -> None:
    text, code = notebook_sources()
    assert "selected_module_3_retriever = search_hotel_knowledge" in code
    assert "Selected for Module 3" in code
    assert "Result count:" in code
    assert "Candidate count:" in code
    assert "\u2014" not in text
