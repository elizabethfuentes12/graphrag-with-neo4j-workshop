# Workshop Defects and Proposed Fixes

Date: 2026-08-21
Branch: finalize-course

What was checked:

- `notebooks/01-build-graph/1.1_build_graph.ipynb` and `workshop-content/content/01-build-graph/index.en.md`
- `notebooks/02-vector-rag-hallucinates/` and `workshop-content/content/02-vector-rag-hallucinates/index.en.md`
- Every Cypher query in both modules, run live against the Aura instance in `.env`
- Every factual claim in the prose, checked against the code that backs it

Live environment at the time of the check:

- Neo4j 5.27-aura, enterprise, Cypher 5 and 25 both available
- 300 `Document`, 300 `Chunk`, 292 `Hotel`
- Both retrieval indexes online
- The instance is not a clean restore. Module 1 and Module 6 have already run on it.

A note on every reference below: the line numbers in this file have drifted as the
working tree changed. Patch by symbol, not by line number, and confirm the symbol
still exists before editing it.

---

## Module 1: fixed

All of these were wrong in the prose. All are now corrected in the working tree.

- **"No other file in this workshop names those five cities" was false.** The `-001` document for each of those cities is in the dump. The source docstring says no *authored* file names them, and the word "authored" was dropped in the rewrite. Now says no later module asks a question about these five `-002` hotels.
- **"This module has no cleanup step or run identifier" was wrong about the run identifier.** `graph_builder.py:255` puts a `run_id` on every document. Now says nothing in this module deletes the five hotels.
- **"The cell removes this temporary data when it finishes" was false.** See the outstanding item below. The prose now says the demo leaves its data behind and that nothing downstream reads it.
- **"Bedrock's 4096-token default" named the wrong owner.** 4096 is the default in the workshop's own wrapper at `bedrock_providers.py:178`. Now says the workshop's Bedrock client sets it.
- **Cell 23 sent the reader to Module 3 for the output comparison.** Module 2 is the module that compares. Fixed.
- **Cell 23 said "Module 2 demonstrates and fixes this failure."** Module 2 only demonstrates it. Module 3 fixes it. Fixed.
- **"The workshop's embedder accepts no override" dropped a word.** The code comment says no *environment* override. `BedrockEmbeddings.__init__` does accept `model_id` and `dimensions` as arguments. Now says no environment override, with the model and width set in code.
- **"Every property in the schema appears in that text as plain prose under a heading" was too strong.** `Service.is_available` and `Service.is_complimentary` are booleans that appear nowhere as prose. The 400-character preview only reaches the six `Hotel` properties. Now lists what actually appears where.
- **"Your own five hotels get the same treatment after the build" promised five.** The cell walks one. Fixed.
- **"The build asserts one chunk per document" described the wrong check.** The build compares the total chunk count against the total document count. One document with two chunks and another with none would pass. Fixed in both files.
- **"Clearing each document again before it retries" was unconditional.** `retry_failures` skips the clear when a write for that document started in the last 30 seconds. Fixed.
- **The Cairo fixture check also requires a rating.** Both files said spa and pool only. The live margin on that gate is exactly one hotel, so the full condition matters. Fixed in both files.
- **"Against the vectors your own extraction just wrote" was too narrow.** The indexes cover every `Chunk` in the graph, which is 300 of them. The participant wrote 5. Fixed.
- **Style leftovers.** Removed the throat-clearing openers in cell 0, cell 23, and the content page intro. Changed "SimpleKGPipeline extracts without a schema" to "can extract". Added the missing gloss for `SimpleKGPipeline` in the notebook. Removed the definite article in front of "the two retrieval indexes" 13 cells before they are introduced. Replaced the bare "Module 2 directory" reference with the actual directory name and what it holds. Split three sentences that carried two claims each.

Checks that pass after the fixes:

- nbformat validates
- All nine original code cells are byte-identical to the git index
- `nbformat_minor` is still 4 and no cell IDs were added
- Zero em-dashes and zero litotes in both files
- The three new code cells compile, longest line 81 characters

Live Cypher results for the three new cells:

- The `count { (h)-[:HAS_ROOM]->() }` subquery form works, including under an explicit `CYPHER 25` prefix
- `FROM_DOCUMENT` and `FROM_CHUNK` point the direction the new query assumes
- `hotel-paris-001.txt` returns exactly one row, 1 chunk, embedding width 1024, 3 rooms, 6 amenities, 11 policies, 8 services
- `SHOW INDEXES` returns both indexes online at 1024 dimensions and cosine similarity
- A sweep of all 300 filenames found no case where the query returns more than one row

---

## Module 1: outstanding

### M1-1. The optional unpinned demo leaves data in the graph forever

- **Where:** `1.1_build_graph.ipynb` cell 15.
- **What is wrong:** The cell calls `run_async(file_path=..., text=...)` with no `document_metadata`. `source_filename` only ever arrives through `document_metadata`. The `finally` block calls `clear_document`, which matches on `MATCH (d:Document {source_filename: $filename})`, so it matches nothing and deletes nothing.
- **Why it matters:** The demo's `Document`, its `Chunk`, and every off-schema label it invented stay in the graph permanently. Nothing catches it. The schema check only looks at the build run's own chunks, and the count checks still balance because the orphan adds one to each side.
- **The obvious one-line fix is unsafe.** Adding `document_metadata={"source_filename": sample.name}` does make the `finally` block match, but `sample = paths[0]` is one of the participant's five real held-out documents. On a first pass through the notebook that is harmless, because the demo runs before the build. A participant who sets `RUN_UNPINNED_DEMO = True` and re-executes cell 15 after the build has finished deletes the correctly built `Document`, `Chunk`, and entities for that hotel, and the next readiness check then fails with no visible cause.
- **Proposed fix:** Give the demo a filename that cannot collide with a real document.
  ```python
  demo_filename = f"unpinned-demo-{sample.name}"
  ```
  Pass it as `file_path` and as `document_metadata={"source_filename": demo_filename}`, and clear that name in the `finally` block. Cleanup becomes exact, re-running after the build is harmless, and the demo's document is unambiguously the demo's. Then change the cell 14 prose back to promising cleanup.
- **Why it is not done yet:** This changes an existing code cell, which was explicitly out of scope for the writing pass. It needs a decision.
- **Recommendation:** Make the fix with the distinct filename. The alternative is shipping a workshop that tells participants it leaves junk in their graph, or one that can silently delete a hotel it just built.

---

## Module 2: defects

