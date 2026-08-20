# align-review: best-practices audit

Written 2026-08-20. Branch `finalize-course`, HEAD `2a6238d`. This is a
static code review, not a live-verification pass — no AWS or Neo4j calls
were made (the AWS SSO token was expired at review time). See `align.md`
and `align-v2.md` for the rewrite's own history; this file is a separate,
independent quality pass over the result: does the workshop showcase Neo4j
and AWS best practice, and is the Python idiomatic and safe.

Seven fresh review agents ran in parallel — one per module (1-6) plus one
for the shared `workshop` package and `setup/` tooling — each reading every
notebook cell, script, README, and paired content page in its scope.

**Zero critical findings.** Nine major, fifteen minor, fourteen nit-level
findings across 38 total, none of which block the workshop from running —
but three are worth fixing before it ships to participants (see "Top
priority" below).

Every finding below now carries a **Proposed fix** — these are proposals
only, not yet applied. Review and mark which ones to act on.

**Update 2026-08-20:** All 38 findings have been implemented. Seven parallel
agents applied the fixes (one per module, plus one for the shared `workshop`
package and `setup/` tooling), each scoped to a disjoint set of files so no
two agents touched the same file. Every finding below now also carries a
**Status** line. The offline test suite (`pytest setup/`, 80 tests) passes
after all changes. No live AWS or Neo4j calls were made during
implementation — these are static edits, unverified against a live run. Two
items deviated from the literal proposed fix and need your attention before
this is considered fully closed — see "Deviations to review" below.

### Deviations to review

1. **Module 3's `tool_choice` fix (major, grounding)** — the proposed
   one-line `tool_choice={"any": {}}` on `Agent(...)`/`BedrockModel(...)`
   construction turned out not to work: `Agent(tool_choice=...)` raises a
   `TypeError`, and `BedrockModel(tool_choice=...)` is silently accepted but
   never read on ordinary conversational turns (Strands only honors it
   internally for `structured_output` calls) — the literal proposed fix
   would have been a no-op that looked like a fix, the exact vacuous-pass
   trap this module warns about. The implementing agent instead added a
   `GroundedBedrockModel(BedrockModel)` subclass that overrides `stream()` to
   force `tool_choice={"any": {}}` only on a fresh, unanswered user question,
   reverting to normal `auto` behavior once a tool result is in context —
   verified against a monkeypatched parent `stream()`. This is a real fix,
   but a bigger change than what was reviewed. Worth a closer look at cell 8
   of `3.2_grounded_booking_agent.ipynb` before this ships.
2. **Module 1's run-id-tagging fix (major, documented risk)** — implemented
   as a recency heuristic (`ingest_started_at` within the last 30s) rather
   than a true per-write lock, since `SimpleKGPipeline`'s internal writes
   aren't otherwise instrumentable without a deeper library change. This
   narrows the race window but doesn't close it. Documented in new
   docstrings/comments in `graph_builder.py` so it isn't mistaken for a
   guarantee.

Everything else was implemented as proposed, with only minor path/API
corrections noted inline below (e.g. `requirements.txt` is actually at
`notebooks/requirements.txt`, not inside the module 6 folder).

---

## Cross-cutting themes

**Region handling is inconsistent between notebooks.** Two independent
reviewers, on unrelated modules, found the same class of bug:
`2.1_vector_rag_hallucinates.ipynb` and `4.2_agentcore_memory.ipynb` both
hardcode `region_name="us-east-1"` instead of calling
`aws_region()`/`configure_aws_region()` like every sibling notebook does. A
participant who sets `AWS_REGION` to anything else gets resources split
across regions with no error — things just quietly stop finding each
other.

**Shared contracts get restated instead of imported.**
`retrieval_contract.py` and `fixtures.py`'s index checks exist specifically
so there's one place to change an embedding model, a dimension count, or an
index definition. Module 2 re-derives the embedding contract as raw
literals instead of importing it, and `retrieval_setup.py` independently
re-implements the same index validation already written in `fixtures.py`.
Both drift silently the next time the contract changes.

**The grounding demo is the one place testing rigor drops.** Module 5's
smoke tests and `verify_setup.py` both pair every refusal with a positive
control on purpose, closing the vacuous-pass gap (see
`grounding-tests-need-positive-controls` in project memory). Module 3.2's
grounded booking agent — the notebook whose entire premise is "abstain
instead of hallucinate" — has no automated assertions at all, print-only,
and nothing forces the model to actually call the retrieval tool before
answering. It's the one demo where a regression would be invisible until a
human reads every printed line.

### Top priority
1. Module 3.2 grounding assertions + `tool_choice` enforcement (below) —
   this is the module the workshop's own "vacuous pass" lesson applies to
   most directly, and it's currently unguarded.
2. The two hardcoded-region notebooks (2.1, 4.2) — silent cross-region
   breakage is a bad failure mode to hand participants.
3. Module 4's Lambda error handling — a stripped Gateway-facing schema lets
   through calls the Lambda code can't handle, surfacing as raw errors
   instead of structured ones.

---

## Module 1 — Build Graph (`notebooks/01-build-graph/`)

- **Major (documented risk), aws/neo4j** — `workshop/bedrock_providers.py:34-56`,
  `graph_builder.py`: `asyncio.wait_for`'s 180s timeout can't cancel a
  Bedrock call already handed to a worker thread. A "timed-out" document
  can still be writing to Neo4j after `retry_failures()` has already
  cleared and re-ingested it, risking a corrupted or duplicated partial
  extraction. Called out candidly in the code's own comments as a known
  trade-off — a real race, not an oversight.
  - *Proposed fix:* don't clear-and-retry immediately on timeout. Tag each
    document's writes with a run id and have `retry_failures()` check (via
    a quick Cypher query) whether that document has had a write in, say,
    the last 30s before clearing it — if so, wait and recheck rather than
    clearing underneath an in-flight write. Longer-term, swap
    `asyncio.to_thread` for a `ProcessPoolExecutor` future that can actually
    be cancelled/terminated on timeout, so "timed out" genuinely means
    "stopped."
  - *Status:* Fixed (heuristic, not a full lock) — writes are now tagged
    with a run id / `ingest_started_at`, and `retry_failures()` skips the
    clear if a recent write exists. The `ProcessPoolExecutor` swap was not
    done (out of scope for this pass); a comment now documents it as the
    longer-term fix. See "Deviations to review" #2 above.
