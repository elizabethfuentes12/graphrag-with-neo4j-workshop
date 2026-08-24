# PR notes

## Title

Restructure Modules 2 and 3 around connected context, rebuild the graph deterministically, and validate all six modules live

## Summary

This branch replaces the unsupported "Vector RAG Hallucinates" lesson with an
evidence-first retrieval lesson, makes the graph build deterministic where the
source documents already carry structure, and validates every module against
live Neo4j and Amazon Bedrock. The notebooks are now the specification and the
tests are the enforcement. Maintenance and release tooling moved out of the
shipped repository so participants see only the setup check they need.

Design rationale and the audit trail are in `workfolder/defects-v2.md`. The
open-work record is `workfolder/fix-defects-v3.md`. The graph release record is
`workfolder/clean-graph-final-state.md`.

## Curriculum restructure

- Retired the title **Vector RAG Hallucinates** and the four-question agent
  contest. The repaired baseline did not reproduce that result consistently, so
  the claim was not supportable.
- Renamed Module 2 to **From Similarity Search to Connected Context** and moved
  it to `notebooks/02-connected-context/2.1_connected_context.ipynb`.
- Moved the retrieval-pattern comparison out of Module 3 and into Module 2. The
  primary comparison is now vector retrieval against Vector-Cypher retrieval.
  Hybrid retrieval, reviewed fixed Cypher, and Text2Cypher are supporting
  patterns.
- Simplified Module 3 to a single notebook,
  `notebooks/03-grounded-booking-agent/3.1_grounded_booking_agent.ipynb`. It
  begins with the selected Hybrid-Cypher function and teaches grounded answers,
  abstention, and the protected reservation command.
- Renamed the matching workshop content routes to `02-connected-context` and
  `03-grounded-booking-agent`, and updated root navigation, module next links,
  summary, and wrap-up.
- Locked the Module 2 learning contract in code. `REQUIRED_SOURCE_FILES`,
  `SOURCE_FIXTURES`, `CAIRO_HOTEL_ID`, `CHICAGO_QUALIFIER`, and
  `CHICAGO_EXCLUSION` live in `notebooks/workshop/retrieval_setup.py`.
- Made every retrieval block display its deterministic evidence before any
  optional answer generation: query, retriever, rank, score, source filename,
  complete text or named fields, relationships traversed, context size, missing
  fields, and provenance.
- Kept optional Text2Cypher governed. It uses the pinned shared schema, a
  bounded timeout, and an `EXPLAIN` planner check, and it executes only queries
  Neo4j classifies as read-only.

## Deterministic graph build

- Added `notebooks/workshop/amenities.py`. A shared parser reads the authored
  `## Hotel Amenities` bullet list exactly as written, and it rejects missing,
  repeated, empty, or malformed sections.
- Removed Amenity nodes and relationships from the LLM extraction schema. The
  model now extracts only genuinely unstructured prose.
- Merged Amenity nodes by their canonical source names and kept source
  provenance on every `OFFERS_AMENITY` relationship. Writes are idempotent.
- Disabled global exact-name entity resolution. Same-named hotels in different
  cities no longer merge.
- Made extraction failures visible. Every source must resolve to exactly one
  Hotel before amenities are attached.
- Added source-exact reconciliation to the validators. They compare the
  filename-to-amenity projection against the committed corpus instead of
  relying on counts.
- Added bounded concurrency and resume support to the facilitator build.
  Participant ingestion stays sequential.
- Made `prepare_graph.py` refuse to clear a populated graph without an explicit
  `--rebuild` request, including a clear against an empty graph.
- Replaced `static/neo4j-hotel-graph.dump`. It is 6,542,982 bytes with SHA-256
  `a6eeecc3305acbbffe46e0ef7531db34c5a62d62db200c5574c3946102e29f02` and holds
  295 Documents, 295 Hotels, 65 Amenities, and 1,606 amenity assertions.
- Confirmed the learner-additive path. Module 1's five held-out documents take
  the graph to 300 Documents, 300 Hotels, 65 Amenities, and 1,632 amenity
  assertions, matching the full corpus projection exactly.

## Module 1 corrections

- Corrected the notebook and content page to describe the real schema, embedding
  configuration, build checks, held-out documents, and later-module handoffs.
- Fixed the optional extraction demo so it cleans up after itself. It now uses a
  distinct filename and deletes only that document, leaving the five participant
  sources and the graph counts unchanged.

