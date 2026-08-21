---
title: "Module 1: Build the Graph"
weight: 20
---

## Build a Typed Graph from Documents

Claude on :link[Amazon Bedrock]{href="https://aws.amazon.com/bedrock/" external=true} converts five hotel FAQ documents into a queryable knowledge graph. `SimpleKGPipeline` from the :link[neo4j-graphrag]{href="https://neo4j.com/docs/neo4j-graphrag-python/current/" external=true} package splits each document into chunks, embeds the chunks, and extracts typed nodes and relationships.

An embedding groups text by meaning. Extraction records specific facts as nodes and relationships, such as whether a hotel offers a spa, whether the spa costs extra, and where the hotel is located. This structure allows a query to match those facts directly. This module writes the embeddings and extracted facts, and every later module reads them.

You add five hotels that were held out of the prepared graph. The remaining modules query them as part of the full dataset.

:::alert{type="info" header="The graph keeps these hotels"}
The five hotels remain in the graph after this module because later modules use them. Nothing in this module deletes them.
:::

---

## What the Graph Looks Like

Extraction writes two connected layers.

**The lexical layer holds the text.** Each source file becomes one `Document` node. The text is split into chunks, and each chunk becomes a `Chunk` node carrying that text and a 1024-dimension embedding of it. Vector search and keyword search read this layer.

**The domain layer holds the facts stated in that text.** A `Hotel` node carries the name, address, and guest rating as properties. Typed relationships connect it to `Room`, `Amenity`, `Policy`, and `Service` nodes. Cypher queries read this layer.

`FROM_CHUNK` and `FROM_DOCUMENT` connect the two layers. A search finds a chunk, then a graph traversal reaches its typed facts and source document.

:::code{language=text}
hotel-tokyo-002.txt
    |  one source file, about 7 KB of text
    v
(:Document {source_filename: "hotel-tokyo-002.txt"})
    ^
    |  FROM_DOCUMENT                      the lexical layer: the text
(:Chunk {text, embedding: 1024 floats})
    ^
    |  FROM_CHUNK                         the domain layer: the facts
(:Hotel {name, address, guest_rating, total_rooms, email, phone})
    |
    +-[:HAS_ROOM]---------> (:Room)
    +-[:OFFERS_AMENITY]---> (:Amenity)
    +-[:HAS_POLICY]-------> (:Policy)
    +-[:PROVIDES_SERVICE]-> (:Service)
:::

Every domain relationship starts at `Hotel`, so each document produces a one-hop star of facts.

| Term | What it means here |
|------|--------------------|
| `Document` | One source file. It carries `source_filename`, which is how the build finds and clears its own work |
| `Chunk` | A slice of that file's text, plus the embedding of that text. These documents produce one chunk each |
| `Hotel` | One hotel, with its name, address, and guest rating as properties on the node |
| `FROM_CHUNK` | Joins an extracted entity back to the chunk it came from |
| `FROM_DOCUMENT` | Joins a chunk back to its source file |

---

## Why You Extract Five Documents

The corpus contains 300 hotel FAQ documents. The graph dump restored during Setup contains 295 of them, extracted with the same pinned schema used in this module. Extracting all 300 takes hours. You extract the five remaining documents in about four minutes.

You extract the `-002` document for Tokyo, Sydney, Rio de Janeiro, Cape Town, and Prague. These documents keep the build separate from the fixtures used by later modules\:

- Later-module fixtures do not depend on these five `-002` hotels, so rebuilding them preserves the required fixture data.
- The dump retains the `-001` hotel for each city, which keeps those cities in the graph during extraction.
- The list excludes Cairo because Module 3 asks about a Cairo hotel by name. That question uses data already present in the dump.

Every aggregation and multi-hop query in later modules runs across the full graph, including your five hotels.

---

## How the Extraction Pipeline Works

`SimpleKGPipeline` runs five stages for each document. The workshop sets the behavior for every stage.

| Stage | What it does here |
|-------|-------------------|
| Split | `FixedSizeSplitter` cuts the document into chunks of at most 12000 characters |
| Embed | Amazon Nova turns each chunk into a 1024-dimension vector and stores it on the `Chunk` node |
| Extract | Claude reads the chunk and returns JSON holding the nodes and relationships it found, restricted to the pinned schema |
| Resolve | Entity resolution merges an extracted entity into an existing node when one already matches |
| Write | The pipeline creates the `Document`, `Chunk`, and entity nodes, then connects them |

Chunk size controls how much text the model sees in one call. The largest corpus document is 7,442 bytes, and the chunk size is 12000 characters, so each document becomes one chunk. The hotel's name, address, rating, rooms, and amenities reach the model together. This context associates every extracted amenity with the correct hotel. The overlap is 0 because each document has only one chunk.

Extracting one complete hotel produces a large JSON response that can exceed the 4096-token default that the workshop's Bedrock client sets. The model then truncates the response in the middle of an object, which makes the JSON invalid and causes the pipeline to drop the chunk. The build raises the extraction limit to 16000 tokens so the complete response fits.

Entity resolution merges matching entities while preserving each chunk. The build records the existing chunk IDs before extraction, so every new chunk belongs to the current run.

---

