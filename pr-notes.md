
## Squash merge message

GitHub prefills the squash commit with every commit subject on the branch.
Replace both fields with the following.

**Title**

```
restructure modules 2-3 and make the graph build deterministic
```

**Extended description**

```
Amenities came out of free-text LLM extraction, though every source
document already lists them under a fixed heading, so the same authored
label could become several nodes and no two builds matched. Alongside
that, a few extractions returned no hotel and the build continued past
them, global exact-name resolution merged hotels sharing a name across
cities, and the readiness checks compared counts rather than
reconciling the graph against the corpus. Module 2 stated up front that
vector RAG hallucinates and relied on four stochastic agent runs to
show it, which did not land consistently on the repaired graph.

Move amenities out of the LLM extraction schema and into a shared
parser that reads the authored bullets exactly as written, merges by
canonical source name, and keeps provenance on every relationship.
Disable global exact-name resolution, fail a document whose extraction
errors, require exactly one hotel per source, and reconcile the graph
against the corpus. Rebuild the shipped dump on this pipeline. The LLM
still extracts the unstructured prose.

Rename Module 2 to From Similarity Search to Connected Context and
teach complementary retrieval instead of a contest, comparing vector
against Vector-Cypher retrieval on the same questions and showing the
deterministic evidence before any generated answer. Collapse Module 3
to a single grounded booking agent notebook covering grounded answers,
abstention, and the protected reservation command. Pin the questions,
fixtures, and expected answers in shared workshop code.

Also fix the self-cleaning Module 1 demo, the Module 4 Lambda role's
Bedrock permission, the Module 6 base path, and the Runtime build
context; give every notebook one base-path contract; drop FAISS and the
benchmark harness; and move tests and release tooling out of the
participant surface.

Modules 1 through 3 and 4 through 6 each passed a live run against
Neo4j Aura and Claude Sonnet on Bedrock, with cleanup verified.
```
