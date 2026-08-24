# Fix Defects Implementation Plan, Version 3

Date: 2026-08-23
Source reviewed: `workfolder/defects-v2.md`, Phases 1 through 6
Status: In progress

This plan supersedes the pending implementation work in
`workfolder/defects-v2.md`, including its Phases 5.5, 7, and 8. That document
remains the historical design and audit record. This file is the source of
truth for the remaining implementation and validation work.

## Goal

Finish the redesign work that remains after Phases 1 through 6. Preserve the
connected-context curriculum, close the deterministic contract gaps, remove
working-directory dependencies, remove evaluation infrastructure that is out of
scope for a simple workshop, and produce current live evidence for Modules 1
through 3.

## Verified baseline

- The current offline suite passes 210 tests after removing 58 FAISS and
  Phase 1.5 benchmark tests and adding the focused Phase 1 and Phase 2
  regressions.
- The repository checker passes notebook parsing, Python compilation, content
  links, content weights, folder-to-page parity, image synchronization, stale
  path checks, and named-path checks.
- Active Module 2 and Module 3 paths and ownership match the redesigned
  curriculum.
- The active Module 2 notebook contains the four locked questions and the core
  Vector, Hybrid, Vector-Cypher, fixed Cypher, and optional Text2Cypher patterns.
- The Module 2 decision-tree source and export are synchronized in both image
  trees. The unsupported comparison image is absent.

These results prove offline implementation health. They do not complete live
semantic acceptance or prove that all promised evidence fields appear during a
current notebook run.

## Defects found in the Phase 1 through 6 review

| ID | Priority | Finding | Required correction |
| --- | --- | --- | --- |
| V3-1 | Release blocker | The optional unpinned Module 1 demo uses a real held-out filename without passing that filename as document metadata. Its cleanup can miss the generated `Document` and leave demo data behind. | Give the demo a unique identity, carry it through metadata, and delete only that identity. Prove that participant data remains unchanged. |
| V3-2 | Release blocker | Working-directory assumptions remain in Module 1, Module 3, later notebooks, `prepare_graph.py`, and held-out source loading. Module 2 has a stronger locator, but the workshop does not use one supported path contract consistently. | Resolve repository, notebook, corpus, build, and staging paths from file or notebook identity. Test every supported launch directory. |
| V3-3 | High | The locked Cairo fixture requires hotel ID `81393d51-1df3-4f53-b58e-e4cda9736fd7`, but the shared readiness query and `SourceFixture` contract do not validate that ID before retrieval. | Add the hotel ID to readiness data, validation, and negative regression tests. |
| V3-4 | High | The fixed Chicago Cypher block shows the query, parameters, candidate records, qualifiers, and exclusions, but it does not fully follow the shared evidence display contract. It omits an explicit retriever label, approximate context size, requested-field gaps, and structured provenance per record. | Normalize the fixed-Cypher display with the other retrieval blocks and assert the displayed fields through behavioral tests. |
| V3-5 | Release blocker | The available live Module 2 execution predates the current evidence-first notebook. It used an earlier arrival question and an earlier cell layout. It cannot validate the locked Phase 1 contract now in the source notebook. | Execute the current Modules 1 through 3 in order and retain a fresh validation record tied to the current source revision. |
| V3-8 | Medium | Phase 5 content tests use a curated learner-file list. Current scans find no stale redesign claims, but a new active page or notebook can fall outside that list. | Derive learner-facing scan coverage from active notebook and workshop-content trees, with narrow documented exclusions for historical evidence and planning records. |
| V3-9 | Critical | The Module 2 notebook and workshop page direct learners to the lite preparation path even when Module 1 already prepared the hosted graph. A readiness mismatch can reach the destructive rebuild path without an explicit rebuild request and erase the restored graph and learner work. | Make the hosted instructions readiness-only and require explicit rebuild intent before any whole-graph deletion. Test the refusal path against a populated graph. |
| V3-10 | High | The decision tree assigns the Chicago spa-and-pool example to Text2Cypher, while the locked contract and notebook use reviewed fixed Cypher as the deterministic acceptance path. Module 3 also says Module 2 compares the selected Hybrid-Cypher configuration even though Module 2 only selects it. | Give reviewed fixed Cypher its own diagram branch, mark Text2Cypher optional and governed, and correct the Module 2 and Module 3 learner prose. |
| V3-11 | High | The Vector-Cypher context-size calculation counts the source text twice and includes representation punctuation. The resulting comparison can teach the opposite of the intended compact-context lesson. | Report structured-field size and source-text size separately, using the same measurement rules for every arm. |
| V3-12 | Medium | The Chicago query selects its candidates by the two expected source filenames, and the Module 2 readiness gate still requires aggregation and counting fixtures from retired lessons. | Select Chicago candidates by city, validate expected source identities separately, and limit Module 2 readiness to facts used by current examples. |
| V3-13 | High | The active Module 3 architecture PNG has no editable source. Two Module 1 PNGs are unreferenced orphans, and the diagram authoring notes document an image path that active pages do not use. | Create the missing editable source, remove the orphans, correct the authoring notes, and generalize diagram ownership tests. |
| V3-14 | Medium | Several notebook failures still produce bare assertions, source provenance is joined through a client-side full-corpus text map, Text2Cypher reports a truncated display count as the result count, and Vector-Cypher can silently drop semantic hits with no extracted Hotel. | Make failures diagnostic, resolve provenance per result, separate total and displayed counts, and expose graph-enrichment misses. |