Note: `2.1_vector_rag_hallucinates.ipynb` and its `README.md` already have uncommitted edits from an earlier style pass. This audit covers that current state.

### Blockers

#### M2-1. The vector agent does not work at all, and the committed index has no compatibility contract

- **Status, 2026-08-21:** The base artifact is rebuilt. `faqs_vector.index` is now an `IndexFlatIP` at `d` 1024 with `ntotal` 300 and L2-normalized vectors, `faqs_vector.manifest.json` and `rebuild_faiss_index.py` exist, the loader rejects a non-inner-product index, and 13 artifact tests pass. The artifact agent is completing `vectors_sha256` and the fixed graph `vector_source`; committing the new artifacts and every notebook-side item below remain open.
- **Where:** `2.1_vector_rag_hallucinates.ipynb` cells 5 and 8.
- **What was wrong:** The committed `faqs_vector.index` was 384-dimensional. `_embed()` asks for 1024 dimensions, which is `EMBEDDING_DIMENSIONS` in `workshop.retrieval_contract`. FAISS raised a bare `AssertionError`. The `except` block in `search_faqs` swallows it and returns the string `"Query error:"`, which is still true and still has to be fixed.
- **Why it matters:** All four demonstrations in the module are empty. The vector agent never receives a single document. It answers by declining politely, which is the opposite of the point the module is making.
- **Evidence:** The committed run at `setup/notebook-output/20260821T011118Z-18505/02-vector-rag-hallucinates/2.1_vector_rag_hallucinates-executed.ipynb` shows `Query error:` on every tool call in all four tests. Test 1's answer reads "I'm sorry... Booking Platforms: Websites like Booking.com...".
- **Every participant hits this.** The 384-dimensional file is tracked in git, and `build_faiss_if_needed()` only checks whether the file exists. It never builds one.
- **Fix:** Keep FAISS as Module 2's standalone vector-RAG baseline and rebuild `faqs_vector.index` at 1024 dimensions using the shared Nova embedding contract: `EMBEDDING_MODEL_ID`, `EMBEDDING_DIMENSIONS`, and `EMBEDDING_PURPOSE` from `workshop.retrieval_contract`.
- **Source the vectors only from the graph, not from 300 new Bedrock calls.** The vectors already exist. Every one of the 300 `faqs_docs.json` texts is byte-identical to its `data/*.txt` file and the longest is 7,442 characters. `graph_config.CHUNK_SIZE` is 12,000 with zero overlap, so each document becomes exactly one `Chunk` whose text is the whole document. Module 1 embeds those chunks through `BedrockEmbeddings`, which is pinned to the same model, the same purpose, and the same 1024 width that the notebook's `_embed` sends. The rebuild script should read the 300 chunk vectors out of Neo4j and write them to FAISS in `faqs_docs.json` order. A missing, duplicate, null, or wrong-width Aura row is an export failure, not a reason to silently switch embedding sources.
- **Why that beats re-embedding:** it removes the cost, quota exposure, and throttling risk from the rebuild, and it prevents the standalone FAISS baseline from drifting onto a second embedding space. The Module 2 graph arm still uses structured Cypher rather than vectors. The benefit is that FAISS and the Neo4j vector retrieval introduced in Module 3 start from the same stored embeddings while the two modules retain different teaching goals.
- **Commit a compatibility manifest:** Add `faqs_vector.manifest.json` beside the index with these values:
  - `embedding_model_id`
  - `embedding_dimensions`
  - `embedding_purpose`
  - `document_count`
  - `corpus_sha256`, the SHA-256 checksum of the exact committed `faqs_docs.json` bytes
  - `faiss_metric`, the metric the index was built with
  - `vectors_sha256`, a digest over the raw vector bytes read back out of the index
  - `vector_source`, fixed to the graph's `Chunk.embedding` export path
  - `vector_normalization`, the normalization applied before indexing and querying
- **Decide the metric explicitly.** The original index was an `IndexFlatL2`, file magic `IxF2`, `d` 384, `ntotal` 300, while Neo4j's chunk index is cosine, and nothing recorded that difference. If the Nova vectors are not unit-norm then an L2 baseline ranks differently from Module 3's Neo4j retrieval for a reason that has nothing to do with the lesson. **Settled:** the rebuild L2-normalizes every vector and stores them in an `IndexFlatIP`, so the baseline ranks by cosine like the graph side. The manifest records `faiss_metric` and `vector_normalization`, and the loader rejects any index that is not inner product.
- **Validate before use:** Loading the baseline must fail with a descriptive error unless all of these hold:
  - the manifest's embedding values equal the shared contract constants
  - `index.d == manifest.embedding_dimensions == EMBEDDING_DIMENSIONS`
  - `index.ntotal == manifest.document_count == len(documents)`
  - the computed corpus checksum equals `manifest.corpus_sha256`
  - the metric recorded in the manifest matches the metric of the loaded index
  - `manifest.vector_source` names the graph `Chunk.embedding` export and `manifest.vector_normalization` matches the query-normalization path
  - the digest of the vectors read back out of the index equals `manifest.vectors_sha256`
- **Shape checks alone are not enough.** Every check in the first four bullets above tests shape. An index whose bytes are corrupted but whose `d` and `ntotal` are still right passes all of them. That is what `vectors_sha256` is for.
- **Make the artifact reproducible:** Commit the facilitator-side rebuild script that walks `faqs_docs.json` in its stored order, pulls each document's vector from the graph, writes the index, and writes the manifest. Participants load the pre-built artifacts; they should not spend the workshop making 300 embedding calls.
- **Do not swallow retrieval failures:** Remove the broad `except Exception` in `search_faqs`, or re-raise with context. Returning `"Query error:"` as an ordinary tool result is what allowed an end-to-end notebook run to look successful while every retrieval had failed.
- **Show the evidence:** Before each vector-agent answer, display the raw retrieved-document set, including filenames, FAISS distances or scores, and the complete document text actually passed to the model. Use a scrollable or collapsible display if needed. The model's response is an observation; the retrieved evidence is the deterministic part of the demonstration.
- **Recommendation:** This is the only recommended architecture. Module 2 should remain the comparison between standalone FAISS document retrieval and structured Cypher over Neo4j. Module 3 owns Neo4j vector, hybrid, and graph-enriched retrieval patterns; moving Module 2 onto Neo4j's vector index would blur that boundary.

#### M2-2. Even with M2-1 fixed, two of the four tests still fail for a hidden reason

