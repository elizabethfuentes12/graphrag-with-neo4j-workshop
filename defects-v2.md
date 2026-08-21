# Workshop Defects and Redesign Plan, Version 2

Date: 2026-08-21
Branch: `finalize-course`
Status: Implementation in progress

This document replaces the Module 2 direction in `defects.md`. The detailed audit
in that file remains useful as historical evidence. This version records the new
curriculum decision and turns it into an implementation plan.

## Brief summary

### What has already been fixed

- Module 1's learner-facing factual errors have been corrected. The notebook and
  workshop page now describe the actual schema, embedding configuration, build
  checks, held-out documents, and cleanup behavior more accurately.
- The broken FAISS artifact has been rebuilt. It now contains 300 normalized
  vectors with 1,024 dimensions in an inner-product index.
- A compatibility manifest now records and validates the embedding model,
  embedding purpose, dimensions, document count, corpus checksum, metric,
  normalization, vector source, and vector checksum.
- A reproducible graph-to-FAISS export script and focused artifact tests have
  been added. Sixteen focused tests passed when this work was recorded.
- Phase 1.5 executed the repaired retrieval paths repeatedly and saved the raw
  evidence. Run 2 established that the old Module 2 title is unsupported by the
  factuality results.
- The empirical result is clear enough for the curriculum decision: the old
  exercises mostly demonstrate missing evidence, variable agent behavior, and
  graph extraction quality. They do not provide a stable demonstration that
  vector RAG hallucinates.
- Phase 2 completed the active path migration. Module 2 now lives under
  `02-connected-context`, Module 3 now lives under `03-grounded-booking-agent`,
  and the old Module 2 notebook is preserved under `setup/phase15/archive/`.
- A post-migration semantic audit corrected Module 3.1 and Module 2.1 ownership
  throughout Modules 4 and 5, shared helpers, setup messages, and deployment
  documentation. Active learner surfaces contain no retired path or filename.

### Summary of the design changes

- Retire the title **Vector RAG Hallucinates**.
- Replace the two-agent answer contest with an evidence-first retrieval lesson.
- Rename Module 2 to **From Similarity Search to Connected Context**.
- Teach semantic search as the entry point and graph traversal as the way to add
  focused, structured, connected facts.
- Move the existing retrieval-pattern comparison from Module 3.1 into Module 2.
- Make vector retrieval and Vector-Cypher retrieval the main comparison.
- Keep hybrid retrieval and Text2Cypher as supporting patterns. They should show
  exact matching and structured filtering without making counting the headline.
- Simplify Module 3 so it focuses on building the grounded booking agent and its
  protected reservation command.
- Compare raw retrieval evidence, named fields, provenance, and context size.
  Treat generated answers as a secondary observation.
- Remove the old Paris, pool-count, Cairo, and Antarctica answer contest from the
  core learner path.

## Why the framing changes

The original module begins with a conclusion and asks four stochastic agent runs
to prove it. The repaired baseline did not produce that result consistently.
Phase 1.5 found that missing evidence was the vector arm's dominant problem. It
also found examples where both arms succeeded and examples where graph extraction
reduced the quality of the graph answer.

The stronger lesson is about complementary retrieval capabilities:

- Semantic search finds relevant source material when the question paraphrases
  the document.
- Exact-term search preserves names, identifiers, and postal codes that embeddings
  can rank poorly.
- Graph traversal expands a semantic match into connected rooms, amenities,
  policies, services, ratings, and provenance.
- Structured Cypher applies explicit filters when a question needs the database
  to select records by known fields and relationships.

This framing does not claim that graph enrichment always returns better context.
The graph can omit or distort facts when extraction or entity resolution is wrong.
The lesson is that semantic retrieval and graph structure contribute different
signals. A useful retrieval design combines those signals according to the
question.

## Proposed Module 2

### Title

**Module 2: From Similarity Search to Connected Context**

Suggested subtitle:

> Use semantic search to find the right source, then traverse the graph to return
> compact, connected facts with provenance.

### Learning objective

By the end of Module 2, a participant should be able to explain what each
retrieval signal contributes and select a retrieval pattern from the evidence a
question requires.

The participant should be able to distinguish:

- semantic relevance from exact matching;
- a relevant source document from a complete answer context;
- unstructured source text from connected, named graph fields;
- retrieved evidence from an LLM's final wording;
- facts present in the source from facts successfully extracted into the graph.

### Proposed notebook flow

#### 1. Verify the retrieval contract

