[< Back to the workshop README](../../README.md)

# Module 3: Retrieval Patterns and the Grounded Booking Agent

Compare four Neo4j retrieval patterns against the graph from Module 1. Then apply a fixed Hybrid-Cypher pattern in a grounded agent and use a protected reservation command to test a rule-enforced write.

**The retrieval path uses vector and full-text search to find candidate chunks. A reviewed Cypher traversal returns connected facts as named fields, including the stable `hotel_id` used by the reservation command.**

**At a Glance**

- **What it demonstrates:** choose a retriever by query shape, abstain when evidence cannot answer, reject requests that exceed the guest limit, and prevent duplicate writes for a retried `request_id`.
- **Neo4j:** reads through the `hotel_chunk_embeddings` and `hotel_chunk_fulltext` indexes; writes one workshop-owned `ReservationRequest` node behind a uniqueness constraint on `request_id`.
- **AWS:** Amazon Bedrock provides LLM reasoning and generates Cypher for the Text2Cypher pattern; Amazon Nova embeds each query.
- **You'll build:** one workshop-owned `ReservationRequest` node. The write path preserves the hotel data and all other graph content.

---

## The two notebooks

| Notebook | What it demonstrates |
|---|---|
| [`3.1_retrieval_patterns.ipynb`](3.1_retrieval_patterns.ipynb) | Compares four retrieval patterns and shows the query shape suited to each one |
| [`3.2_grounded_booking_agent.ipynb`](3.2_grounded_booking_agent.ipynb) | Grounds answers in returned fields, abstains when evidence is missing, enforces a guest limit, and prevents duplicate writes for the same `request_id` |

Run `3.1` first to compare the patterns. Notebook `3.2` then applies a fixed `HybridCypherRetriever`.

## Choosing a retriever

| Retriever | Best for | Why |
|---|---|---|
| `VectorRetriever` | Paraphrased, semantic questions | Finds chunks with similar meaning |
| `HybridRetriever` | Exact names, identifiers, postal codes | Combines semantic similarity with exact full-text matching |
| `VectorCypherRetriever` | Semantic entry, connected answer | Finds a chunk, then traverses relationships to return named fields |
| `Text2CypherRetriever` | Counts and aggregations | The database computes over the whole matching set |

`HybridRetriever` with `alpha=0.2` gives the full-text signal a weight of 0.8 and the vector signal a weight of 0.2. The notebook sets this value explicitly. In historical validation of the deterministic lite sample, hybrid retrieval places the exact postal code `60611` in the top five after pure vector search ranked its chunk 12th.

`Text2CypherRetriever` executes model-generated Cypher. In production, connect it with a read-only Neo4j user and expose it only through a retrieval interface. Part 2 keeps the reservation write path separate and uses a fixed `HybridCypherRetriever` for retrieval.

## The reservation command in Part 2

`reservation_command.py` is a narrow, idempotent command. It reads one enabled rule from the graph, matches one hotel, and writes one `ReservationRequest`. Room booking, hotel data changes, payment, confirmation, and cancellation are outside its scope.

The database enforces two behaviors:

- **The command rejects a reservation over the guest limit.** The rule check runs in the write transaction and blocks the `CREATE` operation.
- **A replayed `request_id` returns `duplicate: true`.** The uniqueness constraint prevents a second node for the same identifier.

## Files in this folder

| File | Purpose |
|---|---|
| `3.1_retrieval_patterns.ipynb` | The four retrievers |
| `3.2_grounded_booking_agent.ipynb` | The grounded agent and the protected reservation write |
| `reservation_command.py` | The local reservation command that Module 5 deploys with the agent |

The production retriever lives in `workshop/hybrid_retrieval.py`. It exposes a function that accepts a single argument. Modules 4 and 5 deploy that same function unchanged.

## The workshop page

`workshop-content/content/03-retrieval-patterns/index.en.md`