## Modules 4 through 6 fixes

- Granted the Module 4.1 Lambda execution role `bedrock:InvokeModel` on the
  embedding model and on inference profiles. Its positive-control smoke test
  previously failed with `AccessDeniedException`.
- Repaired the Module 6 base-path bug. `memory_helpers` resolved to `notebooks/`
  instead of the repository root, so it never found `NEO4J_PASSWORD` and the
  harness reported a pass on a notebook that validated nothing.
- Added `notebooks/05-agentcore-deploy/runtime_app/.dockerignore` so `.env`,
  credentials, notebooks, toolkit state, and a stray `workshop/` source tree
  stay out of the image build context.
- Updated the Gateway tool schemas and the `graph_query` Lambda for the renamed
  module paths and the current retrieval contract.

## Path and dependency contract

- Gave every notebook and helper one tested base-path contract. Launching from
  the repository root, from `notebooks/`, or from a module directory all resolve
  the same assets, and `WORKSHOP_NOTEBOOKS_DIR` overrides the base path with
  validation.
- Removed FAISS from the learner path along with the Phase 1.5 benchmark
  harness. `faiss-cpu` left `notebooks/requirements.txt` and the shared package
  dependencies.
- Set the workshop default model to `us.anthropic.claude-sonnet-5` in
  `.env.example`.

## Diagrams and prose

- Rebuilt the Module 2 retrieval decision tree. Reviewed fixed Cypher now owns
  the Chicago spa-and-pool branch, and Text2Cypher is labeled optional.
- Added an editable Excalidraw source for the decision tree and replaced the
  `.drawio` source. Both image trees are byte-identical.
- Deleted `01-rag-vs-graphrag-problem.png`,
  `01-rag-vs-graphrag-architecture.png`, and
  `02-retrieval-patterns-comparison.png`. No active page referenced them, and
  the retrieval comparison image made a performance claim the evidence did not
  support.
- Updated `DIAGRAM_PROMPTS.md` and the AgentCore architecture export in both
  image trees.
- Corrected the learner claims across Modules 1 through 5. Module 2 selects the
  Hybrid-Cypher configuration rather than comparing it, one-hop examples use
  connected-traversal language, graph `Chunk` nodes are distinguished from whole
  documents, model wording is described as variable, and graph results are
  described as extracted facts rather than an independent source of truth.

## Repository hygiene

- Reduced `setup/` to the participant-facing surface: `verify_setup.py`,
  `run_notebooks.py`, and a short README. The offline test suite, release
  automation, dump repair, and validation scripts moved to the ignored
  `workfolder/` tree so they do not complicate participant setup.
- Removed the obsolete FAISS artifacts, rebuild script, and their tests.
- Deleted the stale `defects.md` from the repository root and moved the historical
  planning records under `workfolder/`.
- Updated `.gitignore` for the relocated notebook output and pytest caches.

## Live validation

The record is `workfolder/live-validation.md`.

- Modules 1 through 3 passed at commit `b1e2684` against Neo4j Aura 5.27 and
  `us.anthropic.claude-sonnet-5` in `us-east-1`. The gate reported 3 passed, 0
  failed, 0 skipped. The graph moved from 295 to 300 Documents as expected, and
  the optional Text2Cypher check reported `passed: EXPLAIN query_type=r`.
- Modules 4 through 6 passed at commit `6e06c32`. Module 4.1 created and called
  both Lambda-backed Gateway tools, Module 4.2 recalled a preference in a new
  session, Module 5 deployed the Runtime and passed its grounding, refusal,
  policy, write, and idempotency checks, and Module 6 wrote real memory records
  with working isolation, recall, provenance, and tagging.
- Cleanup removed the test graph records and the exact workshop AWS resources.
  All 300 Hotel nodes survived, and the unrelated supplier Gateway and Runtime
  were verified separately and left untouched.

## Known gaps

- Modules 4.1 and 4.2 still have no teardown path. Workshop Studio reclaims the
  account when the event ends, so this affects only participants running in
  their own account. Fixing it is out of scope for this branch.
- The accepted dump carries a recovered manifest. Its original wrapper failed
  after graph readiness, so the build-start Git state, critical-file hashes, and
  image identity are recorded as null. A future fresh build captures them
  natively.
- Learner page discovery stays a small explicit list. Adding a page means adding
  it to `LEARNER_FILES` in the content contract test.