Show the graph size, vector index, full-text index, embedding dimensions, metric,
and required fixtures before running a retriever. Fail with an actionable message
when the graph or indexes are missing.

#### 2. Start with semantic retrieval

Use a paraphrased hotel-policy question. Display the ranked `Chunk` results,
scores, filenames, and complete evidence. Explain why semantic similarity finds
the relevant wording even when the query and source use different terms.

#### 3. Show the exact-term gap

Use the existing `60611` example. Compare vector retrieval with hybrid retrieval.
The lesson is that semantic similarity and exact matching solve different parts
of the question.

#### 4. Add connected graph context

Use semantic retrieval to find the source for a hotel, then use Vector-Cypher to
return the connected hotel name, stable identifier, guest rating, amenities, and
source filename as named fields.

The main comparison should answer these questions:

- Did both methods identify the same hotel?
- Which requested facts appear in each result?
- How much unrelated text does each result contain?
- Can the learner trace every returned fact to a source or relationship?
- Does graph enrichment return a compact context that is easier for an agent to
  use?

#### 5. Show structured filtering without centering counting

Use the Chicago spa-and-pool example as a mechanism demonstration. The graph has
two Chicago candidates and one qualifying hotel in the current full build. Show
that Cypher applies both relationship conditions and excludes the other candidate.

Do not claim that vector retrieval must fail. Phase 1.5 showed that both Chicago
answers can succeed when the relevant documents fit inside the retrieval window.
The observable difference is how each result was selected.

#### 6. Summarize the retrieval spectrum

Use a concise decision table:

| Question need | Starting pattern | Contribution |
| --- | --- | --- |
| Paraphrased source lookup | Vector retrieval | Semantic relevance |
| Name, code, or identifier | Hybrid retrieval | Semantic and exact-term relevance |
| Semantic match plus connected facts | Vector-Cypher retrieval | Semantic entry and graph expansion |
| Flexible structured filtering | Text2Cypher retrieval | Database selection over named fields and relationships |

#### 7. Hand off to Module 3

Close by selecting the fixed Hybrid-Cypher retrieval function used by the booking
agent. Module 3 should apply that function rather than compare all retrieval
patterns again.

### What Module 2 should stop claiming

- Vector RAG reliably hallucinates on the workshop questions.
- Returning nearest neighbors causes the model to fabricate an answer.
- Graph retrieval always produces the correct answer.
- Graph retrieval is cheaper than vector retrieval.
- Both old agents read Neo4j.
- A one-hop `Hotel` to `Amenity` relationship is multi-hop reasoning.
- The model will respond in one predetermined way.

### Evidence to display

Every comparison should expose the deterministic retrieval result before any
optional answer generation:

- query text;
- retriever name and configuration;
- result rank and score;
- source filename;
- complete retrieved text when the pattern returns text;
- named graph fields when the pattern returns structured context;
- relationships traversed;
- result count;
- approximate context size;
- missing requested fields;
- provenance for each structured result.

The notebook can optionally ask a model to answer from each context. The lesson
must still work when the wording changes between runs.

## Locked Module 2 learning contract

This section is the Phase 1 specification. Later phases may improve wording and
layout, but they should preserve these questions, expected results, and module
boundaries unless new test evidence requires a change.

### Title and learner promise

**Title:** Module 2: From Similarity Search to Connected Context

**Learner promise:** Use semantic search to find the right source, then traverse
the graph to return compact, connected facts with provenance.

The lesson compares retrieved evidence. An LLM answer may be shown as an optional
extension, but it is outside the completion gate.

### Core examples and expected results

#### Example A: semantic paraphrase

**Question:** When does standard arrival processing begin at AnyCompany Cairo
Nile View?

Use `VectorRetriever` with the pinned Amazon Nova embedding contract. The query
paraphrases check-in instead of copying the source heading or the phrase
`Standard check-in time`.

The deterministic acceptance result is:

- the top three results include the chunk from `hotel-cairo-001.txt`;
- that chunk contains the supported time `3:00 PM`;
- the result displays rank, vector score, complete chunk text, source filename,
  and approximate character count;
- the lesson makes no claim about the wording of an LLM answer.

#### Example B: exact-term retrieval

**Question:** What is the cancellation policy for the hotel at 60611?

Compare the same question with `VectorRetriever` and `HybridRetriever`. Supply
`60611` as the full-text term and the complete question as the vector signal.
Keep the current linear hybrid configuration with `alpha=0.2` until Phase 3
revalidates it.

The deterministic acceptance result is:

- hybrid retrieval returns `hotel-chicago-001.txt` in the top five;
- the returned chunk identifies Windward Mile Tower and contains `60611`;
- the evidence contains the supported cancellation policy of at least 24 hours
  before arrival;
- both result lists display the same top-k limit, ranks, scores, filenames,
  exact-term hits, complete text, and approximate context size;
- the notebook reports the live vector rank instead of treating historical rank
  12 as a permanent guarantee.

#### Example C: semantic entry plus graph enrichment

**Question:** What amenities and guest rating does AnyCompany Cairo Nile View
have?

Run the question first through `VectorRetriever`, then through
`VectorCypherRetriever`. This is the primary Module 2 comparison. Vector retrieval
finds the relevant source. Vector-Cypher uses that semantic entry point and a
reviewed traversal to return focused fields.

The deterministic acceptance result for the enriched record is:

| Field | Expected value |
| --- | --- |
| `hotel_name` | `AnyCompany Cairo Nile View` |
| `hotel_id` | `81393d51-1df3-4f53-b58e-e4cda9736fd7` |
| `guest_rating` | `4.5` |
| `source_filename` | `hotel-cairo-001.txt` |
| `amenities` | Values containing pool, spa, fitness, WiFi, and restaurant terms |

The record must also include the source chunk, semantic score, approximate
context size, missing requested fields, and the relationship types used to add
the structured fields. The notebook should compare field coverage and context
size, then state that extraction quality limits the graph result.

#### Example D: structured AND filtering

**Question:** Which hotels in Chicago offer both a spa and a swimming pool?

Use reviewed, fixed Cypher for the required demonstration. Match Chicago hotels,
require both `OFFERS_AMENITY` relationships on the same hotel, and return the
candidate and qualifying records with their source filenames. A supporting
Text2Cypher example may ask the same question, but its generated query is outside
the deterministic completion gate.

The deterministic acceptance result is:

- the candidate set contains Windward Mile Tower from `hotel-chicago-001.txt`
  and Lakeview Horizon Suites from `hotel-chicago-002.txt`;
- Lakeview Horizon Suites is the only qualifying result;
- the result shows that Windward Mile Tower was excluded because its connected
  amenities do not satisfy both predicates;
- the database returns selected records rather than a pool count;
- no claim says that vector retrieval must fail on this question.

### Evidence display contract

Every retrieval block must display the question, retriever name, relevant fixed
configuration, top-k limit when applicable, result rank, score when applicable,
source filename, approximate context size, and requested fields that are absent.

Pattern-specific evidence is:

| Pattern | Required display |
| --- | --- |
| Vector | Complete chunk text and vector score |
| Hybrid | Complete chunk text, combined score, and exact query terms found in the evidence |
| Vector-Cypher | Source chunk, semantic score, named hotel fields, amenities, traversed relationship types, and field provenance |
| Fixed Cypher | Reviewed query purpose, parameters, candidate records, qualifying records, and source filename for each hotel |
| Supporting Text2Cypher | Generated query, read-only validation state, returned records, and any execution error |

For text results, provenance is
`(:Chunk)-[:FROM_DOCUMENT]->(:Document {source_filename})`. For graph-enriched
hotel fields, provenance adds
`(:Hotel)-[:FROM_CHUNK]->(:Chunk)` and the named relationship used for each
connected fact. A stable `hotel_id` identifies the entity but does not replace
source provenance.

### Pattern priority

The two core patterns are:

1. `VectorRetriever` for semantic source discovery.
2. `VectorCypherRetriever` for semantic entry plus connected, named context.

The supporting patterns are:

- `HybridRetriever` for exact terms such as `60611`;
- reviewed fixed Cypher for deterministic structured filtering;
- `Text2CypherRetriever` as an optional natural-language interface to a pinned,
  read-only schema.

`HybridCypherRetriever` is the handoff pattern. Module 2 identifies it as the
combination selected for the application, while Module 3 uses the fixed shared
function instead of reopening the retriever survey.

### Required fixtures

All examples require an online `hotel_chunk_embeddings` vector index over
`Chunk.embedding`, an online `hotel_chunk_fulltext` index over `Chunk.text`,
1024-dimensional query and stored embeddings, cosine similarity, and exactly one
source chunk for each required source document in the current workshop build.

The example-specific fixture checks are:

