---
title: "Module 2: From Similarity Search to Connected Context"
weight: 30
---

## Compare Retrieval Evidence

Use semantic search to find a relevant source, then use graph structure to return
connected facts as named fields. This module compares retrieval evidence before
any optional answer generation.

Open `notebooks/02-connected-context/2.1_connected_context.ipynb`.

:image[Decision tree for selecting a Neo4j retrieval pattern by query shape]{src="../../images/02-retrieval-decision-tree.png" width=800}

| Retriever | Best for | Contribution |
|-----------|----------|--------------|
| `VectorRetriever` | Paraphrased questions | Semantic relevance |
| `HybridRetriever` | Names, identifiers, and postal codes | Semantic and exact-term relevance |
| `VectorCypherRetriever` | Semantic lookup with connected context | Semantic entry plus graph expansion |
| `Text2CypherRetriever` | Flexible structured questions | Database filtering over named fields and relationships |

## Prepare the Graph

The notebook verifies its graph fixtures and both retrieval indexes before it
constructs a retriever. If preparation is required, run `prepare_graph.py` from
`notebooks/02-connected-context/`.

## Semantic and Exact-Term Retrieval

Vector retrieval finds source text with similar meaning. Hybrid retrieval adds a
full-text signal for exact identifiers such as `60611`. Compare the ranked
evidence, source text, and scores returned by each pattern.

## Connected Graph Context

Vector-Cypher retrieval starts from a semantic Chunk match and follows reviewed
relationships to return the connected hotel and its named fields. Compare field
coverage, provenance, and context size with the source-only result.

:::alert{type="info" header="Extraction defines the graph result"}
Graph enrichment reflects the facts that the extraction pipeline placed in the
graph. Source provenance remains visible so you can inspect omissions or merges.
:::

## Structured Filtering

Structured retrieval lets Neo4j apply filters over connected fields and
relationships. The notebook displays the query and returned records so the
selection mechanism remains visible.

## Next

Head to [Module 3](../03-grounded-booking-agent/).