- **Minor, neo4j** — `1.1_build_graph.ipynb` cells 5, 15: driver closed with
  a bare `driver.close()` instead of `with connect() as driver:`. If
  anything in between raises, the driver/pool leaks. `graph_builder.py`'s
  own functions use `try/finally` correctly — this is notebook-only.
  - *Proposed fix:* replace `driver = connect()` / manual
    `driver.close()` with `with connect() as driver:` wrapping the cell's
    body, matching the context-manager pattern `neo4j.Driver` already
    supports.
  - *Status:* Fixed — cells 5 and 15 now use `with connect() as driver:`.
- **Minor, neo4j** — `graph_builder.py:189-191`, `fixtures.py`: writes use
  plain `session.run(...)` instead of `session.execute_write(...)`,
  forgoing the driver's automatic retry on transient errors.
  - *Proposed fix:* wrap each write in `session.execute_write(lambda tx:
    tx.run(query, **params))` (or a small named helper function) instead of
    calling `session.run` directly.
  - *Status:* Fixed in `graph_builder.py`'s `clear_document()`. (The
    `fixtures.py` half of this finding was fixed separately by the shared-
    package pass — see the Shared section below.)
- **Nit, neo4j** — `graph_builder.py` `check_schema_held()` (~321-345):
  dedups extracted hotels by value (`RETURN DISTINCT h.name, h.address, ...`)
  rather than by node identity — fragile if reused elsewhere.
  - *Proposed fix:* dedup on `elementId(h)` instead of the value tuple,
    e.g. `RETURN DISTINCT elementId(h) AS id, h.name, h.address, ...`.
  - *Status:* Fixed.
