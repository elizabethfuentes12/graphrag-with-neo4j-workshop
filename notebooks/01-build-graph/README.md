[< Back to the workshop README](../../README.md)

# Module 1: Build the Graph

Five hotel FAQ documents go to Claude on Amazon Bedrock, and come back as typed nodes and relationships in Neo4j. `SimpleKGPipeline` from `neo4j-graphrag` reads each document, chunks it, embeds the chunks, and extracts entities under a schema that is pinned before the first call is made. The module closes by creating the two retrieval indexes every later module queries.

**The mechanism, in one sentence: extraction is only queryable if the vocabulary was fixed before the model was allowed to invent one.**

**At a Glance**
- **Failure it stops:** a graph where one document produced an `Address` node, the next put the address on a `Location`, and no single Cypher pattern matches both.
- **Neo4j:** writes `Hotel`, `Room`, `Amenity`, `Policy`, `Service`, and `Chunk` nodes; creates the `hotel_chunk_embeddings` vector index and the `hotel_chunk_fulltext` full-text index. The three uniqueness constraints the dump already ships are untouched here; Module 3 verifies the one its duplicate-request check depends on.
- **AWS:** Claude on Amazon Bedrock does the extraction; Amazon Nova embeds each chunk.
- **You'll build:** five hotels that were deliberately held out of the shipped dump. They join the graph permanently and nothing deletes them afterwards.

---

## The notebook

| Notebook | What it proves |
|---|---|
| [`1.1_build_graph.ipynb`](1.1_build_graph.ipynb) | The same pipeline, with and without a pinned schema, produces a queryable graph and an unqueryable one |

One optional cell extracts a single document with no schema and prints the labels the model invented. It is there for anyone who would rather see the problem than read about it, and skipping it changes nothing downstream.

## Files in this folder

| File | Purpose |
|---|---|
| `1.1_build_graph.ipynb` | The module notebook |
| `held_out_documents.py` | Names the five documents held out of the dump and unpacks them from the corpus archive. The Cairo fixture hotel is deliberately not among them, because Module 3's hero question targets it and must not depend on a participant's extraction having succeeded |
| `data/` | The five held-out source documents, unpacked |

## What this module hands forward

- **The pinned schema.** Module 3's retrieval tool promises the agent that a hotel carries `name`, `address`, and `guest_rating` on the node itself. That promise is only keepable because extraction was constrained when the data was written.
- **Both indexes.** The dump ships without them on purpose, so they are built against the vectors this module's own extraction just wrote. `workshop/retrieval_setup.py` creates them and verifies the result against the retrieval contract, rather than the notebook hand-writing the Cypher.

## Reading section at the end

The notebook closes on the Strands Agents SDK, because Module 2 builds two agents in its first few cells: what an `Agent` is, why the `BedrockModel` is pinned to a specific model ID, and what `@tool` does to a Python function.

The idea to carry forward is that an agent is only as grounded as its tools. A tool that returns plausible text for a question it cannot answer produces a confident wrong answer, and no system prompt reliably prevents that.

## The workshop page

`workshop-content/content/01-build-graph/index.en.md`