- **Where:** `search_faqs` in cell 8, `doc['text'][:500]`.
- **What is wrong:** Each document is cut to 500 characters before the model sees it. In every source document the word "Spa" first appears around offset 2,000 and "Pool" around 2,800. Both are past the cut.
- **Why it matters:** The counting test and the multi-criteria test would fail because of truncation, not because of how vector search works. The prose never mentions truncation, so the participant draws the wrong conclusion. The first 500 characters do contain `Guest Rating` and `Total Rooms`, so the averaging test would work.
- **Fix:** Remove the slice and pass the complete retrieved document to the model. Do not replace 500 with another unexplained constant.
- **Recommendation:** The lesson is about which documents top-k retrieval selects, so do not let a second, hidden truncation step cause the failure.

#### M2-2a. Test 1 can retrieve the complete Paris set even though the prose says it cannot

- **Where:** notebook cell 9 and `index.en.md:42`.
- **What is wrong:** The graph contains two Paris hotels and the FAISS baseline asks for three documents. A `k=3` search can retrieve both Paris documents, whose text contains both ratings, and the model can then compute the correct 4.7 average. The claim that three retrieved documents cannot cover every Paris hotel is not guaranteed and may be false in the repaired run.
- **Why it matters:** Fixing the index can turn the first headline failure into a success. That would teach that vector retrieval cannot aggregate when the actual example just gave it the complete qualifying set.
- **Fix:** Change Test 1 to a city with more matching hotels than `k`. Use Orlando: the live graph contains five Orlando hotels and their average rating is 4.62. With `k=3`, the vector arm is provably missing at least two qualifying documents even if its ranking is perfect.
- **Confirmed at source:** there are five Orlando documents, rated 4.7, 4.5, 4.6, 4.7, and 4.6, so the mean is exactly 4.62.
- **Keep both build paths deterministic:** Add all five Orlando source documents to the lite-build selection, and have the readiness cell report the rated Orlando hotels it found rather than hard-failing, on the same report-do-not-gate principle as M2-7. Update the notebook, page, README, expected result, and both diagrams together.

#### M2-2b. Test 2 has a knowable ground truth and states none

- **Where:** notebook cells 12, 13, and 14, and the counting row of cell 0's table.
- **What is wrong:** The query is "How many hotels in the database have a swimming pool?" and no surface anywhere states the right answer, so a participant reading the output cannot tell a correct count from a wrong one.
- **The answer is derivable.** 175 of the 300 source documents name a pool in their amenity bullet list. The other 125 carry an explicit "Pool facilities are not available at this property" section. The two add to exactly 300.
- **Those 125 negations are a hazard for the count.** If the extraction turned any of them into a `Pool` amenity, the graph's count is inflated, and the test reports a confident wrong number with nothing to check it against.
- **Fix:** Print the source-derived count of 175 beside the graph's count. Marking a test optional in the learner path does not excuse it from having a right answer.

#### M2-3. Neither agent pins a model

- **Where:** cell 8. Both `Agent(...)` calls omit `model=`.
- **What is wrong:** Strands falls back to its own default, `global.anthropic.claude-sonnet-4-6`. The workshop pins `us.anthropic.claude-sonnet-5` in `bedrock_providers.py:66`.
- **Why it matters, three ways:**
  - Module 1's cell 23 teaches "use a fixed model" one notebook earlier, and shows `BedrockModel(model_id="us.anthropic.claude-sonnet-5")`. Module 2 is the only notebook in the workshop that ignores that advice, and it is the only notebook whose whole purpose is comparing two outputs.
  - The `global.` inference profile needs its own Bedrock grant. Module 2 can fail with `AccessDeniedException` in an account where everything else works.
  - `setup/verify_setup.py:282` checks `default_model_id()`, which is not the model Module 2 uses. Setup can pass and Module 2 still fail.
- **Proposed fix:** Pass `model=BedrockModel(model_id=default_model_id())` to both agents.
- **Recommendation:** Do it. It is a two-line change and it closes a real access risk.

#### M2-4. The participant's AWS region is ignored

- **Where:** cell 3 calls `configure_aws_region()`. Cell 5 calls `load_dotenv(find_dotenv())`.
- **What is wrong:** The order is backwards. At cell 3 the `AWS_REGION` from `.env` is not loaded yet, so region resolution falls through to the profile or to `us-east-1`, and writes that into the environment. `load_dotenv` defaults to `override=False`, so cell 5 cannot correct it.
- **Why it matters:** A participant in any other region silently runs the entire module against `us-east-1`. `.env.example` ships `AWS_REGION`, and `aws_region.py:32` says that variable is the one a participant edits.
- **Proposed fix:** Move `load_dotenv(find_dotenv())` above `configure_aws_region()`, matching Module 1's cell 3.
- **Recommendation:** Do it. Module 1 already has the correct order, so this is bringing Module 2 in line.

#### M2-5. Sessions do not name the database

- **Where:** cells 5 and 8. `GraphDatabase.driver(...)` then `.session()` with no `database=`.
- **What is wrong:** Module 2 hand-rolls its connection instead of using `workshop.graph_connection`, which exists to stop this. Module 1 passes `database=graph_database()` in six places.
- **Why it matters:** With `NEO4J_DATABASE` set, Module 2 reads a different database than the one Module 1 wrote to. Every test returns "No results found." and nothing raises an error.
- **Proposed fix:** Use `require_neo4j_env()`, `neo4j_auth()`, and `session(database=graph_database())` from the shared helper.
- **Recommendation:** Do it in the same pass as M2-6.

#### M2-6. Module 2 reads a credential variable the shared helper rejects

- **Where:** cell 5. `os.getenv('NEO4J_USERNAME', os.getenv('NEO4J_USER', 'neo4j'))`.
- **What is wrong:** `graph_connection.py:5` states that the older `NEO4J_USER` spelling is deliberately not read. Cell 5 reads it anyway, and reimplements the missing-variable check that `require_neo4j_env()` already does.
- **Why it matters:** Two places now define what a valid environment looks like, and they disagree.
- **Proposed fix:** Delete the hand-rolled block and call the shared helper.

### Wrong facts in the content

#### M2-7. Test 3 proves nothing, because nothing gets filtered out