- **Nit, content-alignment** — `1.1_build_graph.ipynb` cell 15's amenity
  count has no `a.name IS NOT NULL` filter, unlike `fixtures.py`'s
  near-identical `HERO_QUERY`, which does — two copies of the same query
  with a small behavioral difference.
  - *Proposed fix:* add `WHERE a.name IS NOT NULL` to cell 15's amenity
    count, matching `HERO_QUERY`'s filter exactly.
  - *Status:* Fixed.
- **Nit, python** — `1.1_build_graph.ipynb` cell 11 (`RUN_UNPINNED_DEMO`,
  default off): locally imports `session` from `graph_builder`, which would
  rebind the notebook's global `session` name if the flag were ever flipped.
  - *Proposed fix:* alias the import, e.g.
    `from graph_builder import session as build_session`, so it can never
    shadow the notebook's own `session` variable.
  - *Status:* Fixed (imported as `build_session`).

**Holding up well:** all Cypher here is properly parameterized; the
additive, idempotent build (clears only its own 5 held-out documents)
matches the notebook and content page exactly; `graph_builder.py` and
`held_out_documents.py` explain the non-obvious "why" throughout.

---

## Module 2 — Vector RAG Hallucinates (`notebooks/02-vector-rag-hallucinates/`)

- **Major, aws** — `2.1_vector_rag_hallucinates.ipynb` cell 5: a raw
  `boto3.client("bedrock-runtime", region_name="us-east-1")` hardcodes the
  region right after the same notebook calls `configure_aws_region()`. See
  cross-cutting theme above.
  - *Proposed fix:* drop the literal and call
    `region_name=aws_region()` (from `workshop.aws_region`), matching how
    Module 1's `bedrock_providers.py` resolves region.
  - *Status:* Fixed.
- **Major, aws/python** — same cell, `workshop/retrieval_contract.py`: a
  local `_embed()` restates the embedding model ID, dimension count, and
  purpose string as raw literals instead of importing them from
  `retrieval_contract.py`, whose own docstring says these values are
  defined "here and nowhere else." Correct only by copy-paste today.
  - *Proposed fix:* `from workshop.retrieval_contract import
    EMBEDDING_MODEL_ID, EMBEDDING_DIMENSIONS, EMBEDDING_PURPOSE` and use
    those names in `_embed()` instead of the hardcoded literals.
  - *Status:* Fixed.
- **Minor, aws** — same cell: skips the shared `BEDROCK_CONFIG`
  retry/timeout settings every other Bedrock client in the repo uses.
  - *Proposed fix:* construct the client with
    `config=workshop.bedrock_providers.BEDROCK_CONFIG` (or call the
    existing client-factory helper in `bedrock_providers.py` instead of a
    bare `boto3.client(...)`).
  - *Status:* Fixed — client now built with `config=BEDROCK_CONFIG`.
- **Minor, python** — cell 8: `query_knowledge_graph` catches and reports
  errors; the sibling `search_faqs` tool has no error handling at all
  around embedding or index search.
  - *Proposed fix:* wrap `search_faqs`'s body in the same
    `try/except Exception as e: return f"Query error: {e}"` pattern already
    used in `query_knowledge_graph`.
  - *Status:* Fixed.
- **Minor, neo4j/python** — cell 8: opens and closes a new
  `GraphDatabase.driver(...)` on every tool call, even though the agent's
  own system prompt invites multiple queries in a turn.
  - *Proposed fix:* create the driver once at module/cell scope (mirror the
    `lru_cache`-wrapped driver pattern already used in
    `workshop/hybrid_retrieval.py`) and reuse it across tool calls within
    the notebook session.
  - *Status:* Fixed — added an `lru_cache`-wrapped `_get_driver()`.
