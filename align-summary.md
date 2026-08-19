# Summary of Changes Made to the Workshop

---

## 1. Overview

The workshop is adding 2 modules to show how the graph gets built and how to deploy the agent to agentcore. Also the module 4 was a separate domain of e-commerce so that was updated to match the hotel examples of the rest of the workshop. 

- **Three big changes**: a brand new Module 1 where people build part of the graph themselves, a full
  renumbering of every module, and showing how to deploy an agent to agentcore.
- **Out of scope**: all the AWS Workshop Studio infrastructure. No CloudFormation, no IAM policy, no hosting.
  That already exists and ships from somewhere else.
- **In scope**: notebooks, content pages, Python code, and one binary Neo4j dump file.
- **Where it stands**: Modules 1, 2, 3, and 6 are done. Module 4 Part 1 and Module 5 are the work still in
  flight. The prose and the checking script are done.

---

## 2. The new module structure

| # | Module | Notebook | State                                                 |
|:-:|---|---|-------------------------------------------------------|
| 0 | Setup | checklist only | Moves to pre-session, gains a credential check script |
| 1 | Build the graph | `1.1_build_graph.ipynb` | **New.** Done, except one live run                    |
| 2 | Vector RAG hallucinates | `2.1_*.ipynb` | Renumbered and cleaned                                |
| 3 | Retrieval patterns and the grounded booking agent | `3.1`, `3.2` | Unchanged content, renumbered                         |
| 4 | Production agent with AgentCore | `4.1`, `4.2` | **Changed** Changed to hotel domain                   |
| 5 | Deploy to AgentCore Runtime | `5.1_deploy.ipynb` | **New.** In progress                                  |
| 6 | Neo4j inspectable memory | `6.1_*.ipynb` | Promoted from optional to core                        |

- **Module 1 demonstrates how graphs get build**: Participants extract 5 hotel documents live with Bedrock and Neo4j,
  and those 5 hotels stay in their graph for the rest of the day.
- **The dump holds the other 287 hotels**: 5 documents were held out of the dump on purpose so Module 1 has
  something real to build.
- **Nothing gets deleted**: what a participant builds stays. There is no build-then-wipe step.
- **One folder shape**: `notebooks/0N-name/` matches `workshop-content/content/0N-name/` for every module.
- 

---

## 3. What changes were made

**Content and structure**

- **Renumbered everything at once**: notebook names, notebook folders, content folders, page titles, page
  weights, image paths, and every cross-page link, all in one pass.
- **Fixed stale names**: "Demo 01b", "Demo 06", "Module 7", "Module 8", and the old timing stamps are gone.
- **Fixed broken links**: six dead links to files and folders that never existed are gone.
- **Deleted the cleanup page**: hosted accounts get reclaimed after the event, so there is nothing to tear
  down. Its useful content moved into the wrap-up page.
- **Filled the summary page**: it now carries the argument and the decision tables instead of a second
  victory lap. Wrap-up keeps the accomplishments and next steps.
- **Wrote per-module READMEs**: five of six are done. Module 5's is owned by the session building Module 5.
- **Rewrote the root README**: two paths, hosted first, self-paced second.
- **No hard numbers in prose**: hotel and chunk counts are read from the graph at runtime, never typed into
  text, because they drift.

**The graph**

- **The dump was repaired in place**: fixed on the live staging database rather than rebuilt from a script,
  then verified by querying it.
- **The five held-out hotels are a committed constant**: `notebooks/01-build-graph/held_out_documents.py`.
- **The two search indexes are created by Module 1**: they are deliberately absent from the dump, so
  Module 1's index step does real work.

**Naming, forced by the shipped IAM policy**

- **Lambdas must start with `hotel-booking-`**, roles with `workshop-`. The old `customer-service-*` names
  would have failed for every participant. They are fixed.
- **The old e-commerce tools are going**: `lookup_customer`, `get_order_history`, and `process_refund` are
  replaced by two real retrieval tools, `search_hotel_knowledge` and `graph_query`.

**Checking**

- **`setup/check_repo.py` was written first**: nine checks, no AWS and no Neo4j needed. It asserts notebooks
  parse, Python compiles, links and images resolve, page weights are unique, banned old names stay gone, and
  every file path named in code or prose actually exists.
- **The vacuous-test problem**: a grounded agent saying "I don't know" looks identical to retrieval being
  completely broken. So every grounding test now needs a **positive control**, an assertion on a real exact
  value such as the Cairo hotel's full address, next to its negative one.

---

## 4. Duplicate code, and duplicate images

- **There were three full copies of the shared Python code**, all live at the same time: one in
  `notebooks/workshop/`, one loose in `notebooks/`, and one in `notebooks/02-retrieval-patterns/`.
- **They had drifted apart**: two of the copies differed by 94 lines in one file and 77 in another.
- **Which copy used was non-deterministic**: it depended on whether the caller used `sys.path.insert` or
  `sys.path.append`. Notebooks and build scripts silently loaded different files under the same name.
- **We could not tell which one was correct**, so we reiewed and choose to use `notebooks/workshop/`, because in each case it was the other copy plus a
  documented fix.

**How it was cleaned up**

- **Shared code lives in `notebooks/workshop/`**: anything two or more labs use.
- **Lab code lives in its own lab folder**: anything exactly one lab uses.
- **`notebooks/` root holds zero loose `.py` files**: this is the actual fix. With nothing at the root, no
  file can shadow a lab folder, so the import order stops mattering.
- **The import style now means something**: a flat import means "this file is in my lab folder." A
  `workshop.` import means "this is shared, editing it affects other labs."
- **The other two copies are deleted**: there is one implementation of each module now.
- **Two bugs came out with it**: `graph_connection.py` no longer crashes on import, which used to kill a
  Lambda at cold start, and the fixture data path now resolves properly instead of being duplicated three
  times.

**The prose and images**

- **Content lives in `workshop-content/`**: the markdown pages and the images they use were updated together
  during the renumbering.
- **`static/images/` still holds a duplicate set**: eleven files, byte-identical to `workshop-content/images/`,
  and both are tracked in git.
- **The duplicates were left alone on purpose**: which tree is authoritative is a question for the repository
  author, recorded in `author-questions.md`. `check_repo.py` asserts the two trees stay byte-identical, so
  they cannot silently drift while the question is open.