| Source | Required graph facts |
| --- | --- |
| `hotel-cairo-001.txt` | One Document, one embedded Chunk, one connected Hotel with the locked ID, name, address, rating 4.5, and amenities containing pool, spa, fitness, WiFi, and restaurant terms |
| `hotel-chicago-001.txt` | One Document, one embedded Chunk containing Windward Mile Tower and `60611`, one connected Hotel at the `60611` address, and no extracted combination of both spa and swimming-pool amenities |
| `hotel-chicago-002.txt` | One Document, one embedded Chunk for Lakeview Horizon Suites, one connected Chicago Hotel, and extracted spa and swimming-pool amenities |

Each hotel must resolve through one source path from Hotel to Chunk to Document.
Phase 3 should turn these checks into executable readiness assertions. In
particular, `hotel-chicago-002.txt` must join the lite-build required-source list
before the Chicago example becomes a learner-facing gate.

### Boundary with Module 3

Module 2 ends by selecting `search_hotel_knowledge` from
`workshop.hybrid_retrieval`. Module 3 begins with that function and the same Cairo
hero question. Module 3 teaches evidence-grounded answers, abstention, and the
protected reservation command. It does not repeat the retriever comparison.

## Proposed Module 3

### Title

**Module 3: Build the Grounded Booking Agent**

### Scope

Module 3 should begin with the selected Hybrid-Cypher retrieval function and use
it in the booking agent. It should retain the existing lessons on:

- returning named evidence fields;
- declining questions that the graph cannot answer;
- keeping the reservation write separate from generated Cypher;
- enforcing the guest limit inside the write transaction;
- using `request_id` to make retries idempotent.

The current Module 3.1 retrieval comparison should move to Module 2. The current
Module 3.2 grounded booking notebook should become the only Module 3 notebook and
be renumbered as Module 3.1.

## Defect status

### Resolved redesign defects

- **V2-1:** The active Module 2 title, route, folder, and notebook filename have
  been renamed. A repository gate rejects the retired names on active surfaces.
- **V2-2:** Retrieval-pattern comparison now has one active learner notebook in
  Module 2. The booking agent is the sole active notebook in Module 3.
- **V2-10:** Module ownership and numbering have been reviewed by meaning across
  Modules 3 through 5, shared helpers, fixtures, setup messages, and READMEs.
- **V2-11:** Graph preparation and every active path consumer now use the renamed
  Module 2 location.
- **V2-14:** Repository validation now checks retired learner-facing paths while
  allowing historical defect and Phase 1.5 records.

### Outstanding defects

### Module 1

#### M1-1. The optional unpinned extraction demo leaves data behind

The optional demo still uses a real held-out document name incorrectly. Its
cleanup query cannot find the generated document in the current form. The safe
fix is to give the demo a distinct filename, pass that filename as metadata, and
delete only that distinct document during cleanup.

### Module 2 redesign

#### V2-3. The old learner notebook depends on stochastic answer behavior

The four old tests infer retrieval quality from final model answers. Several
claims fail when the model abstains, searches repeatedly, or answers from memory.
The replacement notebook must grade deterministic evidence instead.

#### V2-4. The existing Module 2 diagrams contain false schema and data claims

The diagrams contain the wrong property name, a nonexistent `City` node, wrong
hotel counts, wrong averages, and an unsupported fabricated answer. They have no
editable source. Replace them with a connected-context diagram and commit its
editable source.

#### V2-5. The learner content uses inaccurate retrieval terminology

The FAISS records are whole documents, yet the current content calls them chunks.
The page also calls a hand-written Cypher tool Text2Cypher and describes a one-hop
relationship as multi-hop. The rewrite must use each product and graph term for
the mechanism that actually runs.

#### V2-6. Runtime setup must use shared workshop contracts

Any retained or moved notebook must load `.env` before resolving the AWS region,
pin the workshop model where a model is used, use the shared Neo4j authentication
and database helpers, resolve paths predictably, and expose retrieval failures.

#### V2-7. Text2Cypher must use the pinned schema and a read-only boundary

The earlier hand-written graph tool carried an incomplete schema and prompted the
model to invent `City`, `LOCATED_IN`, `HAS_AMENITY`, `rating`, and `guestRating`.
The moved Text2Cypher example must use the shared schema, a read-only database
user or equivalent read restriction, and a query timeout.

#### V2-8. Lite-build fixtures can vary because extraction is stochastic

Chicago currently works in the full graph. A lite rebuild can extract a negated
pool statement as a positive amenity. Readiness should report candidate, match,
and exclusion counts. It should avoid turning one stochastic extraction into an
unexplained notebook failure.

#### V2-9. Working-directory assumptions remain in setup and notebooks

