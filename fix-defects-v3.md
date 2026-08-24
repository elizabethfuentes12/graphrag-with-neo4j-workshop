# Fix Defects Implementation Plan, Version 3

Date: 2026-08-23
Source reviewed: `workfolder/defects-v2.md`, Phases 1 through 6
Status: Pending

## Goal

Finish the redesign work that remains after Phases 1 through 6. Preserve the
connected-context curriculum, close the deterministic contract gaps, remove
working-directory dependencies, strengthen evaluation publication safeguards,
and produce current live evidence for Modules 1 through 3.

## Verified baseline

- The full offline suite passes 220 tests.
- The repository checker passes notebook parsing, Python compilation, content
  links, content weights, folder-to-page parity, image synchronization, stale
  path checks, and named-path checks.
- Active Module 2 and Module 3 paths and ownership match the redesigned
  curriculum.
- The active Module 2 notebook contains the four locked questions and the core
  Vector, Hybrid, Vector-Cypher, fixed Cypher, and optional Text2Cypher patterns.
- The Module 2 decision-tree source and export are synchronized in both image
  trees. The unsupported comparison image is absent.
- The Phase 1.5 FAISS baseline is separate from the learner path and its focused
  offline tests pass.

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
| V3-6 | High for publication | The evaluator harness creates strict samples, but the evidence gate trusts recorded flags and final labels. It does not recompute vote winners, vote counts, rationale ownership, or exact raw-response validity. The report can treat shallow flag checks as sufficient for publishable grounding labels. | Make one validator authoritative for both the gate and report. Recompute all derived judge fields from preserved samples and reject inconsistencies. |
| V3-7 | Release blocker | The compact Phase 1.5 policy and decision records are allowed by ignore rules but are still absent from Git's tracked-file inventory. The Phase 6 claim that a fresh clone can locate them is therefore unproven. Several new contract tests and the evaluator contract module are also untracked. | Add every intended durable file to the release change set and verify that local-only raw evidence remains excluded. |
| V3-8 | Medium | Phase 5 content tests use a curated learner-file list. Current scans find no stale redesign claims, but a new active page or notebook can fall outside that list. | Derive learner-facing scan coverage from active notebook and workshop-content trees, with narrow documented exclusions for historical evidence and planning records. |

## Assumptions

- The locked Module 2 title, questions, expected results, and Module 3 boundary
  remain unchanged.
- The published graph dump remains the starting artifact. Graph rebuilding is
  required only if a fixture check proves that the artifact violates the locked
  contract.
- Repository root, `notebooks/`, and the active module directory are supported
  launch locations for notebook and helper workflows.
- Optional Text2Cypher may report a blocked state when verified reader
  credentials are unavailable. Its live execution is outside the deterministic
  completion gate.
- The optional 240-trial benchmark remains supported but is not required for
  workshop release. Any future publication of comparative rates requires a new
  valid benchmark and durable raw evidence.
- Existing unrelated working-tree changes must remain intact.

## Risks

- The Module 1 cleanup regression writes temporary graph data. Run it only
  against an approved workshop graph and verify the graph state before and after
  the test.
- Path changes affect imports, corpus discovery, deployment staging, notebook
  execution, and environment loading. A partial conversion can make one launch
  mode pass while another silently reads the wrong assets.
- Live Neo4j and Bedrock validation uses credentials and incurs model cost.
- Tightening the evaluator gate will reject earlier or manually edited evidence
  files. Historical files should remain historical instead of being rewritten
  to satisfy the new schema.
- Raw evidence contains environment and execution details. Keep it local unless
  an approved durable location and retention policy are recorded.

## Phase 1: Repair deterministic data and evidence contracts

**Status:** Pending

**Outcome:** The optional demo cleans up only its own data, and every required
Module 2 example enforces and displays the complete locked contract.

**Checklist:**

- [ ] Give the optional unpinned demo a filename reserved solely for temporary
  demo data. Do not reuse a held-out source filename.
- [ ] Pass the temporary filename through the extraction metadata so the
  generated `Document`, `Chunk`, and extracted entities can be found by the
  cleanup path.