- **Minor, python** — `build_faiss_if_needed()`: on a missing index,
  extracts the full 300-document corpus to disk, prints a success count,
  then raises `FileNotFoundError` anyway — real I/O and output leading
  nowhere.
  - *Proposed fix:* either remove the extraction branch if it's genuinely
    dead, or — if extraction is meant to recover from a missing index —
    have it proceed to build the FAISS index from the freshly-extracted
    docs instead of raising afterward.
  - *Status:* Fixed — removed the dead extraction branch (the function's
    own error message points at re-cloning, not rebuilding from the zip,
    so extraction was unreachable-useful code either way).
- **Nit** — redundant duplicate imports in cells 3 and 5.
  - *Proposed fix:* remove the repeated `import os` in cell 3 and the
    repeated `sys, os, Path` imports in cell 5; rely on cell 2's imports.
  - *Status:* Fixed.

**Holding up well:** the Phase-5 cell-reorder fix held (Tests 1-4 run
straight through, quoted queries match the content page verbatim); FAISS
vs. Neo4j retrieval paths are kept clearly distinct; the four failure-mode
explanations (aggregation, multi-hop, out-of-domain, null-result signaling)
are accurate, not hand-wavy.

---

## Module 3 — Retrieval Patterns (`notebooks/03-retrieval-patterns/`)

- **Major, grounding** — `3.2_grounded_booking_agent.ipynb` cells 8, 9, 11,
  13, 15: every key claim (abstention, the 15-guest rejection, the accepted
  write, the replay-duplicate check) is print-only. Nothing asserts the
  agent actually abstained, that a rejection carries the right reason code,
  or that a replay is flagged as a duplicate. Contrast with 3.1's real
  `assert any('60611' in ...)` a few cells earlier in the same module.
  - *Proposed fix:* add an `assert` after each demo run, mirroring 3.1's
    pattern — e.g. assert the abstention response contains no fabricated
    availability claim, assert the rejection payload's
    `reason_code == "max_guests_exceeded"`, assert the accepted booking's
    `hotel_id` matches the known fixture id, and assert the replay result's
    `duplicate` flag is `True`.
  - *Status:* Fixed — assertions added to cells 9, 11, 13, checked against
    `reservation_command.py`'s actual field names (`status`, `reason_code`,
    `hotel_id`, `duplicate`, `max_guests`).
- **Major, grounding** — cell 8, `workshop/hybrid_retrieval.py:46-53`:
  grounding is enforced only by system-prompt wording. The `Agent(...)`
  construction never sets `tool_choice`, so nothing forces the model to
  call the retrieval tool before answering — and per the finding above,
  nothing would catch it if the model skipped the call.
  - *Proposed fix:* pass `tool_choice={"any": {}}` (or
    `{"tool": {"name": "search_hotel_knowledge_tool"}}` for the specific
    tool) on the first turn of the `BedrockModel`/`Agent` call so a tool
    call is required before the model can answer in free text.
  - *Status:* Fixed, but not as literally proposed — see "Deviations to
    review" #1 above. `Agent(tool_choice=...)` turned out to raise a
    `TypeError` and `BedrockModel(tool_choice=...)` is silently ignored on
    ordinary turns; a `GroundedBedrockModel` subclass overriding `stream()`
    was written instead to actually force the tool call.
- **Minor, python** — `reservation_command.py:192-207`: `_extract_payload`
  assumes `event` is a mapping and calls `.get()` immediately; a malformed
  event raises an uncaught `AttributeError` that escapes the handler's own
  error-response contract.
  - *Proposed fix:* check `isinstance(event, Mapping)` at the top of
    `_extract_payload` and raise the existing `InvalidCommand` exception
    (rather than let a bare `AttributeError` escape) when it isn't, so
    `handler()`'s existing `except (InvalidCommand, ...)` catches it.
  - *Status:* Fixed.
- **Verified, not a bug** — `index.en.md:45` correctly states there is no
  `guaranteedAvailability` property (the earlier false claim is fixed). No
  fix needed.
  - *Status:* No action taken — not a bug.
- **Nit (deliberate, not a bug)** — `3.1_retrieval_patterns.ipynb` cell 17
  hand-types the schema instead of using `pinned_schema_text()`; cell 18
  frames this as an intentional contrast against the server-side governed
  MCP pattern used later. No fix needed.
  - *Status:* No action taken — not a bug.

