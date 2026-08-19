[< Back to the workshop README](../../README.md)

# Module 6: Inspectable Neo4j Memory

Module 4 Part 2 gave the agent memory it could recall. This module gives it memory it can explain. One preference is persisted, recalled by the same actor in a fresh session, proved invisible to a second actor, and then traced back to the exact message that produced it and forward to the real `Hotel` node it describes.

**The mechanism, in one sentence: a preference stored as a graph node keeps its edges, and its edges are the audit trail.**

**At a Glance**
- **Failure it stops:** a wrong preference, "near the elevator" instead of away from it, that cannot be traced to a source, corrected in place, or connected to the hotel the guest actually booked.
- **Neo4j:** writes `Conversation`, `Message`, `User`, and `Preference` nodes, plus two workshop-owned edges, `DERIVED_FROM` to the source message and `ABOUT_HOTEL` to the existing hotel. No `Hotel` node is modified.
- **AWS:** Amazon Titan Text Embeddings V2 on Amazon Bedrock, used by the memory library.
- **You'll build:** memory records under the module's own namespace, all removable by one scoped cleanup script.

---

## The notebook

| Notebook | What it proves |
|---|---|
| [`6.1_neo4j_memory.ipynb`](6.1_neo4j_memory.ipynb) | The full provenance path, from actor through preference, source message, and session to the canonical hotel, returned by one parameterized Cypher query |

Every actor and session identifier carries a short run ID, so re-running the notebook cannot append to an earlier transcript. Each live cell opens and closes its own memory client, so a failure in one cell cannot leak a connection into the next. Without credentials, every live cell skips cleanly rather than raising.

## The order matters

Managed memory first, inspectable memory second. The provenance walk here only lands as a contrast if the participant has already used the managed alternative in Module 4 Part 2 and seen what it does not give back.

| | AgentCore Memory | Neo4j graph memory |
|---|---|---|
| How it is written | Managed extraction | Explicit application writes |
| When it is recallable | After asynchronous extraction | Immediately |
| Inspectability | A service API | A Cypher query returning the source message |
| Correction | Delete and re-extract | `SET` on one property |
| Domain link | Separate from domain data | An edge to the real `Hotel` node |
| Operations | AWS runs it | You run Neo4j and the embedding contract |

## Two boundaries the notebook states out loud

- Multi-tenant mode rejects a memory write that omits a user identifier, but the application still has to authenticate actors and authorize session IDs. The library does not do that for you.
- The library's semantic searches are store-wide, so this module does not use them as an isolation boundary. Its recall query starts at the selected `User` and traverses out.

## Files in this folder

| File | Purpose |
|---|---|
| `6.1_neo4j_memory.ipynb` | The module notebook |
| `memory_helpers.py` | Builds the memory client over the same Neo4j instance as the hotel graph, and holds the provenance link and recall queries |
| `cleanup_memory.py` | Removes exactly what the notebook wrote: namespaced memory records, the preferences it tagged, and its own relationships. It never changes a `Hotel` node |

## The workshop page

`workshop-content/content/06-neo4j-memory/index.en.md`