- **Where:** `index.en.md:61` and `:63`, notebook cell 15.
- **What is wrong:** There is exactly one hotel whose address contains "Cairo", and it already has both a spa and a pool. So "Cairo hotels with a spa and a pool" returns the same single row as "Cairo hotels". The AND condition excludes nothing.
- **Live result:** 1 row, AnyCompany Cairo Nile View, rating 4.5.
- **Also wrong:** The prose is plural in both places. And the `select_lite_files` docstring in `graph_config.py` claims the opposite, saying the Cairo query has more than one hotel to work with.
- **Why it matters:** The test is supposed to show that a graph applies every condition while similarity ranking does not. As written the claim cannot be observed either way.
- **Fix:** Use Chicago with the existing spa-and-pool criteria. The live graph has two Chicago hotels: Lakeview Horizon Suites has both amenities, while Windward Mile Tower has neither. The AND predicate therefore returns one hotel and visibly excludes the other.
- **Confirmed at source:** `hotel-chicago-001.txt` is Windward Mile Tower, rated 4.5, and its amenity bullet list names no pool and no spa. `hotel-chicago-002.txt` is Lakeview Horizon Suites, rated 4.4, with an Outdoor Swimming Pool and a Full-Service Spa.
- **The lite build can undo this.** Windward Mile Tower's Pool section reads "Pool facilities are not available at this property." `Amenity` carries only `name` and `description` and has no availability flag, so nothing stops the extraction from minting a `Pool` amenity out of that negation. On the full build it does not matter, because Chicago comes from the frozen dump. On the lite build both documents are re-extracted live, and if the negation is extracted as an amenity then Test 3 returns two rows and excludes nothing, which is this same defect again.
- **Report, do not gate.** A hard readiness fixture turns a stochastic extraction into a stochastic notebook failure. Have the readiness cell query the graph for a city with at least two candidates, at least one match, and at least one exclusion, prefer Chicago, and print the city and the counts it actually found. The prose documents Chicago and says the cell prints the live numbers.
- **Also fix:** the false claim that Cairo has more than one hotel to work with. It is in the `select_lite_files` docstring in `graph_config.py`, not at line 50, and `REQUIRED_CITIES` is still `("paris", "cairo")`.

#### M2-8. Both module images contain wrong facts

- **Where:** `workshop-content/images/01-rag-vs-graphrag-problem.png` and `01-rag-vs-graphrag-architecture.png`.
- **The problem diagram:**
  - Shows the Paris average as 4.21. The live answer is 4.7. The average across all hotels is 4.6. 4.21 matches nothing.
  - Says "computed across all 300 hotels". There are 292 hotels, and the Paris query touches 2 of them.
  - Draws a `City` node type. Module 1's page now lists `City` and `Country` as the exact schema drift the pinned schema exists to prevent. The live graph has zero of them.
  - Shows a "fabricated average 3.6" that appears in no run.
  - Has a stray bracket in `AVG()]`.
- **The architecture diagram:**
  - Runs `MATCH (h:Hotel) RETURN AVG(h.rating)`. The property is `guest_rating`. `h.rating` exists on zero of 292 hotels, so the query returns null. The notebook's own tool docstring warns about exactly this mistake.
  - Arrows flow downward into a "Same user query" box at the bottom, which reverses cause and effect.
  - One box renders as two empty shapes.
  - Says "300 Hotel FAQ Documents" over the graph side, where the hotel count is 292.
- **This is authoring, not editing.** These two are the only images in the repository with no `.drawio` source, and `workshop-content/images/DIAGRAM_PROMPTS.md` sits beside them, which is the likely reason they carry 4.21, a `City` node, `h.rating`, a stray bracket, and a doubled box. There is nothing to correct, so both have to be built from scratch.
- **Both images live in two trees.** `workshop-content/images/` and `static/images/` hold byte-identical copies. A fix that lands in one leaves a stale copy in the other.
- **Proposed fix:** Author both as new `.drawio` sources, the way every other diagram in the workshop is authored, and export the PNGs into both trees. Draw them around the repaired Orlando test. Use 4.62 across five matching Orlando hotels, `guest_rating`, no `City` node, and arrows that start at the user query. Keep the vector side explicitly labeled as the standalone FAISS baseline so the diagram does not pre-empt Module 3.
- **Give this its own owner.** Redrawing from scratch is a different skill and a different deliverable from the prose pass, and it should not ride along with it.
- **Consider dropping one of them.** Two diagrams ahead of the module's first cell is a lot, and every fact in them is another thing that has to stay in sync with the notebook.
- **Recommendation:** Do this before any live delivery. These are the first two things a participant sees in the module, and one of them contradicts what Module 1 just taught.

#### M2-9. "Chunks" is the wrong word throughout

- **Where:** `index.en.md` lines 8, 14, 15, 42, 55, 63. Notebook cells 0, 12, 15, 18. `README.md` lines 11, 28, 29, 41.
- **What is wrong:** `faqs_docs.json` holds 300 entries, one per whole document, averaging 7,276 characters. Nothing is chunked. The FAISS store indexes whole documents, and `search_faqs` then truncates each one to 500 characters.
- **Why it matters:** A participant who just finished Module 1 learned that a chunk is a specific node type with an embedding on it. Module 2 uses the same word for something else.
- **Proposed fix:** Say "documents" everywhere the code means the whole entries in `faqs_docs.json`. Keep `Chunk` for Neo4j's actual `Chunk` nodes in Modules 1 and 3.

#### M2-10. The README claims both agents read the graph

- **Where:** `README.md:12`, "Both agents read the graph restored during Setup, including the five hotels added in Module 1."
- **What is wrong:** The vector agent reads a committed FAISS file. It never touches Neo4j.
- **Related:** `README.md:13` says Amazon Nova creates the query embeddings. That is true of the code and false in effect, because the index rejects those embeddings (M2-1).
- **Proposed fix:** Say that the vector agent reads a committed FAISS index over the 300 source documents while the graph agent reads the Neo4j graph extracted from that corpus. They share an underlying source corpus, not a storage engine or an identical representation.

#### M2-11. "Multi-hop" is one hop

- **Where:** `index.en.md:16`.
- **What is wrong:** `Hotel-[:OFFERS_AMENITY]->Amenity` is a single hop. Module 1's page now says every domain relationship starts at `Hotel`, so each document produces a one-hop star.
- **Note:** The notebook heading and the README both say "multiple criteria", which is correct. Only the content page overclaims.
- **Proposed fix:** Use "multiple criteria" on the page too.

#### M2-12. "Text2Cypher" is used wrongly and before it is defined

- **Where:** `index.en.md:30`.
- **What is wrong:** The notebook does not use `Text2CypherRetriever`. It uses a hand-written `@tool` whose docstring carries the schema and lets the model write raw Cypher. `Text2CypherRetriever` is Module 3's subject and is defined there, not here.
- **Proposed fix:** Delete the term, or describe the actual mechanism.

