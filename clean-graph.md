# Workshop plan for deterministic amenities

**Status: Pending. This is an implementation plan. No graph changes have been
made.**

Investigated 2026-08-21 against the current repository, the upstream
`sample-stop-ai-agent-hallucinations-workshop` repository, its historical full
build log, the committed hotel corpus, and the live Aura staging graph.

## Goal

Fix shared amenity identity with the smallest approach that is reliable and
easy to explain in a four-hour introductory workshop.

The workshop lesson should be:

> Use the LLM for genuinely unstructured extraction. When a source already
> contains a structured list, parse that list directly and use its values as
> graph identity.

This is a workshop implementation, not a general-purpose master-data or entity
governance system.

## Workshop scope decisions

- The `## Hotel Amenities` bullet list is the authoritative amenity source.
- The exact trimmed bullet text is the canonical `Amenity.name`.
- All 65 author-declared labels are retained. Grouping them into broader
  concepts is outside this fix.
- The LLM no longer extracts Amenity nodes or `OFFERS_AMENITY` relationships.
- The graph is rebuilt from the committed source data. No legacy migration,
  alias catalog, rollback manifest, or compatibility layer is required.
- The same parser runs for the prebuilt graph and the five learner-ingested
  documents.
- Shared Amenity nodes contain only their canonical name. Hotel-specific
  descriptions, fees, hours, or availability are not placed on the shared
  node.
- Global name-based entity resolution is disabled so two hotels with the same
  display name cannot collapse into one Hotel.
- Every source document must produce exactly one Hotel before its amenities are
  attached.

## What the upstream repository showed

### How the graph is built

The upstream repository extracts `01-graph-build/hotel-faqs.zip`, selects a
30-document lite build or all 300 documents, and sends each whole document to
`SimpleKGPipeline`.

The shared build path already centralizes useful behavior in
`01-graph-build/graph_builder.py`:

- The notebook and preparation script call the same builder.
- A scoped wipe removes only nodes owned by the workshop build.
- A three-document canary runs before the full extraction.
- Failed documents receive one retry after their partial graph is cleared.
- `Document.source_filename` records which source file produced a document.
- Document, Chunk, and entity provenance relationships make source
  reconciliation possible.
- Retrieval indexes and downstream fixtures are prepared and checked in one
  flow.
- Lite and full build modes give facilitators a fast diagnostic path and a
  complete release path.

These patterns are worth reusing. The current repository already carries newer
versions of much of this machinery, so the fix should extend the shared builder
instead of adding a second graph-build path.

### Where the build went wrong

The extraction step uses Claude through a custom Bedrock adapter. That adapter
returns prompt-generated text which is then repaired and parsed as JSON. It
does not use provider-enforced structured output.

The pinned graph schema closes node labels, relationship types, and graph
patterns. It does not constrain `Amenity.name`. The model can therefore turn
the same source line into `WiFi`, `High-Speed WiFi`, or another paraphrase.

The pipeline then runs exact same-label, same-name entity resolution over all
entities. That cannot reunite paraphrased amenities, and it can merge distinct
hotels that happen to share a display name.

The historical full-build log shows extraction parse errors followed by
successful-looking document messages. The completed build contained 300
Document nodes and 300 Chunk nodes but only 292 Hotel nodes. The default error
behavior allowed partial extraction to continue, while readiness checks proved
only that at least one Hotel conformed to the schema.

Four documents failed to produce a Hotel. Four additional Hotel nodes were
lost when exact-name resolution merged these cross-city pairs:

- Riverside Crossing Suites in Dallas and Windsor.
- Riverside Lodge in Boise and Calgary.
- Riverway Lodge in Minneapolis and Saskatoon.
- Waterway Inn in Houston and Kitchener.

Those eight losses reconcile 300 source documents to 292 Hotel nodes.

The pool evidence exposes three different failure classes. The corpus contains
175 hotels whose authoritative amenity list includes a pool, while the graph
returned 168 Hotel identities. Four pool-bearing documents did not produce a
Hotel, two duplicate-name pairs affected the pool result, and one document that
explicitly said no pool was turned into a positive Pool amenity.

The dump process copied the resulting Aura graph and checked structural counts.
It did not normalize amenities or reconcile extracted facts to source. The
current dump repair adds missing source filenames, hotel IDs, and Rule data,
but it does not repair amenity identity.

