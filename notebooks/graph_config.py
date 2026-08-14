# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Build-time settings that belong to Lab 1 alone.

Chunk sizing, the extraction token ceiling, and the lite document sample only
matter while the graph is being built, so they stay here rather than in the
shared `workshop` package. The things later labs also need moved out:

* the pinned extraction schema is `workshop.graph_schema`
* the Neo4j connection is `workshop.graph_connection`
* the embedding and index names are `workshop.retrieval_contract`

Import those from `workshop` directly. This module deliberately does not
re-export them, so there is one obvious place each name comes from.
"""

from collections import defaultdict
from pathlib import Path

# Source documents top out at ~7.4 KB. A chunk this size keeps each hotel in a
# single chunk, so the hotel's name, address and rating are extracted together
# with its rooms and amenities instead of being split across two prompts.
CHUNK_SIZE = 12000
CHUNK_OVERLAP = 0

# A whole hotel in one chunk produces a large extraction payload. The 4096
# default truncates the JSON mid-object and the chunk is dropped.
EXTRACTION_MAX_TOKENS = 16000


# ---------------------------------------------------------------------------
# Document selection
# ---------------------------------------------------------------------------

# Lab 2 asks about Paris and Cairo by name, so the lite sample has to contain
# them. `sorted(...)[:30]` is alphabetical and stops at Boston.
REQUIRED_CITIES = ("paris", "cairo")


def _city_of(filename: str) -> str:
    """Extract the city from a `hotel-<city>-<nnn>.txt` filename."""
    parts = Path(filename).stem.split("-")
    return "-".join(parts[1:-1]) if len(parts) > 2 else Path(filename).stem


def select_lite_files(data_dir: str | Path, max_docs: int) -> list[str]:
    """Return a city-stratified sample of `max_docs` FAQ filenames.

    Every document for each city in `REQUIRED_CITIES` comes first, so the
    Paris average and the Cairo multi-hop query have more than one hotel to
    work with. The remainder is filled round-robin across the other cities
    rather than alphabetically, so the sample spans the corpus.
    """
    by_city: dict[str, list[str]] = defaultdict(list)
    for path in sorted(Path(data_dir).glob("*.txt")):
        by_city[_city_of(path.name)].append(path.name)

    picked = [name for city in REQUIRED_CITIES for name in by_city.get(city, [])]
    others = [city for city in sorted(by_city) if city not in REQUIRED_CITIES]

    depth = max((len(names) for names in by_city.values()), default=0)
    for i in range(depth):
        for city in others:
            if len(picked) >= max_docs:
                return picked[:max_docs]
            names = by_city[city]
            if i < len(names):
                picked.append(names[i])

    return picked[:max_docs]