## Assumptions

- The locked Module 2 title, questions, expected results, and Module 3 boundary
  remain unchanged.
- The published graph dump remains the starting artifact. Graph rebuilding is
  required only if a fixture check proves that the artifact violates the locked
  contract.
- The hosted learner path reaches Module 2 with a prepared graph. Its default
  action is validation, not graph reconstruction.
- Whole-graph reconstruction is a facilitator or self-paced operation and
  requires explicit destructive intent.
- `--rebuild` is required before any whole-graph build, including an empty
  graph. `--resume` also counts as explicit destructive intent for its
  checkpoint workflow.
- Repository root, `notebooks/`, and the active module directory are supported
  launch locations for notebook and helper workflows. Each notebook must work
  from its own module directory; notebooks do not need to work when launched
  from another module's directory.
- Optional Text2Cypher may report a blocked state when verified reader
  credentials are unavailable. Its live execution is outside the deterministic
  completion gate.
- FAISS and the optional Phase 1.5 comparison benchmark are retired. The
  workshop makes no comparative retrieval-rate claim and carries no benchmark
  runner, evaluator, report pipeline, or publication gate.
- Existing unrelated working-tree changes must remain intact.

## Risks

- The Module 1 cleanup regression writes temporary graph data. Run it only
  against an approved workshop graph and verify the graph state before and after
  the test.
- Changing graph preparation from implicit repair to explicit rebuild changes a
  facilitator workflow. Update its documentation and failure messages in the
  same phase so a safe refusal is actionable.
- Path changes affect imports, corpus discovery, deployment staging, notebook
  execution, and environment loading. A partial conversion can make one launch
  mode pass while another silently reads the wrong assets.
- Live Neo4j and Bedrock validation uses credentials and incurs model cost.
- Live notebook logs can contain environment and execution details. Keep them
  local and do not copy credentials into the short validation record.
- Live validation reads credentials and service configuration from `.env`.
  Validation records must not copy credentials or secret values.

## Phase 1: Make graph preparation safe and repair deterministic contracts

**Status:** Complete

**Outcome:** Module 2 cannot erase a prepared graph without explicit rebuild
intent, the optional demo cleans up only its own data, and every required
example enforces and displays the complete locked contract.

**Checklist:**

- [x] Remove the unconditional lite-build prerequisite from the Module 2
  notebook and workshop page. State that Module 1 already prepared the hosted
  graph.
- [x] Make the Module 2 readiness failure direct learners to the non-destructive
  check-only path before any rebuild guidance.
- [x] Keep lite and full preparation instructions under an explicit
  from-scratch or self-paced heading.
