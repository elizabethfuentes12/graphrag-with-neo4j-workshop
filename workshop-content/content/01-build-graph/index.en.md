---
title: "Module 1: Build the Graph"
weight: 20
---

## From Documents to a Typed Graph

You are going to hand five hotel FAQ documents to Claude on :link[Amazon Bedrock]{href="https://aws.amazon.com/bedrock/" external=true} and watch it turn unstructured text into a queryable knowledge graph. `SimpleKGPipeline` from the :link[neo4j-graphrag]{href="https://neo4j.com/docs/neo4j-graphrag-python/current/" external=true} package reads each document, splits it into chunks, embeds them, and extracts typed nodes and relationships.

The five hotels you build are not in the graph you restored during Setup. They join it permanently, and you query them for the rest of the workshop.

:::alert{type="info" header="Your work stays"}
Nothing in this module gets deleted afterwards. There is no cleanup step, no run identifier, and no explanation of why your hotels vanished, because they do not.
:::

---

## The Trade, Said Out Loud

You extract five documents. The rest of the corpus arrived prebuilt in the dump, extracted under this same pinned schema, because extracting all of it means watching a progress bar instead of learning something.

Your five are real, they are yours, and every aggregation and multi-hop question in the modules that follow runs across the whole graph, including them.

---

## Why the Schema Is Pinned

`SimpleKGPipeline` will extract without a schema. Left to itself, the LLM invents a fresh vocabulary for every chunk\: one document yields an `Address` node, the next puts the address on a `Location`, a third calls it a `City`. Each result looks reasonable alone. Together they are unqueryable, because no single Cypher pattern matches all of them.

The pinned schema constrains extraction to one vocabulary\:

:::code{language=text}
(:Hotel)-[:HAS_ROOM]->(:Room)
(:Hotel)-[:OFFERS_AMENITY]->(:Amenity)
(:Hotel)-[:HAS_POLICY]->(:Policy)
(:Hotel)-[:PROVIDES_SERVICE]->(:Service)
:::

Every later module depends on this. Module 3's retrieval tool promises the agent that a hotel carries `name`, `address`, and `guest_rating` on the node itself. That promise is only keepable if extraction was constrained when the data was written.

The notebook includes an optional cell that extracts one document with no schema pinned and prints the labels it invents. Run it if you would rather see the problem than read about it.

---

## Retrieval Indexes

The dump deliberately ships without the vector index and the full-text index. This module creates both, so they are built against the vectors your own extraction just wrote\:

| Index | Type | What reads it |
|-------|------|---------------|
| `hotel_chunk_embeddings` | Vector, cosine similarity | Vector and hybrid retrievers in Module 3 |
| `hotel_chunk_fulltext` | Full-text on `Chunk.text` | The keyword half of hybrid retrieval |

The three uniqueness constraints already ship in the dump. This notebook does not touch them — the one Module 3's duplicate-request check depends on is verified there, not here.

---

## Run It

Open `notebooks/01-build-graph/1.1_build_graph.ipynb` and run the cells in order.

:::alert{type="warning" header="If a document fails"}
Extraction calls can be throttled. The build retries automatically, and the cell is safe to re-run\: it clears only your five documents before trying again, so the rest of the graph is never touched.
:::

At the end the notebook prints the document and hotel counts before and after your build, and lists the hotels you extracted with their addresses, ratings, and amenity counts.

---

## Before Module 2: Agent Basics

The notebook closes with a short reading section on the :link[Strands Agents SDK]{href="https://strandsagents.com/" external=true}, because Module 2 builds two agents in its first few cells. It covers what an `Agent` is, why the `BedrockModel` is pinned to a specific model ID, and what the `@tool` decorator does to a Python function.

The idea to carry forward\: an agent is only as grounded as its tools. A tool that returns plausible text for a question it cannot actually answer produces a confident wrong answer, and no system prompt reliably prevents that. Module 2 shows exactly that failure, then fixes it.

## Next

Head to [Module 2](../02-vector-rag-hallucinates/).
