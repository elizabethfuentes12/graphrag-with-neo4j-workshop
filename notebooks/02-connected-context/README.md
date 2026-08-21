[< Back to the workshop README](../../README.md)

# Module 2: From Similarity Search to Connected Context

Use semantic search to find the right source, then traverse the graph to return
compact, connected facts with provenance. The notebook compares retrieval
evidence directly, so its lessons do not depend on one generated answer.

**At a Glance**

- **What it demonstrates:** semantic retrieval, exact-term retrieval,
  graph-enriched retrieval, and structured filtering.
- **Neo4j:** reads the `hotel_chunk_embeddings` and `hotel_chunk_fulltext`
  indexes plus connected hotel entities.
- **AWS:** Amazon Nova creates query embeddings. Amazon Bedrock supports the
  optional Text2Cypher example.
- **Graph changes:** the notebook reads the prepared graph and does not change
  it.

---

## The notebook

| Notebook | What it demonstrates |
|---|---|
| [`2.1_connected_context.ipynb`](2.1_connected_context.ipynb) | Compares vector, hybrid, Vector-Cypher, and structured retrieval evidence |

Run `prepare_graph.py --mode lite` from this directory before the notebook when
you need to create or repair the deterministic workshop graph.

## Files in this folder

| File | Purpose |
|---|---|
| `2.1_connected_context.ipynb` | The module notebook |
| `hotel-faqs.zip` | The source corpus stored with the workshop |
| `faqs_docs.json` | The corpus metadata retained for the historical FAISS baseline |
| `faqs_vector.index` | The index retained for the historical FAISS baseline |
| `faqs_vector.manifest.json` | The compatibility contract for the FAISS artifacts |
| `graph_builder.py` | The extraction pipeline shared with Module 1 |
| `graph_config.py` | Chunking and deterministic corpus selection |
| `prepare_graph.py` | Prepares the graph for this module when you run the workshop outside the hosted environment |
| `rebuild_faiss_index.py` | Rebuilds the historical FAISS artifacts from graph embeddings |

## The workshop page

`workshop-content/content/02-connected-context/index.en.md`