- [x] Change `prepare_graph.py` so an unexpected or incomplete populated graph
  returns an actionable failure unless the caller explicitly requested a
  rebuild.
- [x] Require explicit rebuild intent before `prepare_graph.py` can reach the
  whole-graph clearing path. Report the observed and expected graph sizes in the
  refusal message.
- [x] Require `--rebuild` for builds against empty graphs as well as populated
  graphs. Treat `--resume` as explicit destructive intent for the checkpoint
  workflow.
- [x] Add regression tests proving that default preparation and check-only mode
  never call the destructive build path on a populated graph.
- [x] Give the optional unpinned demo a filename reserved solely for temporary
  demo data. Do not reuse a held-out source filename.
- [x] Pass the temporary filename through the extraction metadata so the
  generated `Document`, `Chunk`, and extracted entities can be found by the
  cleanup path.
- [x] Clear the same temporary filename in a guaranteed cleanup block, including
  extraction failure cases.
- [x] Replace the learner prose that says the demo leaves data behind with an
  accurate cleanup promise after validation passes.
- [x] Add a regression that creates participant data first, runs the demo
  cleanup, and proves the participant source path and hotel remain unchanged.
- [x] Add `hotel_id` to the Cairo source fixture, readiness query, readiness
  validator, and focused negative tests.
- [x] Make readiness fail before retrieval when the Cairo ID is missing,
  duplicated, or different from the locked value.
- [x] Remove retired aggregation and counting fixtures from the Module 2
  notebook readiness gate.
- [x] Retain broader graph-health fixtures in build-time validation where they
  still protect downstream tools, and rename them for the behavior they protect.
- [x] Select Chicago candidates through a city predicate rather than passing the
  two expected source filenames as the candidate set.
- [x] Keep the expected Chicago filenames in readiness and result validation so
  the city-based query remains deterministic.
- [x] Give the fixed Chicago block an explicit pattern name and configuration,
  then display candidate and qualifying record context size, absent requested
  fields, source filename, and provenance.
- [x] Assert those Chicago display fields through structured notebook-contract
  tests instead of checking only for source-code strings.
- [x] Replace the Vector-Cypher blended context-size number with separate
  measurements for structured fields and source text.
- [x] Apply the same measurement definitions to the vector arm so the learner
  compares equivalent evidence.
- [x] Replace the full-corpus client-side text map with provenance resolution
  tied to each retrieval result.
- [x] Make Vector-Cypher surface semantic hits that lack extracted Hotel context
  and explain why enrichment returned fewer complete records.
- [x] Give every acceptance assertion an actionable message containing the
  expected fact and observed evidence.
- [x] Report total Text2Cypher records separately from the bounded set displayed
  in the notebook.
- [x] Keep generated Text2Cypher outside the deterministic acceptance path.

**Validation:**

- A populated graph cannot enter the whole-graph clearing path without an
  explicit rebuild request.
- The hosted Module 2 instructions perform readiness checks and preserve Module
  1 learner work.
- The demo leaves graph counts and participant source paths unchanged after both
  success and simulated failure.
- Cairo readiness rejects every wrong-ID variant before a retriever is created.
- Module 2 starts without requiring Paris aggregation, pool counting, or other
  retired-lesson fixtures.
- The Chicago query discovers candidates by city and still returns the two
  locked source records, one qualifier, and one explicit exclusion.
- The Chicago block exposes all applicable fields from the evidence display
  contract and still returns two candidates, one qualifier, and one explicit
  exclusion.
- Context-size output counts each character once and separates structured fields
  from source text.
- Missing graph enrichment, provenance, assertion failures, and bounded
  Text2Cypher displays are explicit in notebook output.
- Focused Module 1 cleanup, Module 2 fixture, and notebook-contract tests pass.

**Notes:** This phase closes V3-1, V3-3, V3-4, V3-9, V3-11, V3-12, and V3-14.
It must finish before any new live notebook acceptance run.

