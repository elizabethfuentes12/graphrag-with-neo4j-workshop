# Summary of Changes Made to the Workshop

---

## 1. Overview

The teaching material was already here, and the argument it makes still runs the workshop: vector RAG
hallucinates, a graph grounds it, and a grounded agent abstains honestly. Most of what follows is structural
work around that, not a rethink of it.

The workshop gains two modules. One shows how the graph gets built in the first place, and one shows how to
deploy the finished agent to AgentCore Runtime. Module 4 was also rewritten: it ran on an e-commerce refund
scenario that had nothing to do with the hotel story the rest of the workshop tells.

- **Three changes**: a new Module 1 where people build part of the graph themselves, a full renumbering
  of every module, and a new Module 5 that deploys the agent to AgentCore Runtime.
- **Where it stands**: all six modules are authored, and the repository check script passes all nine of its
  checks. 
- **Module 5 is already deployed and running in AWS**: the AgentCore Runtime, its ECR repository, and its
  CodeBuild project all exist and keep accruing charges until someone removes them. Nothing in the workshop
  deletes them.
- **What is left**:
  - Do one more walk through of all the notebooks.
  - Module 5's README.
  - Two open review findings on Module 5: a dependency list that floats one entry while claiming to pin
    everything, and a build step that records nothing about what it packaged.
  - Live end-to-end runs.
  - **One decision from the repo author**: which of the two image folders is the real one. See section 5.
  - **One setup bug to fix**: the install command creates `notebooks/.venv`, but nothing points the
    notebook kernel at it, so a participant following the README lands on the system Python and the first
    import fails. This needs fixing regardless of the images decision.

---

## 2. The new module structure

| # | Module | Notebook | State |
|:-:|---|---|---|
| 0 | Setup | checklist only | Moves to pre-session, with `verify_setup.py` to check credentials |
| 1 | Build the graph | `1.1_build_graph.ipynb` | **New.** Written, needs a live run |
| 2 | Vector RAG hallucinates | `2.1_vector_rag_hallucinates.ipynb` | Renumbered and cleaned |
| 3 | Retrieval patterns and the grounded booking agent | `3.1`, `3.2` | Same content, renumbered |
| 4 | Production agent with AgentCore | `4.1`, `4.2` | **Rewritten.** Now the hotel domain |
| 5 | Deploy to AgentCore Runtime | `5.1_deploy.ipynb` | **New.** Notebook, container, and page all landed |
| 6 | Neo4j inspectable memory | `6.1_neo4j_memory.ipynb` | Promoted from optional to core |

- **Module 1 shows how the graph gets built**: participants extract five hotel documents live with Bedrock
  and Neo4j, and those five hotels stay in their graph for the rest of the day.
- **The dump holds the other 287 hotels**: five documents were held out of the dump on purpose, so Module 1
  has something real to build rather than a demo that rebuilds what is already there.
- **Nothing gets deleted**: whatever a participant builds stays. There is no build-then-wipe step to explain
  away.
- **One folder shape**: `notebooks/0N-name/` matches `workshop-content/content/0N-name/` for every module,
  so a notebook and the page that describes it are easy to find from each other.

---

## 3. What changed

**Content and structure**

- **Renumbered everything in one pass**: notebook names, notebook folders, content folders, page titles,
  page weights, image paths, and every cross-page link moved together. Moving only some of them is what
  leaves broken images and dead links behind.
- **Fixed stale names**: "Demo 01b", "Demo 06", "Module 7", "Module 8", and the old timing stamps are gone.
- **Fixed broken links**: six links pointed at files and folders that did not exist. All six are gone.
- **Deleted the cleanup page**: hosted accounts get reclaimed after the event, so there is nothing for a
  participant to tear down. The useful parts moved into the wrap-up page.
- **Filled in the summary page**: it now carries the workshop's argument and the decision tables, while
  wrap-up keeps the accomplishments, key concepts, and next steps. The two pages no longer say the same
  thing twice.
- **Added per-module READMEs**: five of six are written. Module 5's is the one still missing.
- **Rewrote the root README**: two getting-started paths, hosted first and self-paced second.
- **Kept hard numbers out of prose**: hotel and chunk counts are read from the graph at runtime instead of
  typed into text, because typed counts go stale the moment the graph changes.

**Module 4, from e-commerce to hotels**

- **The old tools are gone**: `lookup_customer`, `get_order_history`, and `process_refund` were placeholders
  returning canned data.
