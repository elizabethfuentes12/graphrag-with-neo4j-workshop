---
title: "Module 2: GraphRAG Fixes It"
weight: 30
---

## Four Retrieval Patterns

This module covers four :link[Neo4j]{href="https://neo4j.com/" external=true} retrieval patterns that replace generic vector search with structured graph retrieval. Open `notebooks/02_neo4j_retrieval_patterns.ipynb` to explore each one.

:image[Decision tree: which Neo4j retriever to choose based on query type]{src="../../images/02-retrieval-decision-tree.png" width=800}

| Retriever | Best for |
|-----------|----------|
| `VectorRetriever` | Paraphrased / semantic questions |
| `HybridRetriever` | Exact names and identifiers |
| `VectorCypherRetriever` | Semantic entry + connected graph context |
| `Text2CypherRetriever` | Counts and aggregations |

### Pattern 2: HybridRetriever

With `alpha=0.2`, the retriever weights fulltext search at 80% and vector similarity at 20%. This configuration surfaces an exact hotel name that ranks 12th under pure vector search. Try adjusting `alpha` to see how the balance changes the results.

:::alert{type="warning" header="Text2CypherRetriever in production"}
It runs LLM-generated Cypher directly. Always route through a read-only gateway. Part 2 uses a fixed `HybridCypherRetriever` instead, so no model-generated Cypher reaches the write path.
:::

---

## Part 2 — Grounded Booking Agent

Open `notebooks/03_hybrid_retrieval.ipynb`.

:image[Grounded agent architecture: Neo4j enforces retrieval, rules, and writes; Amazon Bedrock handles reasoning only]{src="../../images/03-grounded-agent-architecture.png" width=800}

### Query 1: Hero question

> **"What amenities and guest rating does AnyCompany Cairo Nile View have?"**

Run this query. The `HybridCypherRetriever` finds the hotel by name using full-text search, then traverses its graph relationships to return structured facts — the amenity list and exact guest rating from the graph, not a summarized description.

### Query 2: Does the hotel guarantee availability next weekend?

> **"Does AnyCompany Cairo Nile View guarantee room availability next weekend?"**

Run this query. The agent retrieves the hotel's `guaranteedAvailability` property directly from the graph and returns the exact value, rather than inferring it from document text.

### 15-guest reservation → rejected

Submit a reservation for 15 guests (limit is 10)\:

:::code{language=json}
{
  "status": "rejected",
  "reason_code": "max_guests_exceeded",
  "max_guests": 10
}
:::

The rule check happens inside the same transaction as the potential write. Nothing is written to the graph.

### Same `request_id` replayed → `duplicate: true`

Re-submit the same reservation. Because the graph checks the `request_id` before writing, submitting the same request a second time creates no new node. The response returns `duplicate: true` and the original reservation remains unchanged.

## Next

Head to [Module 3](../03-production-agent/).
