# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Neo4j connection settings shared by every lab that opens a driver.

`NEO4J_USERNAME` defaults to `"neo4j"`, which is what Aura provisions; the older
`NEO4J_USER` spelling is not read. There is no default for `NEO4J_URI` or for
`NEO4J_PASSWORD`. Both are required, and a missing value raises at import rather
than failing later and somewhere else: a baked-in default password sends a bad
credential to the right host, and a baked-in `bolt://127.0.0.1:7687` sends a good
credential to a host that is not listening, which surfaces as a connection
timeout that reads like an Aura outage.

That import-time raise is why this module is separate from `contracts` and from
`graph_schema`. Importing either of those must stay free of environment
requirements so the reservation Lambda and the offline tests can load them
without credentials.
"""

import os

NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")

# Defaulted to "" rather than left as None so both stay `str` for every caller
# below the raise, which the raise guarantees they reach only when set.
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

_MISSING = [
    name
    for name, value in (("NEO4J_URI", NEO4J_URI), ("NEO4J_PASSWORD", NEO4J_PASSWORD))
    if not value
]
if _MISSING:
    raise RuntimeError(
        f"Missing required Neo4j environment values: {', '.join(_MISSING)}. "
        "Set them (see .env.example) before running the workshop labs. Neither "
        "has a default, so a missing one fails loudly here instead of sending a "
        "bad credential to Neo4j or a good one to a localhost that is not "
        "listening."
    )


def neo4j_auth() -> tuple[str, str]:
    """Return the (username, password) pair for the Neo4j driver."""
    return NEO4J_USERNAME, NEO4J_PASSWORD
