---
title: "Summary"
weight: 80
---

## The One Mechanism

Vector search finds text that looks relevant. Graph traversal returns facts that are actually connected. Every module in this workshop is one consequence of that difference.

An agent handed a paragraph can round a rating down, count the chunks it happened to receive, or read "subject to availability" as a yes. An agent handed `guest_rating: 4.5` and an amenity list built from `OFFERS_AMENITY` edges can do none of those things, and when the graph holds no edge at all it has nothing to summarize, so it says so.

---

## What Each Module Proved

| Module | The claim | How you saw it |
|---|---|---|
| **1. Build the Graph** | Extraction is only queryable if the schema was pinned when the data was written | You extracted five held-out documents under the same pinned schema as the rest of the corpus, then created both retrieval indexes against your own vectors |
| **2. Vector RAG Hallucinates** | Similarity is not reasoning | Two agents, one dataset, four questions that top-k retrieval cannot answer |
| **3. Retrieval Patterns** | The retriever is a design decision, not a default | Four retrievers on the same graph, then a booking agent that abstains and writes inside one transaction |
| **4. Production Agent** | Tools and memory move out of the notebook without changing the agent | Retrieval behind an :link[AgentCore]{href="https://aws.amazon.com/bedrock/agentcore/" external=true} Gateway over IAM-authenticated MCP, plus managed cross-session memory |
| **5. Deploy to AgentCore Runtime** | The same agent runs as a service | The agent containerized, launched on Runtime, and one request correlated end to end |
| **6. Inspectable Neo4j Memory** | Memory you cannot audit is memory you cannot correct | A preference traced back to its source message and forward to the real `Hotel` node, then corrected with a single `SET` |

---

## The Evidence

| Query type | Vector RAG | GraphRAG |
|---|---|---|
| Aggregation ("average guest rating in Paris") | Estimated from the retrieved chunks | `AVG()` across every matching hotel |
| Counting ("hotels with a pool") | Undercounted the retrieved chunks | `COUNT()` on the full graph |
| Multi-hop ("Cairo hotels with a spa **and** a pool") | Partial match on similarity | Traversed `Hotel → Amenity` for both |
| Out-of-domain ("hotels in Antarctica") | Fabricated from lookalike documents | Empty result, and an honest refusal |

The failure in the left column is not a prompt problem. No system prompt reliably stops a model from summarizing text it was handed, because summarizing text it was handed is the job it was given.

---

## Choosing a Retriever

| Question shape | Retriever | Why |
|---|---|---|
| Paraphrased, semantic | `VectorRetriever` | Nothing exact to match on |
| Exact name, identifier, postal code | `HybridRetriever` | Embeddings blur short exact strings; the full-text arm holds them |
| Semantic entry, connected answer | `VectorCypherRetriever` | Reviewed traversal turns matched text into named fields |
| Counts and aggregations | `Text2CypherRetriever` | The database computes over the whole matching set |

`HybridCypherRetriever` is the one the workshop ships to production, behind `search_hotel_knowledge` in `workshop/hybrid_retrieval.py`. It takes a single `query` argument. There is no ranker, alpha, or top-k parameter for a caller to set, because those comparisons were made once, by you, and a request does not get to re-run them.

:::alert{type="warning" header="Model-generated Cypher"}
`Text2CypherRetriever` executes Cypher a model wrote. In production it goes behind a read-only user and a read-only IAM policy, never on the path that writes.
:::

---

## Choosing a Memory Store

| | AgentCore Memory | Neo4j graph memory |
|---|---|---|
| How it is written | Managed extraction from the transcript | Explicit application writes |
| When it is recallable | After asynchronous extraction | Immediately |
| Auditability | Retrieved through a service API | A Cypher query returning the source message |
| Correcting a wrong record | Delete and re-extract | `SET` on one property |
| Link to domain data | Separate from it | An edge to the real `Hotel` node |
| Operations | AWS runs it | You run it |

Neither one is the answer. Managed extraction is the cheaper path to a working prototype, and a preference you cannot trace is a preference you cannot defend to the person it is wrong about. Production systems usually run both: managed memory for recency, graph memory for the facts that have to be explainable.

---

## What to Take With You

Three pieces of this repository port to another domain without being rewritten\:

- **The pinned extraction schema** in `notebooks/01-build-graph/1.1_build_graph.ipynb`. Swap the node labels and relationship types for your own entities; the argument for pinning them does not change.
- **The retrieval contract** in `notebooks/workshop/retrieval_contract.py` and `workshop/hybrid_retrieval.py`. One function, one argument, a fixed return shape. That shape is what makes the tool safe to hand to a model.
- **The grounded write** in `notebooks/03-retrieval-patterns/reservation_command.py`. Rule check and write in the same transaction, keyed on a `request_id` so a replay is a no-op rather than a second booking.

## Next

Head to [Wrap-up](../wrap-up/).