Five documents are omitted from the prebuilt graph and extracted live by the
learner. They use the same generative path, so changing only a dump would allow
the defect to return during the workshop.

## Corpus evidence

The source already provides a simple deterministic contract:

| Measure | Observed value |
|---|---:|
| Hotel FAQ documents | 300 |
| Documents with exactly one `## Hotel Amenities` section | 300 |
| Amenity bullet rows | 1,632 |
| Distinct amenity labels | 65 |

The most frequent source labels are already identical across documents:

| Source label | Occurrences |
|---|---:|
| `On-Site Restaurant` | 300 |
| `Complimentary High-Speed Wifi` | 300 |
| `24-Hour Fitness Center` | 274 |
| `Outdoor Swimming Pool` | 175 |
| `Full-Service Spa` | 162 |
| `Lounge Bar` | 130 |

The graph has 83 generated amenity names even though the complete source corpus
has 65 explicit labels. The LLM introduced variation into a field that did not
need generation.

Views, tours, a hammam, architecture, and other low-frequency labels are not
extraction mistakes. The source authors explicitly placed them in the amenity
list. Reclassifying them may be a reasonable future content decision, but it is
not required to repair graph identity.

## Why the earlier proposed fixes are not the answer

### Enum in `GRAPH_SCHEMA`

The installed `neo4j-graphrag` property model accepts a property name, Neo4j
type, description, and required flag. An added enum member is ignored. The
custom Bedrock wrapper also does not enforce an output schema, so putting
allowed values in a prompt would remain probabilistic.

Provider-enforced structured output is useful for other unstructured fields,
but it adds no value to an amenity list that can be parsed directly.

### Fuzzy or semantic resolution

Similarity is not identity. Tested fuzzy clusters incorrectly joined
restaurant with bar, fitness center with business center, valet with
self-parking, view types with river cruise, and a hammam with architecture.
Transitive merging makes a single bridging phrase capable of collapsing
otherwise distinct concepts.

This is too risky for automatic graph mutation and too complicated for the
workshop problem.

### Full-text indexing

A full-text index can improve name lookup. It cannot make two Hotel
relationships point to the same Amenity node, so it does not repair traversal.

### Reviewed merge map or governed catalog

A reviewed alias map and stable concept catalog would be appropriate if many
independent producers supplied changing vocabularies. This workshop has one
fixed corpus whose amenity values are already explicit and consistent.

Adding catalog versions, lifecycle states, alias approval, quarantine, and
migration tooling would obscure the introductory lesson without solving a
problem the workshop actually has.

### Legacy migration

The source corpus is committed and the graph is disposable. Rebuilding it with
the corrected pipeline is simpler and easier to verify than migrating the
LLM-generated amenity slice in place.

## Recommended implementation

### Deterministic amenity parser

Add a small shared parser that:

- Locates the single `## Hotel Amenities` section.
- Reads only its bullet list and stops before the following subsection.
- Trims formatting while preserving the authored label.
- Rejects a missing, repeated, or malformed section.
- Returns the source filename and labels needed for provenance.

The parser should not interpret later prose. This avoids turning sentences such
as “Pool facilities are not available” into positive amenities and keeps the
workshop contract easy to state.

### Simple graph materialization

For every parsed label:

- Match the Hotel through its Document and Chunk provenance.
- Require exactly one Hotel for the source document.
- Merge one shared Amenity by its canonical source name.
- Merge one `OFFERS_AMENITY` relationship from that Hotel.
- Keep source filename or Chunk provenance so the result remains inspectable.

Create a uniqueness constraint on `Amenity.name`. No `amenity_id`, alias file,
category hierarchy, or catalog version is needed for this fixed corpus.

### Safer LLM extraction boundary

Use a schema for the LLM pipeline that excludes Amenity and
`OFFERS_AMENITY`. Keep those types in the overall workshop graph contract and
write them only through the deterministic materializer.

Disable the pipeline's global exact-name resolver. For this workshop, keeping
Policy and Service nodes document-scoped is safer and simpler than teaching
type-specific entity-resolution policy. Shared Amenity nodes still provide the
connected-context traversal the workshop is meant to demonstrate.

Change extraction failure handling so a parse error cannot be printed as a
successful document. Require each Document to resolve to exactly one Hotel
before the build or learner ingestion succeeds.

