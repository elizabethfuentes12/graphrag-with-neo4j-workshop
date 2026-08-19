[< Back to the workshop README](../../README.md)

# Module 2: Vector RAG Hallucinates

Two agents answer the same four questions over the same corpus. One retrieves the top-k most similar chunks and hands them to the model. The other translates the question into Cypher and lets Neo4j compute the answer. The gap between them is the whole argument of this workshop, and it is watched rather than described.

**The mechanism, in one sentence: top-k retrieval can only summarize what it retrieved, and four common question shapes need everything it did not.**

**At a Glance**
- **Failure it stops:** an estimate presented as a computation, a count of the retrieved chunks presented as a count of the corpus, and a fabricated answer to a question the corpus has no data for.
- **Neo4j:** read-only. The graph you restored during Setup, plus the five hotels Module 1 added.
- **AWS:** Claude on Amazon Bedrock reasons for both agents, so the model is not the variable. Amazon Nova embeds the queries.
- **You'll build:** nothing in the graph. This module only reads it.

---

## The notebook

| Notebook | What it proves |
|---|---|
| [`2.1_vector_rag_hallucinates.ipynb`](2.1_vector_rag_hallucinates.ipynb) | Four question shapes where the same model, given retrieved text instead of computed facts, answers confidently and wrongly |

## The four tests

| Failure mode | The question | What vector RAG does | What the graph does |
|---|---|---|---|
| Aggregation | "Average guest rating in Paris?" | Estimates from the chunks it retrieved | `AVG()` over every matching hotel |
| Counting | "How many hotels have a pool?" | Counts the chunks it retrieved | `COUNT()` over the full graph |
| Multi-hop | "Cairo hotels with a spa **and** a pool?" | Partial match on similarity | Traverses `Hotel → Amenity` for both |
| Out-of-domain | "Hotels in Antarctica?" | Returns lookalike documents and fills in the rest | Empty result, and an honest refusal |

The out-of-domain case is the easy one and it is here for completeness. The other three are the ones that matter, because in all three the retrieved text is genuinely on topic. The answer is still wrong.

## Files in this folder

| File | Purpose |
|---|---|
| `2.1_vector_rag_hallucinates.ipynb` | The module notebook |
| `hotel-faqs.zip` | The source corpus, committed so the input never drifts |
| `faqs_docs.json` | The chunked corpus the FAISS baseline reads |
| `faqs_vector.index` | The pre-built FAISS index for the vector-only agent, committed so nobody spends the session waiting on an embedding job |
| `graph_builder.py` | The extraction pipeline, shared with Module 1's additive build |
| `graph_config.py` | Schema, model IDs, and corpus selection |
| `prepare_graph.py` | Brings a graph up to the state this module expects, for a run outside the hosted environment |

## The workshop page

`workshop-content/content/02-vector-rag-hallucinates/index.en.md`