- **Two real retrieval tools replace them**: `search_hotel_knowledge` and `graph_query`, both querying the
  same graph the earlier modules built.
- **The point of the module**: the retrieval code from Module 3 does not change. Only the boundary around it
  moves, from in-process to a managed Gateway endpoint.

**Naming, which the shipped IAM policy decides for us**

- **Lambdas must start with `hotel-booking-`, roles with `workshop-`**: the policy scopes by name prefix and
  cannot be changed from this repo.
- **The old `customer-service-*` names fall outside that grant**: any account running under the shipped
  policy would stop at the first role the notebook creates. Renamed and verified in `4.1`.

**The graph**

- **Participants start with most of the graph already built**: 287 hotels are loaded before the workshop
  begins, so nobody spends the morning waiting on a build.
- **Module 1 adds the last five hotels and the two search indexes**: these are left out of the starting
  graph on purpose, so that Module 1 builds something real instead of re-running work that is already done.
  Everything a participant builds stays in their graph for the rest of the day.
- **Which five hotels are left out is fixed in code**: `notebooks/01-build-graph/held_out_documents.py`.

**Checking the work**

- **`setup/check_repo.py` was written first, on purpose**: nine checks that need no AWS and no Neo4j. They
  catch the things that break quietly, such as a dead link, a duplicate page weight, or a file path named in
  prose that does not exist. Everything written since has landed against it, and all nine pass today.
- **`setup/verify_setup.py` checks a participant's credentials** before they hit a failure mid-notebook.
- **The vacuous-test trap**: a grounded agent saying "I don't know" looks exactly like a completely broken
  one, so a test that checks only for the refusal still passes when nothing works. Every grounding check now
  sits beside a **positive control**: an assertion on a real value, such as the Cairo hotel's full address,
  that a broken system could not produce.

---

## 4. Duplicate code, and duplicate images

**What was there**

- **Three copies of the shared Python code had accumulated**: `notebooks/workshop/`, the `notebooks/` root,
  and a set inside the retrieval patterns folder.
- **They had drifted apart**: not backups, but three slightly different programs sharing one set of names,
  so which one a notebook picked up was not predictable.
- **`notebooks/workshop/` was the one to keep**: in each case it already carried the fixes the others had
  missed.

**How it was cleaned up**

- **Shared code lives in `notebooks/workshop/`**: anything two or more labs use.
- **Lab code lives in its own lab folder**: anything exactly one lab uses.
- **The `notebooks/` root holds no `.py` files at all**: this is the fix that actually holds, because with
  nothing at the root there is no second copy left to pick up by accident.
- **The other two copies are deleted**: there is exactly one implementation of each module now.
- **Consolidating surfaced two bugs**: one that killed the reservation Lambda on startup, and a fixture file
  that had to be kept in three identical copies to be found at all. Both are fixed.

**The prose and images**

- **Content lives in `workshop-content/`**: the markdown pages and the images they use were renumbered and
  updated together.
- **`static/images/` still holds a duplicate set**: eleven files, byte-identical to
  `workshop-content/images/`, both tracked in git.
- **The duplicates were left alone on purpose**: which tree is authoritative is the one open decision left
  for the repository author, and it is written up in section 5. In the meantime `check_repo.py` asserts the
  two trees stay byte-identical, so they cannot quietly drift apart while the question is open.

---

## 5. The one open question: which images folder is the real one

Two folders hold the same eleven files, byte for byte, and both are tracked in git:

- `static/images/`
- `workshop-content/images/`

One should be kept and the other deleted. We did not guess, because deleting the wrong one breaks either
the rendered pages or the platform build, and both are awkward to notice after the fact.

What points each way:

- **`workshop-content/images/` is the tree in use today**: every image reference in every markdown page
  resolves to it, so the workshop renders correctly from this tree right now.
- **Nothing in this repository references `static/images/` at all**: no page, no notebook, no build file.
  The only mention of the folder anywhere is one row in the README's repository-layout table.
- **We think, but cannot confirm, that the platform wants `static/`**: our understanding is that AWS
  Workshop Studio looks for a top-level `static/` folder, but the Workshop Studio configuration for this
  workshop lives outside this repository, so we have no way to check that from here. You can.

Whichever way it goes, the follow-on work is small: delete one tree, repoint anything that referenced it,
and drop the `check_repo.py` check that currently holds the two in sync.
