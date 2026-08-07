---
title: "Module 2: GraphRAG Fixes It"
weight: 30
---

## Four Retrieval Patterns

Open `notebooks/02_neo4j_retrieval_patterns.ipynb`.

:image[Decision tree: which Neo4j retriever to choose based on query type]{src="/static/images/02-retrieval-decision-tree.png" width=800}

| Retriever | Best for |
|-----------|----------|
| `VectorRetriever` | Paraphrased / semantic questions |
| `HybridRetriever` | Exact names and identifiers |
| `VectorCypherRetriever` | Semantic entry + connected graph context |
| `Text2CypherRetriever` | Counts and aggregations |

### Pattern 2: HybridRetriever

`alpha=0.2` (80% fulltext, 20% vector) surfaces an exact hotel name that ranks 12th with vector-only search. Try it.

:::alert{type="warning" header="Text2CypherRetriever in production"}
It runs LLM-generated Cypher directly. Always route through a read-only gateway. Part 2 uses a fixed `HybridCypherRetriever` — no model-generated Cypher touches the write path.
:::

---

## Part 2 — Grounded Booking Agent

Open `notebooks/03_hybrid_retrieval.ipynb`.

:image[HybridCypherRetriever grounds the agent; business rules are enforced inside the write transaction]{src="/static/images/02-grounded-agent-architecture.png" width=800}

### Query 1: Hero question

> **"What amenities and guest rating does AnyCompany Cairo Nile View have?"**

### Query 2: Does the hotel guarantee availability next weekend?

> **"Does AnyCompany Cairo Nile View guarantee room availability next weekend?"**

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

Re-submit the same reservation. One node, two deliveries, zero duplicates.

## Next

Head to [Module 3](../03-production-agent/).
