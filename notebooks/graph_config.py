"""Bridge module: re-exports from the workshop package for notebooks that
import graph_config directly instead of from workshop.*"""
from workshop.graph_schema import GRAPH_SCHEMA          # noqa: F401
from workshop.graph_connection import NEO4J_URI, neo4j_auth  # noqa: F401

# Also re-export build-time settings so notebooks using:
#   from graph_config import CHUNK_SIZE, CHUNK_OVERLAP
# continue to work.
from workshop.retrieval_contract import (               # noqa: F401
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PURPOSE,
)

# Build-time constants (only used in graph build notebooks)
CHUNK_SIZE = 12000
CHUNK_OVERLAP = 0
EXTRACTION_MAX_TOKENS = 16000