## Why the Schema Is Pinned

`SimpleKGPipeline` can extract data without a schema. In that mode, the model chooses labels for each chunk based on headings that vary across documents. Test runs produced these label differences\:

| Kind of drift | Labels the model chose | Why it breaks queries |
|---------------|------------------------|-----------------------|
| A property promoted to a node | `Address`, `Fee`, `Location` | The address sits on the hotel node in one document and one hop away in the next |
| A type split from its instance | `RoomType`, `BedConfiguration` | A room's own properties become separate nodes to join through |
| Two names for one thing | `ContactMethod`, `ContactInfo` | Both are reasonable, and a query has to know which one a given document used |
| Geography expanded into a hierarchy | `City`, `Country` | The city is text inside the address in most documents and a node in a few |

Each structure represents its source document, but a single Cypher pattern cannot match all of them. The extraction process needs one vocabulary that applies to every document.

The pinned schema provides that shared vocabulary\:

:::code{language=text}
(:Hotel)-[:HAS_ROOM]->(:Room)
(:Hotel)-[:OFFERS_AMENITY]->(:Amenity)
(:Hotel)-[:HAS_POLICY]->(:Policy)
(:Hotel)-[:PROVIDES_SERVICE]->(:Service)
:::

The schema restricts extraction to the listed node types, relationship types, and patterns. The model drops facts that do not fit instead of creating new labels.

The model also follows the property descriptions in the schema\:

- `address` stores the address as a `Hotel` property and keeps `Address` out of the graph.
- `guest_rating` converts a value such as `4.6/5.0` into the float `4.6`. Later modules can average the numeric property.
- `Amenity` creates a node only when the document says the hotel has that amenity. This rule prevents sentences such as "Pool facilities are not available at this property" from creating a pool.

Later modules require this structure. Module 3's retrieval tool expects each `Hotel` node to have `name`, `address`, and `guest_rating` properties. The pinned schema writes those properties consistently.

The notebook includes an optional comparison. It extracts one document without a schema and prints the labels created by the LLM. That comparison leaves its document and its invented labels in the graph, and nothing later in the workshop reads them.

---

## Retrieval Indexes

The graph dump contains the extracted data but excludes the vector and full-text indexes. This module creates both indexes over every `Chunk` in the graph, including the chunks your extraction just wrote\:

| Index | What it reads | What it finds |
|-------|---------------|---------------|
| `hotel_chunk_embeddings` | `Chunk.embedding`, cosine similarity over 1024 dimensions | Text that means the same thing as the question in different words |
| `hotel_chunk_fulltext` | `Chunk.text`, full-text | Exact strings that embeddings blur together, such as a postal code or a hotel name |

Each index handles a different search pattern. An embedding of `60611` is similar to embeddings for other five-digit numbers, so vector search can rank the correct chunk below other results. Keyword search matches `60611` exactly. Vector search handles the opposite case by matching a question to relevant text that uses different words. Module 3 combines both indexes and lets you adjust their weights.

The document and query embeddings must use the same model, dimensions, and purpose. A query embedding with different settings can return incorrect rows without producing an error. The workshop embedder prevents this mismatch by using fixed settings.

The dump already contains three uniqueness constraints. This notebook leaves them unchanged. Module 3 verifies the constraint used by its duplicate-request check.

---

## What the Build Verifies

The build ends with three checks. It stops when any check fails\:

1. **The schema held.** The build lists every label this run's own chunks produced and fails if an off-schema label appears.
2. **The indexes match the retrieval contract.** The build reads both indexes back and compares type, state, label, property, dimensions, and similarity function.
3. **The graph answers the later modules' questions.** The build runs those queries now, such as Paris hotels with ratings and Cairo hotels that have a spa, a pool, and a rating.

The document and chunk counts are strict. All five documents must load, and the total chunk count must equal the total document count. The fixture checks allow variation in individual properties because extraction is stochastic. They require at least one Cairo hotel with a spa, a pool, and a rating, and at least two Paris hotels with a rating. The schema check is strict because an unexpected label means the shared vocabulary failed.

---

## Run It

Open `notebooks/01-build-graph/1.1_build_graph.ipynb` and run the cells in order. Expect about four minutes for the five documents.

:::alert{type="warning" header="If extraction fails"}
Bedrock can throttle extraction calls, so the build retries them automatically. If a call still fails, rerun the cell. Before each attempt, the build removes data from only these five documents. It preserves all other graph data.
:::

At the end, the notebook compares the document and hotel counts from before and after the build. It also lists the hotels you extracted with their addresses, ratings, and amenity counts, and it walks both layers of the graph for one of them.

---

## Learn the Agent Basics for Module 2

Module 2 creates two agents. At the end of this notebook, a short section introduces the :link[Strands Agents SDK]{href="https://strandsagents.com/" external=true}. It explains how an `Agent` works, why `BedrockModel` uses a fixed model ID, and how the `@tool` decorator exposes a Python function to the model.

Accurate tool results provide the foundation for grounded answers. If a tool returns plausible text that does not answer the question, the agent can give a confident but incorrect answer. Module 2 compares this result with an answer based on computed graph data.

## Next

Head to [Module 2](../02-vector-rag-hallucinates/).