Several paths rely on launching from one module directory. The rename increases
the chance of silent path breakage. Resolve repository and module assets from one
documented base path and test execution from the supported working directory.

### Module 3 and downstream modules

### Legacy FAISS and Phase 1.5 assets

#### V2-12. The new learner path may no longer use standalone FAISS

The rebuilt artifact is valid and tested, but the proposed notebook can teach
semantic retrieval through Neo4j's vector index. Keeping a second learner-facing
vector store adds concepts and maintenance without strengthening the connected
context lesson.

Audit all consumers before choosing one of these outcomes:

- retain FAISS as an optional facilitator baseline with its tests and manifest;
- move it into an explicitly archival evaluation area;
- remove it after confirming that no supported setup or notebook path uses it.

Do not delete the artifact merely because the curriculum changed. Its current
consumers and the value of the Phase 1.5 evidence must be resolved first.

#### V2-13. The Phase 1.5 grounding labels remain invalid

The judge evidence budget truncated long graph traces. The parser, rationale
selection, tie handling, and report divisor also have recorded defects. The
factuality results support retiring the old title. The grounding labels should
remain marked invalid unless the saved evidence is rescored.

The rescore is no longer a release gate for the new curriculum because the new
module makes no hallucination claim. It remains required if Phase 1.5 is kept as
an active evaluation artifact rather than historical evidence.

### Repository hygiene and validation

#### V2-15. The workshop path has not been rerun after the redesign

The final result needs a clean execution of Modules 1 through 3, followed by
focused smoke checks for Modules 4 and 5 references. Notebook structure, Python
compilation, setup behavior, diagram exports, and internal links also need
validation.

## Implementation plan

### Goal

Replace the unsupported hallucination lesson with a deterministic explanation of
how semantic search, exact-term search, and graph traversal combine to produce
focused answer context. Simplify Module 3 around the grounded booking agent and
preserve the working setup and deployment path.

### Assumptions

- The approved learner-facing title is **From Similarity Search to Connected
  Context**.
- Module 2 will own retrieval-pattern comparison and graph preparation.
- Module 3 will own the grounded booking agent and reservation command.
- The primary comparison is vector retrieval versus Vector-Cypher retrieval.
- Hybrid retrieval and Text2Cypher remain supporting patterns.
- The old four-question agent contest will leave the core learner path.
- Phase 1.5 evidence remains historical unless a separate decision promotes it
  into an actively maintained evaluation suite.
- Existing unrelated working-tree changes will be preserved.

### Risks

- Renaming the Module 2 directory affects imports, setup utilities, tests, links,
  notebook execution order, and held-out document loading.
- Moving a notebook between modules can leave stale titles and downstream prose
  even when all file paths resolve.
- Removing the FAISS baseline too early can break evaluation tools or discard a
  useful reproducibility artifact.
- Graph-enriched context can look authoritative when extraction omitted or merged
  source facts. The notebook must show provenance and state this limit.
- A broad Text2Cypher example can generate unsafe or invalid queries. Keep it
  read-only, schema-pinned, time-bounded, and visibly separate from writes.
- Lite extraction can change graph fixtures between runs. Prefer reporting live
  evidence over brittle fixture gates.
- Moving content without updating Modules 4 and 5 can break the production story.

### Phase 1: Lock the new learning contract

**Status: Complete**

**Outcome:** A short specification defines the exact questions, evidence fields,
expected fixtures, and boundary between Modules 2 and 3.

**Checklist:**

- [x] Confirm the Module 2 title and one-sentence learner promise.
- [x] Select the semantic paraphrase example.
- [x] Retain the deterministic `60611` exact-term example.
- [x] Select one graph-enrichment example that returns a hotel, stable ID, rating,
  amenities, and source filename.
- [x] Retain Chicago as a structured-filter mechanism example.
- [x] Define the fields and provenance each retriever must display.
- [x] Define which patterns are core and which are supporting.
- [x] Record the graph fixtures required by every example.
- [x] Confirm that Module 3 begins with the selected Hybrid-Cypher function.

**Validation:** Complete. Every example has a deterministic expected retrieval
result that can be checked without grading an LLM answer. The expected facts were
cross-checked against the committed source corpus, fixture manifest, retrieval
readiness checks, and existing Phase 1.5 Chicago evidence.

**Notes:** Pool counting, Orlando aggregation, and Antarctica leave the core path.
They may remain in historical Phase 1.5 evidence. The contract also identifies
`hotel-chicago-002.txt` as a new required lite-build source fixture. Phase 3 must
add it to the required-source contract, make the lite selector guarantee both
Chicago documents from that same source of truth, and add readiness tests for
the expected source path and amenities. Updating `REQUIRED_SOURCE_FILES` alone
would make the current lite build fail because the selector does not guarantee
the second Chicago document.