**Holding up well:** `reservation_command.py` is fully parameterized, no
eval/exec anywhere despite the name, idempotent via a real uniqueness
constraint with a race-recovery path; the Sonnet-5 / no-`temperature` fix is
correctly in place; 3.1's hybrid retrieval is genuine score fusion (verified
against the library's ranker), backed by a real assertion.

---

## Module 4 — Production Agent (`notebooks/04-production-agent/`)

- **Major, aws** — `4.2_agentcore_memory.ipynb` cell 7: hardcodes
  `REGION = "us-east-1"` instead of calling `aws_region()` as 4.1 does. If a
  participant set a different region, 4.1's Gateway lands there while 4.2's
  `find_gateway_url`/`find_memory_id` lookups silently search us-east-1.
  - *Proposed fix:* replace `REGION = "us-east-1"` with
    `REGION = aws_region()` (or call `configure_aws_region()` as 4.1 cell 4
    does), so both notebooks resolve the same region from the same source.
  - *Status:* Fixed.
- **Major, aws** — `lambda_tools/*/lambda_function.py`, `4.1` cell 22: both
  Lambda handlers call straight into their retrieval functions with no
  try/except, and both raise a bare `ValueError` on an empty query. This is
  reachable because the Gateway-facing schema projection strips
  `minLength`/`additionalProperties` from the model-visible tool schema —
  the contract the model sees no longer forbids what the code still can't
  handle, so a bad call surfaces as a raw Lambda `FunctionError` instead of
  a structured MCP error.
  - *Proposed fix:* two-part. (1) In each `lambda_function.py`, wrap the
    call to `graph_query`/`search_hotel_knowledge` in `try/except
    ValueError as e: return {"error": str(e)}` (or the MCP-appropriate error
    shape) instead of letting it raise. (2) Either stop stripping
    `minLength`/`additionalProperties` in the `gateway_input_schema`
    projection (4.1 cell 22) so the model-visible contract matches what the
    code enforces, or — if the Gateway genuinely can't carry those
    keywords — validate the query argument explicitly inside the handler
    before calling into retrieval.
  - *Status:* Fixed (part 1) — both Lambda handlers now wrap the retrieval
    call in `try/except ValueError` and return a structured `{"error": ...}`
    payload instead of raising.
  - *Proposed fix:* validate `event.get("query")` is present and is a
    non-empty string at the top of the handler, returning a clean
    structured error payload (not a raised exception) if not.
  - *Status:* Fixed (part 2) — added the `isinstance`/non-empty-string
    guard at the top of both handlers. Cell 22's Gateway schema projection
    was deliberately left unchanged, as scoped.
- **Nit, aws** — `4.1_agentcore_gateway.ipynb` cell 13: the Bedrock IAM
  statement wildcards the region on the foundation-model ARN. Low risk
  (model ARNs carry no account ID, action list is tightly scoped) but worth
  a second look if this repo is ever hardened further.
  - *Proposed fix:* scope the resource to the specific model family
    actually invoked, e.g. `arn:aws:bedrock:*::foundation-model/anthropic.claude-*`,
    instead of `foundation-model/*`.
  - *Status:* Fixed.

**Holding up well:** the Neo4j driver and retrievers are cached at module
scope (`lru_cache`), correctly surviving warm Lambda starts; the "tools
can't write" guarantee is genuinely tested (a stub LLM is made to emit a
real `SET` and the test asserts rejection); IAM elsewhere is tightly scoped;
the wheel-packaging change was independently re-verified by actually
building it.

---

## Module 5 — AgentCore Deploy (`notebooks/05-agentcore-deploy/`)