#### M2-13. The prose states what the model will do

- **Where:** `index.en.md:42`, `:55`, `:72`. Notebook cell 0's table, twice. Notebook cells 11, 13, and 14 print "Vector agent reasons from 3 documents" unconditionally, after the fact, regardless of what happened.
- **What is wrong:** These are LLM calls. The output varies. The page says "It will return results from similar-looking documents and the LLM may fabricate details."
- **Refuted by the live run:** On the Antarctica test the agent did not fabricate. It answered that Antarctica has virtually no traditional hotels and explained the Antarctic Treaty System.
- **Why it matters:** A current Claude given three irrelevant hotel documents is likely to notice they are irrelevant. Test 4 probably will not produce a hallucination even after M2-1 is fixed, and the module's title rests on it.
- **Proposed fix:** Reframe test 4 around what is actually observable and always true. The retriever gives no signal that its results are irrelevant, and the model has to notice on its own. Change the unconditional print lines to report what happened rather than what was expected.
- **Recommendation:** Do this. A test whose stated outcome does not reproduce is worse than no test.
- **Test status:** Keep all four tests. Treat Tests 1 and 3 as the core path. Mark Test 2 as an optional reinforcement of the same complete-set limitation as Test 1, and Test 4 as an optional observation because the model's response to irrelevant neighbors is stochastic. Optional does not mean unverified: all four retrieval paths still need automated execution coverage.

#### M2-14. Token numbers are cumulative, and the prose says they are comparable

- **Where:** cell 9 tells the participant the numbers let them compare token usage between the two agents.
- **What is wrong:** The same two `Agent` objects run all four tests, so `accumulated_usage` is a lifetime sum. The graph agent reaches 11,981 by test 4. Tool counters carry over too, so by test 4 each agent has four turns of prior history.
- **Why it matters:** In test 4 the vector agent already knows from earlier turns that its tool is broken, which changes its answer.
- **Proposed fix:** Create fresh agents per test. If the reuse is deliberate, say the numbers are cumulative.
- **Recommendation:** Fresh agents per test. It gives clean per-query numbers and removes the cross-test contamination.

#### M2-15. Dead configuration guidance and unused imports

- **Where:** cell 3's trailing comment tells the participant to set `MODEL = OpenAIModel(model_id="gpt-4o-mini")`.
- **What is wrong:** Nothing reads a `MODEL` variable, because neither agent takes a `model=` argument. Following the instruction does nothing.
- **Also:** `from pathlib import Path` is unused. `os` is imported three times, in cells 2, 3, and 5.
- **Proposed fix:** Delete the comment and the unused imports. If M2-3 is fixed, the comment could become real guidance.

#### M2-16. The three test names disagree across three surfaces

- **Page:** Aggregation, Counting, Multi-hop, Out-of-domain.
- **README:** Aggregation, Counting, Multiple criteria, No matching data.
- **Notebook headings:** Calculate an Average, Count Matching Hotels, Apply Multiple Criteria, Handle a Question with No Matching Data.
- **Why it matters:** A participant switching between the page and the notebook has to re-map the names each time.
- **Proposed fix:** Pick one set of four names and use it everywhere.

#### M2-17. The tool docstring drifts from the live graph

- **Where:** `query_knowledge_graph` in cell 8. This docstring is the graph agent's entire model of the schema.
- **What is wrong:**
  - `Amenity` properties omit `fee`, which is present on 32 of 83 nodes.
  - `Service` appears in the relationship list with no properties documented. The live node has `name`, `description`, `is_complimentary`, `is_available`, `hours`, and `cost`.
  - `Hotel` omits `hotel_id`, present on 287 of 292.
  - `Document` and `Chunk` are absent entirely.
- **Proposed fix:** Regenerate the docstring from `graph_schema.py` rather than maintaining it by hand.
- **Recommendation:** Worth doing. A wrong schema in the docstring makes the agent write wrong Cypher, and that failure looks like a graph problem.

#### M2-18. The notebook depends on the working directory without saying so

- **Where:** cell 2 uses `os.path.join(os.getcwd(), "..")`. Cell 5 opens the FAISS index and document file by relative path; the repaired version will also open the manifest.
- **What is wrong:** All of those paths need the working directory to be the module folder. The page says only "open the notebook".
- **Evidence this has already bitten someone:** `build_faiss_if_needed()`'s error message interpolates `os.getcwd()`.
- **Proposed fix:** Resolve paths relative to the notebook file, or state the requirement on the page.

### Style and structure

- **One em-dash**, `index.en.md:33`. The rest of the module is clean.
- **Nine of 21 notebook cells have bare-string sources** instead of lists. Cells 7, 10, 11, 13, 14, 16, 17, 19, 20. The other twelve are lists.
- **21 code lines over 88 characters.** One 110-character token-printing line is copy-pasted into eight separate cells.
- **Trailing whitespace** in cells 5, 7, and 8.
- **Two claims in one sentence** at `index.en.md:8`, `:55`, `:63`, `:72`, and notebook cells 12 and 18.
- **Vague phrasing where a concrete statement belongs.** `:42` says the agent "generates and executes Cypher along these lines". Either show the query it produced, or say the query varies per run. `:42` also says "Run both agents and compare their outputs" without saying what to compare or what a correct answer looks like.
- **Three bare arXiv links** under a `**Research background:**` label in the notebook's opening cell. No subject and verb after the label, and no sentence saying what the papers establish or why to open them.
- **Cells do not lead with their purpose.** Cell 4 is a bare heading, followed by cell 5, the largest and most consequential cell in the notebook, with no prose. Cell 6 is a bare heading followed by a 40-line `HookProvider` class with no explanation of what a Strands hook is.
- **Token instrumentation is buried inside Test 1.** It is a general topic and belongs before the tests. The content page never mentions token metrics at all.
- **The notebook has no closing cell.** It ends on a `print()`. No summary and no pointer to Module 3. The page has a Next section; the notebook does not.

### Missing explanation