### Phase 2: Restructure the module files

**Status: Complete**

**Outcome:** Active module paths, notebook numbering, and executable path
consumers match the new curriculum. The move preserves authored history and
leaves generated local files behind.

**Locked path map:**

| Current path | Destination | Treatment |
| --- | --- | --- |
| `notebooks/03-retrieval-patterns/3.1_retrieval_patterns.ipynb` | `notebooks/02-connected-context/2.1_connected_context.ipynb` | Becomes the sole Module 2 learner notebook |
| `notebooks/03-retrieval-patterns/3.2_grounded_booking_agent.ipynb` | `notebooks/03-grounded-booking-agent/3.1_grounded_booking_agent.ipynb` | Becomes the sole Module 3 learner notebook |
| `notebooks/03-retrieval-patterns/reservation_command.py` | `notebooks/03-grounded-booking-agent/reservation_command.py` | Moves with the booking agent |
| `notebooks/02-vector-rag-hallucinates/2.1_vector_rag_hallucinates.ipynb` | `setup/phase15/archive/2.1_vector_rag_hallucinates.ipynb` | Preserved as historical evaluation material |
| `workshop-content/content/02-vector-rag-hallucinates/` | `workshop-content/content/02-connected-context/` | Becomes the Module 2 route |
| `workshop-content/content/03-retrieval-patterns/` | `workshop-content/content/03-grounded-booking-agent/` | Becomes the Module 3 route |

The tracked Module 2 support assets move to `notebooks/02-connected-context/`:
the README, graph builder, graph configuration, preparation script, source
archive, and legacy FAISS files. Phase 6 decides the final status of the FAISS
files. The Module 3 README moves to `notebooks/03-grounded-booking-agent/` and
receives only the minimum identity and path corrections in this phase.

**Review:** Ready to execute. The phase is large but remains one atomic path
migration. Splitting the moves from their active consumers would create broken
intermediate paths.

**Checklist:**

- [x] Record the pre-move tracked-file inventory and current working-tree changes
  so unrelated edits remain untouched.
- [x] Move tracked authored files individually. Leave ignored `data/`,
  `__pycache__/`, notebook outputs, and virtual environments out of the move.
- [x] Move the retrieval-pattern notebook to
  `notebooks/02-connected-context/2.1_connected_context.ipynb`.
- [x] Move Module 2 graph preparation, corpus, README, and legacy FAISS assets to
  `notebooks/02-connected-context/` without changing their behavior.
- [x] Archive the old agent-comparison notebook at
  `setup/phase15/archive/2.1_vector_rag_hallucinates.ipynb` and remove it from
  the notebook runner.
- [x] Move the booking notebook to
  `notebooks/03-grounded-booking-agent/3.1_grounded_booking_agent.ipynb`.
- [x] Move the Module 3 README and `reservation_command.py` into
  `notebooks/03-grounded-booking-agent/`.
- [x] Rename both workshop content routes according to the locked path map.
- [x] Apply minimum identity edits to the moved notebooks and READMEs: titles,
  module numbers, preparation hints, relative imports, file inventories, and
  handoff references. Defer lesson rewriting to Phases 3 through 5.
- [x] Update the notebook runner so it registers exactly one Module 2 notebook
  and one Module 3 notebook in the correct order.
- [x] Update active Python path consumers in Module 1, held-out loading, dump
  repair, the Phase 1.5 harness, and the FAISS tests.
- [x] Update Module 5's executable source path for `reservation_command.py` in
  the deployment notebook. Defer its explanatory lineage rewrite to Phase 4.
- [x] Update active route and filename references in root navigation, workshop
  navigation, summary links, and module next links. Defer full prose rewriting
  to Phase 5.
- [x] Add the retired Module 2 and Module 3 routes and notebook filenames to the
  active-surface stale-path gate while allowing historical files under
  `setup/phase15/` and the defect records.
- [x] Update path-sensitive tests and keep the module-folder-to-page parity gate
  passing.
- [x] Review the final rename set for accidental generated files, unrelated
  notebook output churn, or deletion of legacy FAISS assets.

**Validation:**

- The repository contains one active learner notebook for Module 2 and one for
  Module 3, and every notebook-runner path resolves.