**Validation result:** Complete offline. Phase 1 focused and related tests pass
as part of the current 210-test setup suite. The repository checker and whitespace
validation pass. Live semantic acceptance remains Phase 5 work.

## Phase 2: Establish one working-directory contract

**Status:** Complete

**Outcome:** Active notebooks and helper scripts find the same repository assets
from every supported launch location.

**Checklist:**

- [x] Define one documented base-path contract for the repository root,
  notebooks root, current module, corpus archive, extracted data, shared package,
  reservation command, and deployment build context.
- [x] Preserve the documented `WORKSHOP_NOTEBOOKS_DIR` override and validate it
  before use.
- [x] Update Module 1 bootstrap and held-out loading so they do not derive paths
  from the process working directory.
- [x] Update `prepare_graph.py` so its corpus archive, extracted data, environment
  files, and imports resolve from the script location or shared base contract.
- [x] Apply the same locator to Modules 3 through 6 where imports, requirements,
  cleanup utilities, or deployment staging still use the process working
  directory.
- [x] Make the notebook runner set and report each notebook's execution directory
  explicitly.
- [x] Document the supported launch locations in the root and module setup prose.
- [x] Add path-contract tests from the repository root, notebooks root, and each
  notebook's own active module directory. Tests must prove that every resolved
  asset is the same file in all three cases.
- [x] Add a fresh-clone path test that runs without extracted `data/`, caches, or
  notebook output directories.

**Validation:**

- Path tests pass from all supported launch locations.
- Module 1 finds held-out documents and Module 2 finds its corpus archive without
  relying on prior directory changes.
- Modules 3 through 6 import the shared package and locate their module assets
  consistently.
- The repository checker and notebook runner tests pass from outside the
  `notebooks/` directory.

**Notes:** This phase closes V3-2. Keep path resolution independent from live
credentials so most failures remain testable offline.

**Validation result:** Complete offline. Path resolution tests cover Modules 1
through 6, the held-out corpus helper, `prepare_graph.py`, and the supported
launch locations without generated data. The combined 210-test setup suite and
repository checker pass.

## Phase 3: Retire out-of-scope comparison infrastructure

**Status:** Complete

**Outcome:** The workshop contains only the Neo4j retrieval paths it teaches.
FAISS and the optional Phase 1.5 benchmark no longer add dependencies, artifacts,
commands, tests, or publication machinery.

**Checklist:**

- [x] Remove the committed FAISS index, corpus mapping, manifest, loader, and
  rebuild utility.
- [x] Remove the direct FAISS dependency and regenerate the workshop lock file.
- [x] Remove the Phase 1.5 benchmark harness, evaluator, merge, report,
  validation, evidence-capture runner, and their dedicated tests.
- [x] Remove the Phase 1.5 evidence-retention policy and local benchmark output.
- [x] Keep the standalone notebook smoke runner, additive graph validation, and
  active Modules 1 through 6 tests.
- [x] Remove active learner and authoring references to FAISS and the optional
  benchmark.
- [x] Run the full offline suite, repository checker, dependency scan, and stale
  reference scan after all retirement deletions are integrated.

**Validation:**

- No tracked active file imports FAISS or names the retired benchmark commands or
  artifacts.
- Workshop dependencies and the lock file contain no direct `faiss-cpu`
  dependency.
- The normal workshop suite and repository checker pass without replacement
  benchmark infrastructure.

**Notes:** V3-6 was a publication safeguard for infrastructure the workshop no
longer needs. Retirement removes that publication path instead of replacing it
with a more complex validator.

**Validation result:** Complete. The simplified offline suite passes 210 tests,
the repository checker passes, the workshop lock resolves offline, and active
tracked code and content contain no retired FAISS or benchmark references.

## Phase 4: Complete release-inventory and learner-surface coverage

**Status:** Pending

**Outcome:** Every durable Phase 1 through 6 artifact remains present in a fresh
clone, and every active learner surface participates in semantic regression
checks.

**Checklist:**

- [ ] Replace the curated learner-file list with discovery of active notebook
  markdown, module READMEs, workshop pages, root navigation, summary, and wrap-up
  content.