- **Major, aws** — `5.1_deploy.ipynb` cell 07 (`BedrockModelInvocation`
  policy): the IAM resource list includes
  `arn:aws:bedrock:{REGION}:{account_id}:*` — a wildcard over every
  resource type in the account/region, not just the cross-region inference
  profile the comment justifies. Should scope to `inference-profile/*`.
  - *Proposed fix:* change the resource entry to
    `arn:aws:bedrock:{REGION}:{account_id}:inference-profile/*`, matching
    the comment's stated intent.
  - *Status:* Fixed.
- **Minor, docker** — `runtime_app/.dockerignore`: only `.env` is excluded —
  no pattern for `*.pem`, `credentials`, or `.aws/`. Low risk today, but an
  incomplete secret-exclusion list.
  - *Proposed fix:* add `*.pem`, `*.key`, `credentials`, and `.aws/` to
    `.dockerignore` alongside the existing `.env` entry.
  - *Status:* Fixed.
- **Minor, content-alignment** — `index.en.md:56-57`: describes the build
  context staging but doesn't mention the wheel build or the
  `BUILD_INFO.txt` provenance file the notebook actually produces.
  - *Proposed fix:* add a sentence to `index.en.md` noting that staging now
    builds `workshop` as a wheel (`uv build --wheel`) and writes
    `BUILD_INFO.txt` with the commit/dirty-state into the build context,
    so the page matches `runtime_app/`'s actual contents.
  - *Status:* Fixed.
- **Nit, docker** — no `HEALTHCHECK` in the Dockerfile (not required — Runtime
  manages the lifecycle — but a generic gap).
  - *Proposed fix:* leave as-is; optionally add a one-line comment in the
    Dockerfile noting AgentCore Runtime manages container liveness, so a
    future reader doesn't wonder if it was forgotten.
  - *Status:* Fixed — comment added near `EXPOSE 8080`.
- **Nit, consistency** — no `README.md` in this module's notebook directory,
  unlike sibling modules 01/03/04/06.
  - *Proposed fix:* add a `README.md` following the structure already used
    by modules 01/03/04/06 (short overview, what you'll build, prerequisites,
    cleanup pointer).
  - *Status:* Fixed — `README.md` created, content drawn from the actual
    notebook and content page (no invented steps).

**Holding up well:** Dockerfile layer order is exactly right (deps before
app code, wheel installed `--no-deps` before the `USER` switch, app files
copied with `--chown` after); the `AWS_REGION`/`AWS_DEFAULT_REGION` quirk is
correctly handled; top-level error handling deliberately logs only the
exception type, never the message, to keep Neo4j credentials out of
CloudWatch; the `workshop.fixtures` import claim was independently
re-verified, not just trusted.

---

## Module 6 — Neo4j Memory (`notebooks/06-neo4j-memory/`)

- **Minor, neo4j** — `memory_helpers.py:243-267`, `cleanup_memory.py:84-124`:
  queries run via auto-commit `session.run(...)` rather than managed
  `execute_read`/`execute_write`, losing automatic retry-on-transient-error
  and diverging from the vendored library's own client pattern.
  - *Proposed fix:* wrap each query in `session.execute_read(lambda tx:
    tx.run(...).data())` or `session.execute_write(...)` as appropriate, in
    both `_run_query` and `run_cleanup`.
  - *Status:* Fixed — writes and reads classified per-query and dispatched
    to `execute_write`/`execute_read` accordingly.
- **Minor, python** — `requirements.txt:4` vs `memory_helpers.py:180-182`:
  `requirements.txt` pins `neo4j-agent-memory[bedrock]>=0.5.0` (open floor),
  but the code's own comment claims the package "is pinned" to justify
  matching an exact warning string tied to several 0.5.0-specific quirks.
  Not live yet since 0.5.0 is still latest, but the comment is currently
  inaccurate.
  - *Proposed fix:* change the pin to
    `neo4j-agent-memory[bedrock]==0.5.0` in `requirements.txt`, matching the
    notebook's own commented-out `pip install "neo4j-agent-memory[bedrock]==0.5.0"`
    line and making the code comment's claim true.
  - *Status:* Fixed. Note: this file actually lives at `notebooks/requirements.txt`,
    not inside the module 6 folder — the correct file was patched.