- **The core mechanism is asserted eight times and explained zero times.** Nowhere does the module say why vector search cannot aggregate. The reason is simple: an approximate-nearest-neighbour index returns a fixed-length list ranked by distance and has no aggregation operator, so any count or average has to be computed by the model from whatever documents it happened to receive. Module 1's page now has exactly this kind of paragraph for why an embedding of `60611` ranks badly. Module 2 needs its equivalent.
- **`k=3` is never explained, and the honest limit is never stated.** Raising `k` would partly fix aggregation, until context and cost stop you. As written the module implies impossibility where the truth is a ceiling.
- **Why FAISS is separate is never answered.** Module 2 should say that FAISS is deliberately retained as a minimal standalone document-RAG baseline. Module 3 then introduces Neo4j vector retrieval, hybrid retrieval, and graph enrichment. The separation is curricular, not an endorsement of maintaining two production embedding stores. The rebuilt FAISS artifact must still use the workshop's shared Nova model, purpose, and width so the baseline is compatible and reproducible.
- **The Module 1 relationship is never stated.** Module 2 has no hard dependency on Module 1. It never touches either retrieval index, never queries the held-out hotels, and its FAISS file is committed. Ordering is enforced only by page weight. The README asserts a dependency that does not exist. The notebook prints a hotel count with no expected value, so a participant cannot tell whether their graph is right.

---

## Recommended order of work

1. **M2-1**, the dimension mismatch and missing artifact contract. The base index is rebuilt at 1024 dimensions from the graph's chunk vectors, the metric is settled, and the manifest, rebuild script, and tests exist. The artifact agent is completing `vectors_sha256` and `vector_source`; committing the artifacts and the notebook-side validator and error-handling work remain open.
2. **M2-2 and M2-2a**, the hidden truncation and invalid Paris aggregation example. Pass complete documents and use the five-hotel Orlando set so `k=3` is provably incomplete.
3. **M2-3, M2-4, M2-5, M2-6**, the four environment and configuration bugs. All are small, all are already solved correctly in Module 1, and all can be done in one pass.
4. **M1-1**, the one-line cleanup fix in Module 1's optional demo.
5. **M2-7 and M2-2b**, tests 3 and 2. Replace Cairo with the verified Chicago comparison, add its lite-build selection and its reporting readiness cell, and give the pool count its source-derived answer of 175.
6. **M2-13**, test 4 and test status. Reframe it around observable retrieval behaviour, retain all four tests, and mark Tests 2 and 4 optional in the learner path.
7. **M2-8**, the two images. Authored from scratch as `.drawio` sources by their own owner and exported into both image trees. Required before any live delivery.
8. **M2-14, M2-15, M2-16, M2-17, M2-18**, the remaining code and consistency fixes.
9. **The prose pass**, covering the style items, the missing explanations, and the Module 1 relationship.

The single highest-value change is rebuilding the FAISS baseline with an explicit compatibility contract. Build it from the chunk vectors the graph already holds: that costs nothing, it is repeatable, and it puts both arms on one embedding space, which is the comparison the module is trying to make. It restores every demonstration without collapsing Module 2 into Module 3. The next highest-value change is replacing Paris with Orlando: a working index is not enough if the headline example can retrieve the complete qualifying set and answer correctly.

---

## Implementation plan

### Goal

Restore Module 2 as a reliable comparison between standalone FAISS document retrieval and structured Cypher over Neo4j, while keeping Module 3 responsible for Neo4j vector, hybrid, and graph-enriched retrieval patterns.

### Assumptions

- FAISS remains the only vector store used by Module 2.
- The committed FAISS artifact uses the shared Nova embedding model, purpose, and 1024-dimension width.
- The committed FAISS vectors are the same vectors Module 1 wrote onto the graph's `Chunk` nodes, exported rather than recomputed.
- Participants load the committed index and do not make 300 document-embedding calls.
- Tests 1 and 3 are the core learner path. Tests 2 and 4 remain in the notebook as optional exercises.
- All four tests remain in automated execution coverage even when some are optional for learners.
- The raw retrieval result is the deterministic evidence. The LLM answer is an observed outcome and is not used as the sole pass condition.
- Existing unrelated working-tree changes are preserved.

### Risks

- The graph-sourced rebuild depends on an Aura graph holding all 300 source documents with exactly one embedded chunk per filename. A lite, partial, duplicated, or stale graph must fail validation rather than mix embeddings from a fallback source.
- FAISS IDs are positional. Any change to document ordering without rebuilding the index can silently associate a vector with the wrong document.
- A valid dimension alone does not prove compatibility. The model, purpose, metric, corpus bytes, document count, index size, and stored vector bytes must agree too. An `IndexFlatL2` baseline and Neo4j's cosine chunk index rank differently unless the vectors are unit-norm.
- The corpus carries 125 explicit "not available" amenity sections. LLM extraction can turn a negation into a positive amenity, which silently breaks any test that depends on a hotel being excluded.
- Full documents increase the model context compared with the current 500-character previews. Token usage and context limits must be measured after truncation is removed.
- LLM wording remains stochastic. Assertions about exact model prose will be brittle.
- The repository already contains unrelated uncommitted notebook and content edits, so each worker needs exclusive file ownership and a narrow patch.

### Parallel execution model

Use at most three worker agents at a time alongside the coordinating agent. Work proceeds in waves so tasks with stable interfaces run together and content work waits for the final queries and outputs.

- **Artifact agent, active:** Owns the FAISS rebuild script, `faqs_vector.index`, `faqs_vector.manifest.json`, and focused artifact-contract tests. It is completing the two integrity fields added in the refined plan. It does not edit `defects.md`, the Module 2 notebook, or learner content.
- **Notebook agent, pending:** Owns the Module 2 notebook runtime: environment loading, pinned model, shared Neo4j connection helpers, manifest validation at load, complete document delivery, visible retrieval evidence, fresh agents per test, and exception handling. It must not rebuild or replace the committed FAISS artifacts.
- **Fixture agent, pending:** Owns `graph_config.py`, the lite-build selection, the readiness cells, and their tests. Its job is to make the five rated Orlando hotels and the filtering Chicago pair present in the full build and reported in any build, not to gate the notebook on an extraction it cannot control. It does not edit the notebook or images.
- **Content agent, pending:** Starts after the Orlando and Chicago contracts are stable. Owns the Module 2 README and the workshop page. It does not write the notebook, and it does not draw the diagrams.
- **Diagram agent, pending:** Owns the two new `.drawio` sources and the exported PNGs in both image trees. Starts once the Orlando numbers are final.
- **Coordinating agent:** Owns the plan, resolves overlaps, integrates the worker patches, runs repository-wide validation, and performs the final factual review.

**One agent writes the notebook.** The notebook agent is the only writer of `2.1_vector_rag_hallucinates.ipynb`. Two agents editing one JSON file cannot be parallelized safely, and nine of the 21 cells still carry bare-string sources, so concurrent rewrites produce diffs nobody can review. Prose changes to notebook cells go to the notebook agent as a patch, and it applies them.