- [ ] Keep exclusions narrow and explicit for planning records, generated
  output, caches, and retired local directories.
- [ ] Re-run stale-title, retired-path, module-number, unsupported-claim,
  `Chunk` terminology, model-variability, extraction-boundary, and handoff scans
  across the discovered learner surfaces.
- [ ] Add a reviewed fixed-Cypher branch to the Module 2 decision tree with the
  Chicago spa-and-pool example and its candidate, qualifier, and exclusion
  evidence.
- [ ] Give optional Text2Cypher a separate flexible structured example and label
  its reader-credential and read-only planner boundary.
- [ ] Update the diagram contract test so it enforces the fixed-Cypher and
  Text2Cypher example ownership instead of merely requiring both labels.
- [ ] Create an editable source for the active Module 3 grounded-agent
  architecture diagram and synchronize its export across both image trees.
- [ ] Remove the two unreferenced Module 1 comparison PNGs from both image trees.
- [ ] Correct the image path in the diagram authoring usage notes.
- [ ] Generalize diagram tests so every retained PNG has a documented editable
  source and an active consumer, with any approved exception named explicitly.
- [ ] Correct Module 3 prose so it says Module 2 selects Hybrid-Cypher for the
  application but does not execute it as a comparison arm.
- [ ] Add reviewed fixed Cypher to the Module 2 content table and label
  Text2Cypher optional and governed.
- [ ] Confirm that both image trees contain the same editable sources and exports
  and that no unsupported comparison image has returned.
- [ ] Review the final tracked-file inventory for unintended generated or local
  evidence files.

**Validation:**

- A fresh-clone inventory contains every active contract file and test required
  by the workshop.
- The learner-surface gate covers every active page and notebook without hiding
  active files behind broad directory exclusions.
- The Module 2 decision tree assigns Chicago to reviewed fixed Cypher and gives
  optional Text2Cypher a distinct governed role.
- The active Module 3 architecture image has an editable source, and no
  unreferenced Module 1 image remains in either image tree.
- Module 2 and Module 3 prose describes the patterns the notebooks actually run
  and the Hybrid-Cypher handoff they select.
- No credential, generated notebook output, or retired benchmark artifact enters
  the release set.

**Notes:** This phase closes V3-8, V3-10, and V3-13. The diagram source,
exports, ownership tests, and learner prose must change together.

## Phase 5: Run current live semantic acceptance

**Status:** Pending

**Outcome:** The current source notebooks run from graph build through grounded
agent and produce the exact evidence promised by the locked learning contract.

**Checklist:**

- [ ] Start from the published graph artifact or another explicitly approved
  clean workshop graph and record its initial identity.
- [ ] As a safety preflight, run the Module 2 non-destructive readiness path
  against that populated graph and confirm that graph counts and existing
  learner data do not change. This preflight is not the Module 2 execution in
  the ordered acceptance run.
- [ ] Execute Module 1, including the repaired optional demo cleanup test, and
  confirm that the final graph contains only intended workshop data.
- [ ] Execute the current Module 2 notebook. Do not reuse the earlier executed
  notebook as acceptance evidence.
- [ ] Verify the semantic paraphrase result contains
  `hotel-cairo-001.txt` and `3:00 PM` in the top three.
- [ ] Verify the Hybrid result contains `hotel-chicago-001.txt`, `60611`,
  Windward Mile Tower, and the supported cancellation policy in the top five.
- [ ] Record the live vector rank for the Chicago source without treating it as
  a permanent constant.
- [ ] Verify the Vector-Cypher Cairo record contains the locked hotel name,
  hotel ID, rating, source filename, required amenity terms, source text,
  semantic score, relationship types, field provenance, separate structured and
  source-text sizes, and no missing requested fields.
- [ ] Verify that graph-enrichment misses remain visible and do not silently
  reduce the reported semantic result set.
- [ ] Verify the fixed Chicago filter returns two candidates, only Lakeview
  Horizon Suites as the qualifier, and Windward Mile Tower as the explicit
  exclusion.