- **Minor, python** — `memory_helpers.py:82-85`: `MEMORY_VECTOR_INDEXES` is
  defined with a comment claiming a smoke test verifies it — nothing in the
  repo imports or uses it. Dead code, stale comment.
  - *Proposed fix:* delete the constant and its comment, or — if the intent
    was real — wire it into an actual assertion in the notebook's smoke
    test cell.
  - *Status:* Fixed — confirmed genuinely unused repo-wide, then deleted.
- **Nit, neo4j** — replaying message-write cells (6, 8, 10) without
  re-running the `RUN_ID` cell first appends duplicate `Message` nodes — no
  dedup key on messages. Not called out anywhere as "run top to bottom
  once."
  - *Proposed fix:* add a one-line markdown note above the first message-write
    cell: "Run this notebook top to bottom once per session — re-running
    these cells without re-running the `RUN_ID` cell creates duplicate
    message records."
  - *Status:* Fixed — markdown note added above the first message-write
    cell.
- **Nit, python** — `cleanup_memory.py:93-105`: the printed deletion count
  sums only `nodes_deleted`; relationship-only deletes are silently
  excluded from the summary (the deletes themselves are correct).
  - *Proposed fix:* also sum `counters.relationships_deleted` across the
    four queries and report both counts, e.g. "Deleted N node(s) and M
    relationship(s)."
  - *Status:* Fixed.

**Holding up well:** every claim in the code's comments about the vendored
library's 0.5.0 internals was checked against the actual PyPI source and
held up; recall correctly uses a parameterized, actor-anchored graph
traversal instead of the library's store-wide vector search; `cleanup_memory.py`
is tightly scoped by owner tag and prefix and asserts the Hotel count is
unchanged before/after; the previously-flagged missing-`CYPHER 25` content
regression is confirmed fixed.

---

## Shared `workshop` package & `setup/` tooling