### Phase 1: Rebuild and contract the FAISS artifact

**Status: In progress, final integrity fields and artifact commit remain**

`notebooks/workshop/faiss_artifacts.py`, `notebooks/02-vector-rag-hallucinates/rebuild_faiss_index.py`, `faqs_vector.manifest.json`, `setup/test_faiss_artifacts.py`, and `setup/test_rebuild_faiss_index.py` all exist, and `faqs_vector.index` has been rebuilt in place. Verified: `IndexFlatIP`, `d` 1024, `ntotal` 300, vector norms exactly 1.0, manifest checksum matching the corpus, 13 tests passing. The artifact agent is now adding `vectors_sha256`, the fixed graph `vector_source`, and their negative tests. Committing the artifacts remains separate.

**Outcome:** A reproducible 1024-dimension FAISS artifact that fails loudly when its model, purpose, metric, corpus, ordering, vector bytes, or dimensions drift.

**Checklist:**

- [x] Add a facilitator-side rebuild script that walks `faqs_docs.json` in its stored order and reads each document's vector from the graph's matching `Chunk`.
- [x] Reject missing filenames, duplicate chunks, null embeddings, and wrong-width vectors; do not fall back to a second embedding source.
- [x] Decide the FAISS metric. Settled: L2-normalized vectors in an `IndexFlatIP`, which makes the baseline rank by cosine like Neo4j's chunk index, with the loader rejecting any other metric.
- [x] Add the manifest dataclass, the corpus checksum, and a loader that validates the contract fields, `index.d`, `index.ntotal`, and the document count.
- [x] Add negative tests that prove each mismatch produces a descriptive failure.
- [x] Extend the manifest and the validator with `faiss_metric` and `vector_normalization`, and add their negative tests.
- [ ] Extend them with `vectors_sha256` and the fixed graph `vector_source`, and add those negative tests. The seven fields present today are all shape and provenance labels; nothing yet detects a corrupted vector body whose `d` and `ntotal` still read correctly.
- [x] Rebuild `faqs_vector.index` at 1024 dimensions.
- [ ] Commit the rebuilt `faqs_vector.index` and `faqs_vector.manifest.json`. Both are currently uncommitted working-tree changes.
- [x] Run the artifact tests and record the rebuilt index size, vector count, dimension, and metric.

**Validation:** The index loads as 1024-dimensional with 300 vectors at the recorded metric; the manifest matches the shared contract, the exact corpus bytes, and the vectors actually stored; deliberately altered test fixtures fail for the expected reason; a vector-byte corruption that leaves `d` and `ntotal` intact is still rejected.

**Notes:** The graph export removes the cost and throttling exposure of a 300-call rebuild. Aura access and a complete graph are facilitator-side artifact-build prerequisites; participants still use the committed FAISS artifact without Aura access on the vector arm.

### Phase 2: Repair notebook setup and retrieval execution

**Status: Pending**

**Outcome:** Module 2 loads the contracted FAISS artifact, uses the intended AWS and Neo4j configuration, and exposes retrieval failures instead of converting them into ordinary answers.

**Checklist:**

- [ ] Load `.env` before resolving and exporting the AWS region.
- [ ] Pin both agents to the workshop model and resolved region.
- [ ] Replace the hand-written Neo4j credential and database handling with the shared helpers.
- [ ] Resolve the index, documents, and manifest paths predictably and give an actionable error when the notebook starts in the wrong directory.
- [ ] Validate the complete FAISS contract before creating either agent.
- [ ] Normalize the query vector before searching, so the printed scores are cosine similarities and agree with `manifest.vector_normalization`. Ranking is unaffected either way, because an unnormalized query scales every inner product by the same constant, but the displayed number is only interpretable when both sides are normalized.
- [ ] Remove the 500-character slice and pass complete retrieved documents to the vector agent.
- [ ] Stop swallowing FAISS and Cypher exceptions.
- [ ] Display filenames, scores or distances, and the complete retrieved text before each vector-agent answer.
- [ ] Create fresh agent instances for every test and report per-test token usage.
- [ ] Restrict the Cypher tool to read operations and apply a query timeout.

**Validation:** Setup fails on a mismatched artifact or database; a direct vector smoke query returns three complete documents; tool errors remain visible; repeated tests do not share history or token counters.

### Phase 3: Make all four tests factually observable

**Status: Pending**

**Outcome:** Each test demonstrates a property visible in the raw retrieval or graph result, without relying on a particular LLM response.

**Checklist:**

- [ ] Replace the Paris aggregation with the five-hotel Orlando query and document the graph answer of 4.62.
- [ ] Add all five Orlando documents to lite selection, and have the readiness cell report the rated Orlando hotels it found instead of hard-failing.
- [ ] Assert deterministically, with no model call, that a `k=3` retrieval for the Orlando query returns three hits covering fewer than five of the five Orlando documents.
- [ ] Keep the pool-counting test, print the source-derived count of 175 beside the graph's count, and mark it optional in the learner path.
- [ ] Replace Cairo with the verified two-hotel Chicago spa-and-pool comparison, and update `REQUIRED_CITIES` and the `select_lite_files` docstring with it.
- [ ] Have the readiness cell find and print a city with multiple candidates, at least one match, and at least one exclusion, preferring Chicago, rather than gating on Chicago alone.
- [ ] Keep the Antarctica test, expose the nearest documents and scores, and mark the learner exercise optional.
- [ ] Describe Test 4 as the behaviour of a top-k baseline without a relevance threshold, not as a guarantee that the model fabricates an answer.
- [ ] Ensure all four tests still execute in the automated notebook run.

**Validation:** Orlando has five rated graph records; `k=3` cannot contain the complete Orlando set; the Chicago AND query filters at least one candidate; Antarctica returns FAISS neighbors while Neo4j returns no matching hotel; all four test cells execute from fresh agents.

### Phase 4: Align learner content and diagrams

**Status: Pending**

**Outcome:** The notebook, README, workshop page, and diagrams describe the repaired implementation and clearly distinguish Modules 2 and 3.

**Checklist:**

