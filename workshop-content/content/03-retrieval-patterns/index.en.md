---
title: "Module 3: Retrieval Patterns and the Grounded Booking Agent"
weight: 40
---

## Compare Four Retrieval Patterns

This module compares four :link[Neo4j]{href="https://neo4j.com/" external=true} retrieval patterns over the same hotel graph. Open `notebooks/03-retrieval-patterns/3.1_retrieval_patterns.ipynb` and run each pattern to see how it handles a different query shape.

:image[Decision tree: which Neo4j retriever to choose based on query type]{src="../../images/02-retrieval-decision-tree.png" width=800}

| Retriever | Best for |
|-----------|----------|
| `VectorRetriever` | Paraphrased or semantic questions |
| `HybridRetriever` | Exact names and identifiers |
| `VectorCypherRetriever` | Semantic lookup with connected graph context |
| `Text2CypherRetriever` | Counts and aggregations |

### Pattern 2: HybridRetriever

With `alpha=0.2`, the retriever weights full-text search at 80% and vector similarity at 20%. In historical validation of the deterministic lite sample, this configuration placed the postal code `60611` in the top five after pure vector search ranked its chunk 12th. Adjust `alpha` to see how the balance changes the results.

:::alert{type="warning" header="Text2CypherRetriever in production"}
`Text2CypherRetriever` executes model-generated Cypher. In production, connect it with a read-only Neo4j user and expose it only through a retrieval interface. Part 2 keeps generated Cypher separate from the write path by using a fixed `HybridCypherRetriever` for retrieval.
:::

---

## Part 2: Grounded Booking Agent

Open `notebooks/03-retrieval-patterns/3.2_grounded_booking_agent.ipynb`.

:image[Grounded agent architecture: Neo4j enforces retrieval, rules, and writes; Amazon Bedrock handles reasoning only]{src="../../images/03-grounded-agent-architecture.png" width=800}

### Query 1: Retrieve Amenities and a Guest Rating

> **"What amenities and guest rating does AnyCompany Cairo Nile View have?"**

Run this query. The `HybridCypherRetriever` uses full-text search to match the hotel name and vector search to match the requested meaning. It then traverses the graph relationships and returns structured facts, including the amenity list and exact guest rating.

### Query 2: Does the hotel guarantee availability next weekend?

> **"Does AnyCompany Cairo Nile View guarantee room availability next weekend?"**

Run this query. The graph has no `guaranteedAvailability` property because Neo4j holds hotel knowledge while live inventory is outside its scope. The retrieved evidence cannot confirm availability, so the agent abstains.

### Reject a 15-guest reservation

Submit a reservation for 15 guests. The maximum is 10\:

:::code{language=json}
{
  "status": "rejected",
  "reason_code": "max_guests_exceeded",
  "max_guests": 10
}
:::

The rule check runs inside the write transaction and blocks the `CREATE` operation.

### Safely Retry a Valid Request

Submit a valid reservation with a new `request_id`, then submit the same valid payload again. The first call creates one node. The second call returns `duplicate: true` with the original `created_at`. The uniqueness constraint prevents another node.

## Next

Head to [Module 4](../04-production-agent/).