- [ ] Clear the same temporary filename in a guaranteed cleanup block, including
  extraction failure cases.
- [ ] Replace the learner prose that says the demo leaves data behind with an
  accurate cleanup promise after validation passes.
- [ ] Add a regression that creates participant data first, runs the demo
  cleanup, and proves the participant source path and hotel remain unchanged.
- [ ] Add `hotel_id` to the Cairo source fixture, readiness query, readiness
  validator, and focused negative tests.
- [ ] Make readiness fail before retrieval when the Cairo ID is missing,
  duplicated, or different from the locked value.
- [ ] Give the fixed Chicago block an explicit pattern name and configuration,
  then display candidate and qualifying record context size, absent requested
  fields, source filename, and provenance.
- [ ] Assert those Chicago display fields through structured notebook-contract
  tests instead of checking only for source-code strings.
- [ ] Keep generated Text2Cypher outside the deterministic acceptance path.

**Validation:**

- The demo leaves graph counts and participant source paths unchanged after both
  success and simulated failure.
- Cairo readiness rejects every wrong-ID variant before a retriever is created.
- The Chicago block exposes all applicable fields from the evidence display
  contract and still returns two candidates, one qualifier, and one explicit
  exclusion.
- Focused Module 1 cleanup, Module 2 fixture, and notebook-contract tests pass.

**Notes:** This phase closes V3-1, V3-3, and V3-4. It must finish before any new
live notebook acceptance run.

## Phase 2: Establish one working-directory contract

**Status:** Pending

**Outcome:** Active notebooks and helper scripts find the same repository assets
from every supported launch location.

**Checklist:**

- [ ] Define one documented base-path contract for the repository root,
  notebooks root, current module, corpus archive, extracted data, shared package,
  reservation command, and deployment build context.
- [ ] Preserve the documented `WORKSHOP_NOTEBOOKS_DIR` override and validate it
  before use.
- [ ] Update Module 1 bootstrap and held-out loading so they do not derive paths
  from the process working directory.
- [ ] Update `prepare_graph.py` so its corpus archive, extracted data, environment
  files, and imports resolve from the script location or shared base contract.
- [ ] Apply the same locator to Modules 3 through 6 where imports, requirements,
  cleanup utilities, or deployment staging still use the process working
  directory.
- [ ] Make the notebook runner set and report each notebook's execution directory
  explicitly.
- [ ] Document the supported launch locations in the root and module setup prose.
- [ ] Add path-contract tests from the repository root, notebooks root, and each
  active module directory. Tests must prove that every resolved asset is the
  same file in all three cases.
- [ ] Add a fresh-clone path test that runs without extracted `data/`, caches, or
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

## Phase 3: Harden Phase 1.5 evidence publication controls

**Status:** Pending

**Outcome:** A report can mark judge labels publishable only after one strict,
recomputed evidence contract passes.

**Checklist:**

- [ ] Centralize run validation so the command-line gate and report generator
  apply the same rules.
- [ ] Parse each preserved raw judge response again and confirm that its exact
  schema and normalized values match the recorded sample.
- [ ] Recompute factuality and grounding winners from all preserved samples.
- [ ] Reject unresolved ties, mismatched winning labels, incorrect vote counts,
  and rationales that did not come from a sample casting the winning label.
- [ ] Persist enough evidence metadata to prove that the judge received the full
  evidence shown to the evaluated agent. Validate the retained character count
  and integrity value instead of trusting a Boolean flag alone.
- [ ] Reject a report request when the strict gate fails. Historical reports may
  render only with the existing invalid-grounding warning and without
  publishable rates.
- [ ] Pin the complete FAISS compatibility manifest and evaluator settings when
  merging worker slices.
- [ ] Add mutation tests for altered raw responses, forged completion flags,
  changed labels, wrong vote counts, unrelated rationales, manifest drift, and
  unbalanced cells.
- [ ] Confirm that the optional benchmark still requires ten trials in every
  question, arm, and prompt-condition cell.

**Validation:**

- The gate rejects every inconsistent derived field even when stored status
  flags claim success.