- [ ] Use "documents" for the whole FAISS records and reserve "chunks" for actual Neo4j `Chunk` nodes.
- [ ] Explain that Module 2 deliberately uses FAISS as a minimal standalone vector-RAG baseline.
- [ ] Explain that Module 3 introduces Neo4j vector, hybrid, and graph-enriched retrieval.
- [ ] Use one consistent set of four test names and visibly label Tests 2 and 4 optional.
- [ ] Explain why top-k retrieval alone cannot guarantee exact set aggregation, while acknowledging that filters, thresholds, and larger `k` can change the baseline.
- [ ] Replace deterministic claims about model answers with instructions for comparing retrieved evidence, Cypher results, and grounding.
- [ ] Author both diagrams as new `.drawio` sources around Orlando, the 4.62 graph result, the standalone FAISS branch, and the correct `guest_rating` property, then export the PNGs into both `workshop-content/images/` and `static/images/`.
- [ ] Add a notebook closing cell that summarizes the limitation and points to Module 3.

**Validation:** A cross-surface terminology and fact check finds no Paris or Cairo test remnants, no `h.rating`, no `City` node, no claim that both agents read Neo4j, and no guarantee that the model hallucinates.

### Phase 5: Integrate and run the workshop path

**Status: Pending**

**Outcome:** The repaired module passes static checks and an end-to-end Module 1 through Module 3 execution without hiding failures.

**Checklist:**

- [ ] Review every worker patch against its assigned file ownership and preserve unrelated edits.
- [ ] Validate notebook structure, source formatting, and Python compilation.
- [ ] Run focused unit tests for the artifact contract, the rebuild script, lite selection, the readiness cells, and the notebook runner.
- [ ] Execute Modules 1 through 3 in order against the configured workshop environment.
- [ ] Confirm the notebook's own deterministic retrieval assertion passes: three hits for the Orlando query, covering fewer than five of the five Orlando documents. That assertion is the module's lesson and needs no model call, so it is the gate rather than an eyeball check for `Query error:`.
- [ ] Confirm no vector tool call returns `Query error:`.
- [ ] Confirm expected Orlando and Chicago graph facts in the executed notebook.
- [ ] Review token usage after complete documents replace 500-character previews.
- [ ] Save or report the executed-notebook evidence and any stochastic answer differences.

**Validation:** All focused tests pass; Modules 1 through 3 execute successfully; no tool error is represented as a successful text result; retrieval evidence and graph answers match their documented contracts.

### Completion criteria

- The committed FAISS index is reproducible from the graph's own chunk vectors, 1024-dimensional, built at a recorded metric, and protected by a manifest that validates the contract fields, the corpus bytes, and the stored vector bytes.
- Module 2 remains architecturally distinct from Module 3.
- The notebook passes complete retrieved documents and shows them before the agent answer.
- Orlando makes the `k=3` aggregation limitation provable.
- Chicago makes the multiple-criteria filter observable.
- All four tests remain present, with Tests 2 and 4 optional for learners and mandatory for automated execution.
- Configuration, database selection, model selection, token metrics, and failure handling match the shared workshop contracts.
- Notebook, README, workshop page, diagrams, and executed results agree.
- Both diagrams have committed `.drawio` sources and identical exports in both image trees.
- The deterministic retrieval assertion, not a reading of the model's answer, is what proves the `k=3` limitation.

---

## Verified offline for this revision

Checked against the working tree and the committed corpus, with no live service, so
no worker needs to repeat them:

- All 300 `faqs_docs.json` entries are byte-identical to their `data/*.txt` file. The longest document is 7,442 characters, so nothing reaches the 8,000-character truncation in `_embed` and nothing splits at `CHUNK_SIZE` 12,000. Each document is therefore exactly one `Chunk` whose text is the whole document.
- The originally committed `faqs_vector.index` was an `IndexFlatL2` with `d` 384 and `ntotal` 300, its 450 KB matching 384 x 4 x 300 exactly. That is the defect M2-1 describes.
- The rebuilt `faqs_vector.index` in the working tree is an `IndexFlatIP` with `d` 1024 and `ntotal` 300. Its first vectors have norm exactly 1.0, so the export normalizes and the baseline now ranks by cosine, matching Neo4j's chunk index. `faqs_vector.manifest.json` records `faiss_metric` `inner_product` and `vector_normalization` `l2`, and its `corpus_sha256` matches the committed corpus bytes.
- The 13 tests in `setup/test_faiss_artifacts.py` and `setup/test_rebuild_faiss_index.py` pass. The manifest carries seven fields; `vectors_sha256` and `vector_source` are not among them yet.
- `BedrockEmbeddings` sends `EMBEDDING_MODEL_ID`, `EMBEDDING_PURPOSE`, and 1024 dimensions, the same three values the notebook's `_embed` sends.
- Orlando has five documents, rated 4.7, 4.5, 4.6, 4.7, and 4.6. The mean is 4.62.
- Chicago has two documents. Windward Mile Tower, rated 4.5, lists no pool and no spa, and its Pool section is a negation. Lakeview Horizon Suites, rated 4.4, has both.
- 175 documents name a pool in their amenity bullet list. 125 carry an explicit "Pool facilities are not available at this property" section. The two add to 300.
- `sample = paths[0]` in Module 1's cell 15 is one of the participant's real held-out documents, which is what makes the naive M1-1 fix unsafe.
- The two Module 2 PNGs have no `.drawio` source, and they are byte-identical in `workshop-content/images/` and `static/images/`.

---

## Not verified

- **The pre-build state of the graph.** Module 1 and Module 6 have both already run on the Aura instance. The dump's own contents were inferred from the 287 hotels carrying `hotel_id` versus the 5 that do not, and from the 295-document claim on Module 1's page. A clean restore is needed to check the participant path from the start.
- **Whether cell 19's empty-index message and cell 22's no-hotel message ever print.** Both indexes are already online and all five held-out documents are already loaded. Both code paths were shown to be reachable: four documents in the corpus produce no hotel at all, and the query correctly returns zero rows for them.
- **The four-minute build time.** Checking it means running the extraction and spending Bedrock tokens.
- **Whether the extraction turned any of the 125 pool negations into a `Pool` amenity.** This decides whether Test 2's graph count can match the source count of 175, and whether Windward Mile Tower is genuinely excluded on a lite build. It needs one Cypher query against a built graph.
- **Whether the vector agent hallucinates once M2-1 is fixed.** The behaviour claims come from the committed executed notebooks, where the tool was already broken. This needs a live run to settle, and test 4's premise should be treated as unproven until then.
- **Whether `global.anthropic.claude-sonnet-4-6` is granted in the workshop account.** M2-3 is a real divergence from the pinned model either way, but no Bedrock call was made to check the grant.
- **The three arXiv links in the notebook's opening cell.** Outbound network was blocked, and a known-good control returned empty too, so nothing was proven. `2601.05214` is worth a manual check.
