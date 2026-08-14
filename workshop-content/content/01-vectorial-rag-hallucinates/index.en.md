---
title: "Module 1: Vectorial RAG Hallucinates"
weight: 20
---

## Why Vectorial RAG Gets the Wrong Answer

Traditional RAG retrieves the top-k most similar document chunks and hands them to an LLM to answer. This works for narrative questions but fails on four specific query types:

:image[Vector RAG retrieves 3 chunks and the LLM guesses; Graph-RAG computes exact results from all data]{src="../../images/01-rag-vs-graphrag-problem.png" width=800}

| Failure mode | Query example | What RAG does | What should happen |
|---|---|---|---|
| **Aggregation** | "Average guest rating in Paris?" | LLM estimates from 3 chunks | `AVG()` across all hotels |
| **Counting** | "How many hotels have a pool?" | LLM counts 3 docs, misses 293 | `COUNT()` on the full graph |
| **Multi-hop** | "Cairo hotels with spa AND pool?" | Vector similarity, partial match | Traverse Hotel → Amenity → Amenity |
| **Out-of-domain** | "Hotels in Antarctica?" | Returns similar docs, LLM fabricates | Empty result, honest "no data" |

---

## Two Agents, One Dataset

Open `notebooks/01_graphrag_vs_rag.ipynb`.

:image[Architecture: FAISS vector search and Neo4j graph as two parallel retrieval paths over the same 300 hotel documents]{src="../../images/01-rag-vs-graphrag-architecture.png" width=800}

| Agent | Retrieval |
|-------|-----------|
| RAG Agent | FAISS vector similarity → top-3 chunks |
| Graph-RAG Agent | Text2Cypher → :link[Neo4j]{href="https://neo4j.com/" external=true} executes |

:::alert{type="info" header="FAISS index pre-built"}
The workshop environment includes a pre-built FAISS index — skip the data-loading step and run the tests directly.
:::

---

## Test 1: Aggregation

**Query:** "What is the average guest rating of all hotels in Paris?"

Run both agents and compare their outputs. The RAG agent reads three document chunks and generates an estimate from partial data. The Graph-RAG agent executes the following Cypher query across all hotels instead\:

:::code{language=cypher}
MATCH (h:Hotel) WHERE h.address CONTAINS 'Paris'
RETURN avg(h.guestRating) AS avg_rating
:::

---

## Test 2: Counting

**Query:** "How many hotels in the database have a swimming pool?"

Run both agents. The RAG agent counts occurrences across the three retrieved chunks and returns an undercount. The Graph-RAG agent executes a `COUNT()` query across all 296 hotels in the knowledge graph and returns the exact number.

---

## Test 3: Multi-Hop

**Query:** "Which hotels in Cairo have both a spa and a swimming pool?"

Run both agents. The RAG agent relies on semantic similarity and may miss hotels that lack an explicit combined keyword mention in their documents. The Graph-RAG agent traverses the graph from each Hotel node through its Amenity relationships and returns only the hotels connected to both amenity types.

---

## Test 4: Out-of-Domain

**Query:** "Tell me about hotels in Antarctica."

:::alert{type="warning" header="Watch the RAG agent"}
It will return results from similar-looking documents and the LLM may fabricate details. Graph-RAG returns `No results found.`
:::

## Next

Head to [Module 2](../02-graphrag-fixes-it/).