### Rebuild rather than migrate

Run the corrected full build from the committed corpus and generate a new
prebuilt graph artifact. Keep the five held-out documents out of that artifact
and let the existing additive build process ingest them during the workshop.
The additive path must invoke the same amenity parser and materializer.

The rebuild is facilitator and release work. Participants should not spend
workshop time rebuilding hundreds of documents or learning migration mechanics.

## Implementation plan

### Phase 1: Add deterministic amenity handling

**Status: Pending**

**Outcome:** The same source list always produces the same shared Amenity nodes.

**Checklist:**

- [ ] Add the shared amenity-section parser under `notebooks/workshop`.
- [ ] Add the idempotent Amenity and `OFFERS_AMENITY` materializer.
- [ ] Add the uniqueness constraint for `Amenity.name`.
- [ ] Resolve each Hotel through Document and Chunk provenance rather than its
  generated display name.
- [ ] Reject missing, repeated, or malformed amenity sections.
- [ ] Reject a source document that does not resolve to exactly one Hotel.
- [ ] Keep hotel-specific amenity qualifiers off the shared Amenity node.

**Validation:** All 300 documents parse to 1,632 amenity assertions and 65
distinct names. A repeated run produces no duplicate nodes or relationships.

**Completion criteria:** Amenity identity is completely independent of LLM
wording and every edge can be traced to a source document.

### Phase 2: Integrate the corrected build and rebuild the graph

**Status: Pending**

**Outcome:** Full, prebuilt, and learner-additive paths use the same extraction
boundary.

**Checklist:**

- [ ] Separate the overall graph contract from the schema passed to the LLM.
- [ ] Exclude Amenity and `OFFERS_AMENITY` from LLM extraction.
- [ ] Disable global exact-name entity resolution.
- [ ] Make component failures fail the affected document visibly.
- [ ] Require one Hotel per source document in canary and final readiness
  checks.
- [ ] Invoke deterministic amenity materialization from both full and additive
  build flows.
- [ ] Rebuild the graph from the committed source corpus.
- [ ] Generate the new prebuilt graph artifact with the five held-out documents
  omitted.

**Validation:** The complete build has 300 distinct Hotels, 65 Amenity nodes,
and 1,632 `OFFERS_AMENITY` assertions. The prebuilt graph plus five live
documents produces the same final amenity projection as the complete build.

**Completion criteria:** No supported build path can create an Amenity name or
merge a Hotel identity through LLM output.

### Phase 3: Add focused tests and update the workshop story

**Status: Pending**

**Outcome:** The fix is protected without adding participant-facing complexity.

**Checklist:**

- [ ] Test parser boundaries, corpus totals, idempotence, and source provenance.
- [ ] Add regressions for Chicago shared WiFi, 175 pool-listing documents, the
  explicit pool negation, the four missing Hotels, and the four cross-city
  duplicate names.
- [ ] Update readiness checks so Document and Chunk counts cannot substitute
  for Hotel and relationship completeness.
- [ ] Re-run affected Phase 1.5 reference facts and evaluation evidence.
- [ ] Update the Module 1 notebook, README, and workshop content with the
  deterministic extraction boundary.
- [ ] Demonstrate that both Chicago hotels traverse to the same authored WiFi
  node.
- [ ] Keep catalog governance, migration, and entity-resolution theory out of
  the required four-hour participant path.

**Validation:** Tests fail on the old graph defects and pass on both the full
build and the prebuilt-plus-live build.

**Completion criteria:** A participant can explain the implementation in one
sentence and inspect the source-to-graph evidence without learning a production
governance system.

## Overall completion criteria

- [ ] The same 300 documents always produce 300 distinct Hotels, 65 Amenity
  nodes, and 1,632 hotel-to-amenity assertions.
- [ ] Both Chicago hotels share the same `Complimentary High-Speed Wifi` node.
- [ ] An explicit negative statement outside the authoritative list cannot
  become a positive amenity.
- [ ] Duplicate Hotel display names in different cities remain distinct.
- [ ] The prebuilt and learner paths use the same deterministic amenity logic.
- [ ] The graph is rebuilt from source rather than migrated from legacy
  generated values.
- [ ] The participant-facing explanation remains appropriate for an
  introductory four-hour workshop.
