# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Modules shared by more than one workshop lab.

Import submodules directly, for example::

    from workshop.contracts import MAX_GUESTS
    from workshop.graph_connection import NEO4J_URI, neo4j_auth

This package deliberately re-exports nothing. `graph_connection` raises at
import when `NEO4J_PASSWORD` is unset, and `bedrock_providers`, `graph_setup`,
`hybrid_retrieval`, and `reservation_command` all build AWS or Neo4j clients. A
convenience re-export here would drag every one of those into `import workshop`,
and `contracts` promises the reservation Lambda that it can be imported without
touching credentials or the network. Keeping this file empty of imports is what
makes that promise true.
"""
