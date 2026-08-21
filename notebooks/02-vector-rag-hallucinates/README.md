[< Back to the workshop README](../../README.md)

# Module 2: Vector RAG Hallucinates

This module compares two agents that answer the same four questions from the same hotel data. The vector agent retrieves the most similar text chunks. The graph agent translates each question into Cypher and queries Neo4j. Both agents use the same model, so the tests focus on how each retrieval method affects the answer.

Vector search can only use the chunks it retrieves. Questions that require a calculation across the full dataset need a retrieval method that can access and compute over every matching record.

**What this module shows**

- **Calculations:** Vector retrieval provides a sample of relevant chunks. Neo4j can calculate results across all matching records.
- **Neo4j access:** Both agents read the graph restored during Setup, including the five hotels added in Module 1.
- **AWS services:** Claude on Amazon Bedrock powers both agents. Amazon Nova creates the query embeddings for vector search.
- **Graph changes:** This module reads the graph and does not change it.

---

## The notebook

| Notebook | What it demonstrates |
|---|---|
| [`2.1_vector_rag_hallucinates.ipynb`](2.1_vector_rag_hallucinates.ipynb) | How vector and graph retrieval handle aggregation, counting, multiple criteria, and missing data |

## The four tests

| Test | Question | Vector agent | Graph agent |
|---|---|---|---|
| Aggregation | "Average guest rating in Paris?" | Reasons from three retrieved chunks | Runs `AVG()` over every matching hotel |
| Counting | "How many hotels have a pool?" | Reasons from three retrieved chunks | Runs `COUNT()` over every matching hotel |
| Multiple criteria | "Cairo hotels with a spa **and** a pool?" | Ranks chunks by similarity | Traverses `Hotel → Amenity` relationships and applies every condition |
| No matching data | "Hotels in Antarctica?" | Returns the nearest chunks, even when they are irrelevant | Returns an empty query result |

The first three tests use relevant source text that covers only part of the data needed for the answer. The final test shows that vector search still returns nearest neighbors when the dataset has no relevant records.

## Files in this folder

| File | Purpose |
|---|---|
| `2.1_vector_rag_hallucinates.ipynb` | The module notebook |
| `hotel-faqs.zip` | The source corpus stored with the workshop |
| `faqs_docs.json` | The chunked corpus the FAISS baseline reads |
| `faqs_vector.index` | The pre-built FAISS index for the vector agent |
| `graph_builder.py` | The extraction pipeline shared with Module 1 |
| `graph_config.py` | Schema, model IDs, and corpus selection |
| `prepare_graph.py` | Prepares the graph for this module when you run the workshop outside the hosted environment |

## The workshop page

`workshop-content/content/02-vector-rag-hallucinates/index.en.md`