- Every numbered notebook folder has a matching workshop content folder.
- Active code, tests, navigation, and learner files contain no retired routes or
  notebook filenames. Historical Phase 1.5 and defect records are excluded.
- The repository structure check, notebook-runner tests, and path-sensitive
  FAISS tests pass without Neo4j, Bedrock, or deployment access.
- Both moved notebooks remain valid JSON and every Python code cell compiles.
- The change summary shows tracked renames and focused identity edits. It shows
  no ignored data, cache files, generated notebook output, or unrelated changes.

**Validation result:** Complete for the Phase 2 structural scope. All 71 focused
repository, runner, FAISS, and rebuild tests pass. Notebook parsing, Python
compilation, content references, content weights, module-to-page parity, and
named paths pass in the repository checker. Active surfaces contain no retired
routes or notebook filenames. Unchanged support assets and the archived notebook
are byte-identical to their original Git blobs.

At Phase 2 completion, the repository checker still reported two pre-existing
content issues outside the structural scope: fixed graph counts in Module 1 and
a mismatched `03-agentcore-architecture.png` export. The post-migration quality
review removed the fixed counts and synchronized the current Module 4 export.
The full repository checker now passes.

**Notes:** This phase is an atomic path migration, so every active executable
consumer moves with its source. It does not change retrieval behavior, graph
fixtures, learner examples, diagrams, or FAISS ownership. Those changes remain
in Phases 3 through 6. The workshop is still mid-redesign after this phase and
is not ready for release until the later content and integration phases pass.
The existing ignored corpus extract now lives under the new Module 2 path. Old
bytecode caches were preserved under hidden retired-directory names and remain
outside Git.

### Phase 3: Build the evidence-first Module 2 notebook

**Status: Pending**

**Outcome:** Module 2 demonstrates semantic, exact-term, and graph-enriched
retrieval through visible evidence.

**Checklist:**

- [ ] Add a clear opening that explains semantic entry and graph expansion.
- [ ] Make lite selection consume the required-source contract and guarantee both
  Chicago documents while keeping the configured lite sample size stable.
- [ ] Add readiness assertions for `hotel-chicago-002.txt`, its embedded Chunk,
  its Hotel source path, and its connected spa and swimming-pool amenities.
- [ ] Add focused tests for required-source selection and the Chicago fixture
  acceptance query.
- [ ] Verify graph and index readiness before constructing retrievers.
- [ ] Use the shared embedding, AWS region, Neo4j database, and schema contracts.
- [ ] Display complete vector results with rank, score, filename, and text.
- [ ] Display hybrid results beside the `60611` vector results.
- [ ] Display Vector-Cypher results as named fields with provenance.
- [ ] Compare requested-field coverage and approximate context size.
- [ ] Add the Chicago structured-filter example without predicting model failure.
- [ ] Keep Text2Cypher read-only, schema-pinned, and time-bounded.
- [ ] Remove answer-dependent pass criteria and cumulative agent metrics.
- [ ] Add a closing decision table and handoff to Module 3.

**Validation:** Each section proves its lesson from retrieved evidence. Repeated
runs can vary in model wording without changing the learning outcome.

### Phase 4: Simplify Module 3 and repair downstream references

**Status: Complete**

**Outcome:** Module 3 contains the grounded booking agent only, and later modules
refer to the new numbering accurately.

**Checklist:**

- [x] Retitle Module 3 around the grounded booking agent.
- [x] Update the notebook introduction to treat Module 2 as the retrieval-pattern
  comparison.
- [x] Keep the fixed Hybrid-Cypher implementation and retrieval contract.
- [x] Keep abstention, guest-limit enforcement, and idempotent retry lessons.
- [x] Update Module 4 references to the retrieval comparison and booking agent.
- [x] Update Module 5 references to the booking agent and reservation command.
- [x] Update shared helper docstrings and fixture messages by meaning.
- [x] Update every `Module 3.1` and `Module 3.2` reference after manual review.

**Validation:** Complete. Modules 3 through 5 describe one consistent lineage
from the retrieval comparison in Module 2.1, to the local booking agent in
Module 3.1, to managed tools in Module 4, to the deployed runtime in Module 5.
The audit found no active `Module 3.2` reference.

### Phase 5: Rewrite learner content and diagrams

**Status: In progress**

**Outcome:** Notebook prose, READMEs, workshop pages, navigation, and diagrams all
teach the connected-context story.

**Checklist:**

- [x] Rewrite the Module 2 README and workshop page.
- [x] Rewrite the Module 3 README and workshop page.
- [x] Update the root README, workshop index, summary page, wrap-up page, and
  Module 1 next link.
