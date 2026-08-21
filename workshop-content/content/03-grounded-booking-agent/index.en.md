---
title: "Module 3: Build the Grounded Booking Agent"
weight: 40
---

Module 2 compared retrieval patterns and selected a fixed Hybrid-Cypher path for
the application. Module 3 applies that path in a grounded agent and keeps the
reservation write behind a reviewed command.

Open `notebooks/03-grounded-booking-agent/3.1_grounded_booking_agent.ipynb`.

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