- **Major, python** — `retrieval_setup.py:171-229` vs `fixtures.py:193-222`:
  two independent implementations of the same two index-contract checks
  (vector index dimensions/similarity, fulltext index), with slightly
  different code shapes. A future index-contract change has two call sites
  to update, with nothing forcing them to move together.
  - *Proposed fix:* pick one implementation (likely `fixtures.py`'s
    `_index_problems`, since it's the more established of the two) and have
    `retrieval_setup.py` import and call it directly instead of
    reimplementing it — or extract both into a single shared function in
    `retrieval_contract.py` that both modules import.
  - *Status:* Fixed — `retrieval_setup.py` now imports and calls
    `fixtures.py`'s `_index_problems` directly; the duplicate
    implementation was deleted. (A further move into `retrieval_contract.py`
    would be cleaner but was left as a future step, not required now.)
- **Minor, python** — `graph_connection.py:31`: `NEO4J_USERNAME` is a
  module-level constant computed once at import time, contradicting the
  file's own stated design that values are read at call time. Never
  referenced anywhere — every real caller uses `neo4j_auth()` instead. Dead
  code that doubles as a trap for a future caller.
  - *Proposed fix:* delete the module-level `NEO4J_USERNAME` constant;
    keep only the call-time `neo4j_auth()` function as the single way to
    read it.
  - *Status:* Fixed.
- **Minor, neo4j/python** — `hybrid_retrieval.py:96-108`: `Neo4jConfig` is a
  frozen dataclass carrying `password: str` with the default `__repr__`.
  Any uncaught exception or debug print touching this object — it also
  doubles as an `lru_cache` key — renders the plaintext Neo4j password. Add
  `field(repr=False)`.
  - *Proposed fix:* change the field to
    `password: str = field(repr=False)` (and consider the same for
    `username`) so default `repr()`/logging never prints the credential.
  - *Status:* Fixed — applied to both `password` and `username`.
- **Nit, packaging** — `pyproject.toml:9-15`, `bedrock_providers.py:20`:
  `botocore` is imported directly but relies on being pulled in
  transitively by `boto3` rather than being declared.
  - *Proposed fix:* add `botocore` explicitly to `pyproject.toml`'s
    `dependencies` list alongside `boto3`.
  - *Status:* Fixed.
- **Nit, neo4j** — `hybrid_retrieval.py:145-152`: the `lru_cache`d driver is
  never closed in this module. Fine for a warm, recycled Lambda container;
  a notebook calling the same tools repeatedly leaks a driver/socket per
  kernel session.
  - *Proposed fix:* no change needed for the Lambda path; for notebook
    usage, add a note in the module docstring (or an explicit teardown
    cell) that a long notebook session can call `_get_driver.cache_clear()`
    after closing the cached driver if it needs to release the connection.
  - *Status:* Fixed — docstring note added; no code change needed for the
    Lambda path, as scoped.
- **Nit, tooling** — `setup/check_repo.py:184-221`: `RETIRED_NAMES`/
  `BANNED_PATTERNS` are manually maintained with no test keeping them in
  sync as folders get renamed, unlike the module-registration check in
  `test_run_notebooks.py`.
  - *Proposed fix:* add a test analogous to
    `test_every_module_with_a_notebook_folder_is_registered` that cross-checks
    `RETIRED_NAMES`/`BANNED_PATTERNS` against the actual current module
    folder names, failing if either list looks stale.
  - *Status:* Fixed — two tests added to `test_check_repo.py`;
    `check_repo.py` itself intentionally left unchanged.
- **Nit, python** — `workshop_utils.py` mixes four concerns (log
  suppression, progress display, a Strands trace hook, result printing);
  each is genuinely shared across Module 4's notebooks, but the file's
  docstring only describes half of what's in it.
  - *Proposed fix:* lowest-effort — expand the module docstring to
    enumerate all four responsibilities. If it grows further, split into
    `workshop_utils/logging.py`, `progress.py`, `tracing.py`, `printing.py`.
  - *Status:* Fixed — docstring expanded to cover all four
    responsibilities. File was not split, as scoped.

**Holding up well:** the Aura constraint-type bug
(`NODE_PROPERTY_UNIQUENESS` vs `UNIQUENESS`) is fixed in both `fixtures.py`
and its equivalent, and exercised by tests; the dual `AWS_REGION`/
`AWS_DEFAULT_REGION` write is correct and consistently called from every
module's setup cell that needs it; the 78-test offline suite asserts both
directions (healthy passes silently, broken produces a specific message)
rather than being tautological; no bare `except:`, no mutable default
arguments, and no hardcoded embedding literals outside `retrieval_contract.py`
anywhere in the shared package.

---

## Methodology

Seven fresh, context-free review agents ran in parallel: one per module
(1-6), one for the shared `workshop` package and `setup/` tooling. Each read
every notebook cell, script, README, and paired content page in its scope,
cross-checked design claims against `align.md`/`align-v2.md`'s documented
"known-intentional" decisions (CYPHER 25 prefixes, no `temperature` for
`claude-sonnet-5`, wheel-based packaging, the botocore region quirk, the
positive-control testing pattern) to avoid false positives, and reported
findings with severity, category, and file:line citations. No live AWS or
Neo4j calls were made. Findings above are consolidated and cross-checked
against each other for overlap; none are duplicated across sections.
Proposed fixes were added afterward by a single pass over the collected
findings.

**Implementation pass (2026-08-20):** a second set of seven parallel agents
then applied the fixes, one per module plus one for the shared package,
partitioned by file ownership so no two agents edited the same file
concurrently (the one case where two findings touched the same file —
`fixtures.py`, referenced by both a Module 1 finding and a Shared-section
finding — was resolved by giving the whole file to the Shared-package
agent). Each agent verified its own changes statically (`py_compile`/JSON
validity, and for the shared package, the full offline test suite) before
reporting back; no agent executed a notebook against live AWS or Neo4j.
Status lines and the "Deviations to review" section above were written by
reviewing each agent's own completion report, not by re-deriving the diffs
independently — treat the two flagged deviations as needing a human look
specifically because they diverge from what an agent was asked to do.