- [x] Remove or live-render the fixed graph counts still present in the Module 1
  notebook and workshop page.
- [ ] Replace the old Module 2 diagrams with a semantic-entry and graph-expansion
  diagram.
- [x] Synchronize the existing `03-agentcore-architecture.png` export between
  both image trees.
- [ ] Commit editable diagram sources and synchronized exports in both image trees.
- [ ] Use `Chunk` only for graph `Chunk` nodes and `document` for whole documents.
- [ ] Remove deterministic claims about model answers.
- [ ] Explain that graph results reflect the extracted graph rather than an
  independent source of truth.
- [ ] Explain how Module 2 selects the retriever applied in Module 3.

**Validation:** Learner-facing surfaces contain no hallucination promise, false
schema element, false count, or stale module number.

### Phase 6: Resolve legacy FAISS and Phase 1.5 assets

**Status: Pending**

**Outcome:** Every retained artifact has a documented purpose and active test
owner.

**Checklist:**

- [ ] Inventory all consumers of the FAISS index, manifest, documents, loader,
  rebuild script, tests, and Phase 1.5 harness.
- [ ] Decide whether FAISS remains an optional baseline, becomes archival, or is
  removed.
- [ ] Keep the manifest and rebuild tests if any supported path retains FAISS.
- [ ] Mark Phase 1.5 reports clearly as historical if the harness is archived.
- [ ] If the harness remains active, repair evidence budgeting, JSON parsing,
  majority rationale selection, tie handling, and report arithmetic.
- [ ] Confirm every retained FAISS and Phase 1.5 consumer still uses the paths
  established in Phase 2.
- [ ] Remove only assets that have no supported consumer after the audit.

**Validation:** No orphaned artifact or test remains, and no supported workflow
depends on a retired path.

### Phase 7: Fix the remaining Module 1 cleanup defect

**Status: Pending**

**Outcome:** The optional unpinned demo always removes only its own temporary data.

**Checklist:**

- [ ] Give the demo a filename that cannot collide with a held-out document.
- [ ] Pass that filename through document metadata.
- [ ] Clear the distinct demo filename in the cleanup block.
- [ ] Re-run the demo after a completed build and verify that real hotel data
  remains unchanged.
- [ ] Restore the learner-facing cleanup promise after validation.

**Validation:** The demo creates and removes its own nodes and cannot delete a
participant-built hotel when rerun.

### Phase 8: Integrate and validate the workshop path

**Status: Pending**

**Outcome:** The redesigned workshop runs from graph build through grounded agent
without stale references or hidden retrieval failures.

**Checklist:**

- [ ] Validate notebook JSON structure and compile every code cell.
- [ ] Run focused graph preparation, retrieval, fixture, and path tests.
- [ ] Execute Modules 1 through 3 in order against the configured environment.
- [ ] Smoke-check the Module 4 and Module 5 handoff references.
- [ ] Verify the semantic, hybrid, Vector-Cypher, and structured-filter evidence.
- [ ] Verify that every displayed structured fact includes provenance.
- [ ] Check all internal links, notebook paths, and workshop navigation.
- [ ] Search learner-facing files for the old title and retired test claims.
- [ ] Exclude historical defect and evaluation records from that search gate.
- [ ] Confirm both diagram trees contain matching exports and editable sources.
- [ ] Record live service versions, graph counts, model ID, region, and execution
  time with the final validation report.

**Validation:** All focused tests pass, Modules 1 through 3 execute successfully,
later-module handoffs resolve, and the deterministic evidence matches the new
learner-facing claims.

## Completion criteria

- Module 2 is titled **From Similarity Search to Connected Context**.
- Module 2 compares retrieval evidence rather than trying to induce hallucination.
- Semantic search, hybrid search, graph enrichment, and structured filtering each
  have one clear role.
- Vector-Cypher is the main demonstration of semantic entry plus connected graph
  context.
- Module 3 contains the grounded booking agent and protected write path without a
  duplicate retriever survey.
- Module 4 and Module 5 accurately identify the earlier source of each retrieval
  and write component.
- Every retained FAISS or Phase 1.5 asset has a documented purpose and passing
  validation.
- The optional Module 1 demo cleans up only its own data.
- All notebooks use shared environment, model, database, schema, and path
  contracts.
- Learner-facing content contains no unsupported hallucination guarantee.
- New diagrams show the real graph schema and have editable sources.
- Modules 1 through 3 run end to end with deterministic evidence for every core
  lesson.
