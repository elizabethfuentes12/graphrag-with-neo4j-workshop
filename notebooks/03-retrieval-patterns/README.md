[< Back to the workshop README](../../README.md)

# Module 3: Retrieval Patterns and the Grounded Booking Agent

Four Neo4j retrievers run against the graph Module 1 built, so the choice between them is made by watching them rather than by reading a table. Then one of the four is handed to an agent, along with a write path that checks its rules inside the same transaction that would do the writing.

**The mechanism, in one sentence: vector search finds candidates, reviewed traversal turns them into named fields, and a field is the only thing safe to hand to a write path.**

**At a Glance**
- **Failure it stops:** a retriever chosen by default rather than by question shape; an agent that reads "subject to availability" as a yes; and a booking that gets written twice because the participant clicked twice.
- **Neo4j:** reads through the `hotel_chunk_embeddings` and `hotel_chunk_fulltext` indexes; writes one workshop-owned `ReservationRequest` node behind a uniqueness constraint on `request_id`.
- **AWS:** Claude on Amazon Bedrock reasons and writes the Cypher in the Text2Cypher pattern; Amazon Nova embeds each query.
- **You'll build:** `ReservationRequest` nodes. Nothing else in the graph is modified, and no hotel data is touched.

---

## The two notebooks

| Notebook | What it proves |
|---|---|
| [`3.1_retrieval_patterns.ipynb`](3.1_retrieval_patterns.ipynb) | Four retrievers on one graph. Each is best at a question shape the other three handle worse |
| [`3.2_grounded_booking_agent.ipynb`](3.2_grounded_booking_agent.ipynb) | An agent that answers from returned fields, abstains when the graph is silent, and cannot double-book |

Run `3.1` first. `3.2` uses the retriever `3.1` argues for.

## Choosing a retriever

| Retriever | Best for | Why |
|---|---|---|
| `VectorRetriever` | Paraphrased, semantic questions | Nothing exact to match on |
| `HybridRetriever` | Exact names, identifiers, postal codes | Embeddings blur short exact strings; the full-text arm holds them |
| `VectorCypherRetriever` | Semantic entry, connected answer | The traversal returns named fields instead of paragraphs |
| `Text2CypherRetriever` | Counts and aggregations | The database computes over the whole matching set |

`HybridRetriever` with `alpha=0.2` weights the full-text arm at 0.8. That is a tuned setting, not a default, and the notebook says so on screen before it shows the result. It surfaces an exact hotel name that pure vector search ranks well down the list.

`Text2CypherRetriever` executes Cypher a model wrote. It stays on the read path, behind a read-only user and a read-only IAM policy in production, and it never touches the path that writes. Part 2 uses a fixed `HybridCypherRetriever` for exactly that reason.

## The write is the point of Part 2

`reservation_command.py` is a narrow, idempotent command. It reads one enabled rule from the graph, matches one hotel, and writes one `ReservationRequest`. It does not book a room, change hotel data, or implement payment, confirmation, or cancellation.

Two behaviours are demonstrated and both are enforced by the database rather than by the prompt:

- **A reservation over the guest limit is rejected.** The rule check runs inside the same transaction as the potential write, so nothing is written on the failing path.
- **A replayed `request_id` returns `duplicate: true`.** The uniqueness constraint is what makes that true, not a check the agent remembered to run.

## Files in this folder

| File | Purpose |
|---|---|
| `3.1_retrieval_patterns.ipynb` | The four retrievers |
| `3.2_grounded_booking_agent.ipynb` | The grounded agent and the safe write |
| `reservation_command.py` | The reservation command, also the payload Module 4's tooling is shaped around |

The production retriever itself is not built inline. It lives in `workshop/hybrid_retrieval.py` behind a function taking a single argument, and Modules 4 and 5 deploy that same function unchanged.

## The workshop page

`workshop-content/content/03-retrieval-patterns/index.en.md`