- [ ] Verify optional Text2Cypher either passes the reader-role and planner gates
  or reports a clear blocked state without executing generated Cypher.
- [ ] Execute Module 3 immediately after Module 2 and verify grounded answering,
  abstention, guest-limit enforcement, and idempotent reservation retries.
- [ ] Record source revision, service and library versions, graph counts, model
  ID, embedding contract, AWS region, Neo4j database, and execution timestamps.
- [ ] Read live service configuration from `.env` without copying credentials
  or secret values into evidence.
- [ ] Save a short tracked Markdown validation record containing the commit,
  graph identity, non-secret environment and library versions, timestamps, and
  acceptance results.
- [ ] Keep executed notebooks and detailed logs as local diagnostics. Publish
  them only after assigning an approved immutable URI and checksum.

**Validation:**

- Modules 1 through 3 pass in order against the same configured environment.
- The non-destructive preparation path preserves the starting graph and learner
  work.
- Every locked Module 2 result and evidence field is visible in the executed
  notebook.
- The live record corresponds to the current notebook questions and current
  source revision.
- The repaired demo leaves no temporary graph data and Module 3 completes after
  the retrieval handoff.

**Notes:** This phase closes V3-5 and the live portion of V2-15. It is the first
phase that requires external credentials and model cost.

## Phase 6: Reconcile release state and downstream handoffs

**Status:** Pending

**Outcome:** Repository state, release documentation, published artifacts, and
later-module handoffs all describe the same completed redesign.

**Checklist:**

- [ ] Smoke-check the Module 4 and Module 5 references to Module 2 retrieval
  selection, Module 3 grounding, and the protected reservation command without
  creating deployment resources.
- [ ] Validate all internal links, notebook paths, navigation, and editable
  diagram sources after the final changes.
- [ ] Re-run the full offline test suite, repository checker, notebook code-cell
  compilation, shell syntax checks, and whitespace validation.
- [ ] Reconcile the clean-graph final-state record with the actual tracked
  artifact names, current source revision, publication state, and redesign
  completion state.
- [ ] Update current test totals in release summaries while retaining clearly
  labeled historical totals where they describe an earlier result.
- [ ] Independently verify the published static graph dump size and SHA-256.
- [ ] Review the final change set for unrelated edits, generated notebook
  output, raw evidence, credentials, caches, and accidental artifact deletion.

**Validation:**

- Offline and live gates both pass after the final source changes.
- Modules 4 and 5 identify the correct upstream retrieval and write components.
- Release documentation names only files that exist and reports the actual
  graph artifact, source revision, test count, evidence retention, and
  completion state.
- The redesign is marked complete only after every release blocker in this plan
  is closed.

## Completion criteria

- The optional Module 1 demo creates and removes only its own temporary data.
- Module 2 preparation cannot clear a populated graph without explicit rebuild
  intent, and hosted instructions use the non-destructive readiness path.
- All active notebooks and helpers use one tested base-path contract.
- Cairo readiness enforces the locked hotel ID before retrieval begins.
- Module 2 readiness depends only on current learner examples.
- The Chicago structured query discovers candidates by city and validates the
  expected source identities separately.
- Every deterministic Module 2 block displays all applicable evidence and
  provenance fields.
- Context-size comparisons count source text once and distinguish it from named
  structured fields.
- Acceptance failures, Text2Cypher display limits, and graph-enrichment misses
  are explicit and actionable.
- The current Modules 1 through 3 pass in order with fresh live evidence.
- FAISS artifacts, dependencies, rebuild utilities, and tests are absent.
- The optional Phase 1.5 benchmark, evaluator, report pipeline, and evidence
  retention machinery are absent.
- Active learner scans cover the complete current learner surface.
- The Module 2 diagram and learner prose distinguish reviewed fixed Cypher from
  optional Text2Cypher.
- Every retained active diagram has an editable source and an active consumer.
- Module 4 and Module 5 handoffs use the redesigned module ownership and paths.
- Release records, test totals, graph dump identity, and completion status agree.
- No active learner or release surface publishes a comparative benchmark claim.
