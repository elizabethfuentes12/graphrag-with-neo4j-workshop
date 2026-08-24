# Live validation: Modules 1--3

Date: 2026-08-23 (America/Denver)

Code under test: `b1e268473de738767faf851ef2ea63972fedd932`

Environment: Neo4j Aura Enterprise 5.27, database `neo4j`, AWS Region
`us-east-1`, model `us.anthropic.claude-sonnet-5`.

The prebuilt graph started with 295 Documents, 295 Hotels, 65 Amenities, and
1,606 amenity assertions. Module 1 added the five held-out hotel sources and
the graph ended with 300 Documents, 300 Hotels, 65 Amenities, and 1,632 amenity
assertions. The post-patch full re-run held those four counts at the learner-
complete values.

| Module | Notebook | Result |
| --- | --- | --- |
| 1 | `1.1_build_graph.ipynb` | passed |
| 2 | `2.1_connected_context.ipynb` | passed |
| 3 | `3.1_grounded_booking_agent.ipynb` | passed |

The full gate reported 3 passed, 0 failed, and 0 skipped. Module 2's optional
Text2Cypher supporting check reported `passed: EXPLAIN query_type=r`. Module 3
confirmed availability abstention, rejected an over-limit guest request, and
returned an idempotent duplicate result for the repeated reservation request.

The focused Module 2 notebook contract test passed (11 tests). The full offline
suite passed 214 tests, and the repository checker passed after the live run.