- The report and evidence gate agree on whether grounding labels are publishable.
- No historical Phase 1.5 grounding label becomes valid through schema
  migration or report regeneration.
- Focused evaluator, merge, report, retention, FAISS, and release-workflow tests
  pass.

**Notes:** This phase closes V3-6. Running the paid benchmark is deferred unless
the release makes comparative rate or stability claims.

## Phase 4: Complete version-control and learner-surface coverage

**Status:** Pending

**Outcome:** Every durable Phase 1 through 6 artifact is present in a fresh clone,
and every active learner surface participates in semantic regression checks.

**Checklist:**

- [ ] Add the Phase 1.5 retention policy, findings, and amenity recheck to the
  intended tracked release set.
- [ ] Add the evaluator contract and all new focused contract tests to the same
  release set.
- [ ] Confirm that raw trials, detailed generated reports, logs, executed
  notebooks, archived notebooks, and release-smoke bundles remain local-only.
- [ ] Replace the curated learner-file list with discovery of active notebook
  markdown, module READMEs, workshop pages, root navigation, summary, and wrap-up
  content.
- [ ] Keep exclusions narrow and explicit for planning records, historical
  evidence, generated output, caches, and retired local directories.
- [ ] Re-run stale-title, retired-path, module-number, unsupported-claim,
  `Chunk` terminology, model-variability, extraction-boundary, and handoff scans
  across the discovered learner surfaces.
- [ ] Confirm that both image trees contain the same editable sources and exports
  and that no unsupported comparison image has returned.
- [ ] Review the final tracked-file inventory for unintended generated or local
  evidence files.

**Validation:**

- A fresh-clone inventory contains every compact retained artifact and every
  contract test required by Phases 1 through 6.
- The learner-surface gate covers every active page and notebook without hiding
  active files behind broad directory exclusions.
- Local-only evidence remains ignored and no credential or generated notebook
  output enters the release set.

**Notes:** This phase closes V3-7 and V3-8. The current diagram design passed
visual review and needs verification, not redesign.

## Phase 5: Run current live semantic acceptance

**Status:** Pending

**Outcome:** The current source notebooks run from graph build through grounded
agent and produce the exact evidence promised by the locked learning contract.

**Checklist:**

- [ ] Start from the published graph artifact or another explicitly approved
  clean workshop graph and record its initial identity.
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
  semantic score, relationship types, field provenance, context size, and no
  missing requested fields.
- [ ] Verify the fixed Chicago filter returns two candidates, only Lakeview
  Horizon Suites as the qualifier, and Windward Mile Tower as the explicit
  exclusion.
- [ ] Verify optional Text2Cypher either passes the reader-role and planner gates
  or reports a clear blocked state without executing generated Cypher.
- [ ] Execute Module 3 immediately after Module 2 and verify grounded answering,
  abstention, guest-limit enforcement, and idempotent reservation retries.
- [ ] Record source revision, service and library versions, graph counts, model
  ID, embedding contract, AWS region, Neo4j database, and execution timestamps.
- [ ] Save executed notebooks and logs as local evidence. Publish them only after
  assigning an approved immutable URI and checksum.

**Validation:**

- Modules 1 through 3 pass in order against the same configured environment.
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
- [ ] Record the final disposition of the optional benchmark. State that it was
  deferred unless a valid 240-trial run was actually completed.
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
- All active notebooks and helpers use one tested base-path contract.
- Cairo readiness enforces the locked hotel ID before retrieval begins.
- Every deterministic Module 2 block displays all applicable evidence and
  provenance fields.
- The current Modules 1 through 3 pass in order with fresh live evidence.
- The evaluator gate recomputes judge outcomes and the report cannot publish
  labels that fail that gate.
- Compact Phase 1.5 records and new contract tests are present in a fresh clone,
  while raw evidence remains local-only.
- Active learner scans cover the complete current learner surface.
- Module 4 and Module 5 handoffs use the redesigned module ownership and paths.
- Release records, test totals, graph dump identity, and completion status agree.
- No comparative benchmark claim is published without a valid complete-evidence
  run and durable raw evidence.
