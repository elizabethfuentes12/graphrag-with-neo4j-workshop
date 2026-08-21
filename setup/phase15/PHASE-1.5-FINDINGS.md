> **RETRACTED 2026-08-21.** The conclusions below are withdrawn. The run 1 comparison
> was not fair between arms: the vector agent received an added "base your answer on what
> the search returns" instruction that the graph agent did not, the judge used the graph's
> own extraction output as ground truth for both arms, the graph tool's results were capped
> at 15 rows while the vector tool's were not, and no question in the set required graph
> traversal. On the judge's own labels the graph arm scored 24 correct out of 24 against the
> vector arm's 15 correct, 8 partial, 1 incorrect, which is the opposite of what this
> document concluded. The deterministic measurements survive and are listed in `defects.md`
> under Phase 1.5. Do not cite anything else here. Run 2 is complete and its results are in
> `defects.md` under Phase 1.5, with tables at `PHASE-1.5-REPORT-RUN2.md`.

# Phase 1.5 findings: what the repaired Module 2 comparison actually demonstrates

Run date: 2026-08-21
Chat model: `us.anthropic.claude-sonnet-5`, region `us-east-1`
Embedding model: `amazon.nova-2-multimodal-embeddings-v1:0`
FAISS artifact: 300 vectors, 1024 dimensions, `inner_product` over L2-normalized rows
Corpus checksum: `c16b35bf926933fcd365e7bf00015adcb0bf65ab0aef830ce0f9e268b59d5e6b`
Graph: `neo4j+s://471c14c2-staging.databases.neo4j.io`, database `neo4j`, 292 hotels, 300 documents

48 trials, 6 per question per retrieval arm, against the required minimum of 3. Every
trial used a fresh agent and a fresh model client. The trials were collected in five
separate processes, so no trial shared a session, a client, or a token counter with
any other. The raw evidence is in `evidence/phase15-merged.json` and the generated
tables are in `PHASE-1.5-REPORT.md`.

Zero trials produced a swallowed tool error. The M2-1 dimension mismatch is gone, and
every vector retrieval returned three real documents.

## The headline: the module title is not supported

"Vector RAG Hallucinates" does not reproduce. Across 24 vector-arm trials the judge
applied the `fabricated` grounding label zero times. The vector agent invented no
hotel, no rating, no amenity, and no address.

| Vector arm, 24 trials | Count |
| --- | --- |
| Fabricated | 0 |
| Incorrect | 1 |
| Partial | 8 |
| Correct | 15 |

The single `incorrect` trial answered "3 hotels" to the pool count. That is an
undercount drawn from three retrieved documents, not an invention. The model reported
what it was given.

Test 4 confirms what defects.md M2-13 predicted. On all six Antarctica trials the
vector agent was factually correct. Three declined on insufficient evidence, two
answered from the retrieved documents, and one volunteered correct outside knowledge
about the Antarctic Treaty. None fabricated a hotel. The module cannot rest its title
on this test.

**Recommendation:** Rename the module around incomplete top-k evidence and the absence
of an aggregation operator. Do not retain "hallucinates."

## The k=3 limitation is real for one retrieval and false for an agent

The plan assumed Orlando would make the ceiling provable, because the corpus holds five
Orlando hotels and `k=3` can return at most three. The first half holds. The second
half does not.

The vector agent answered Orlando correctly in 3 of 6 trials. It got there by looping.
It read the filenames in its own retrieved evidence, saw `hotel-orlando-001`, `-003`,
and `-005`, inferred that `-002` and `-004` must exist, and then searched for those
names directly:

```
q='average guest rating of hotels in Orlando'  -> orlando-001, orlando-005, orlando-003
q='Orlando hotel guest rating'                 -> orlando-005, orlando-003, santafe-001
q='hotel-orlando-002 hotel-orlando-004 ...'    -> orlando-002, orlando-001, orlando-005
q='hotel-orlando-004'                          -> orlando-004, orlando-001, orlando-005
```

Four searches at `k=3` covered all five Orlando documents, and the agent then computed
4.62 correctly. Three of six trials reached full coverage this way.

The deterministic assertion the plan proposes for Phase 3 is still true and still worth
keeping. A single `k=3` retrieval for the Orlando query returns three hits covering
fewer than five of the five Orlando documents. What changes is the claim built on top
of it. The limitation belongs to one retrieval call, not to the agent, and the prose
has to say so. An agent that can call its retriever repeatedly can defeat a small `k`
whenever the corpus uses predictable identifiers.

**Recommendation:** Keep Orlando and keep the deterministic single-retrieval assertion
as the gate. Describe the limit as a property of one top-k call. State plainly that the
agent sometimes works around it, and that the workaround depends on guessable filenames
rather than on anything the retriever provides.

## Pool counting is the strongest test in the module, and it is currently marked optional

Pool counting is the one question where the vector arm fails reproducibly.

| Pool counting, 6 vector trials | Result |
| --- | --- |
| Factuality | partial x5, incorrect x1 |
| Grounding | insufficient x5, grounded x1 |

Every vector trial answered "3 hotels" or "at least 3 hotels" against a true 175. No
filename trick helps here, because enumerating 175 documents through a `k=3` window is
not something an agent can bluff its way to. Five of six trials explicitly flagged that
the tool retrieves rather than counts.

This is the demonstration the module wants. The plan currently marks it optional and
promotes Orlando, where the vector agent succeeds half the time.

**Recommendation:** Promote pool counting to the core learner path. Demote Orlando to
the supporting example.

## The graph arm is confidently wrong on the pool count, and nothing says so

All six graph trials answered **168 hotels**. The corpus says **175**. Every one of the
six was stated without qualification, and the judge scored them all correct because the
graph result was the reference it was given.

The gap now has a full explanation:

- 4 documents that list a pool produced no `Hotel` node at all. They are
  `hotel-austin-002.txt`, `hotel-mumbai-001.txt`, `hotel-sanfrancisco-004.txt`, and
  `hotel-tucson-001.txt`. That drops 175 to 171.
- 1 document, `hotel-austin-001.txt`, carries the "Pool facilities are not available at
  this property" negation and the extraction minted a `Pool` amenity from it anyway.
  That raises 171 to 172. This is the M2-7 hazard, observed live, on one document.
- 4 pool-bearing hotels are each linked to two documents, because entity resolution
  merged them. Counting distinct hotels rather than documents takes 172 to 168.

Per document the extraction is accurate. The graph agrees with the source on the pool
question for 295 of the 296 documents that produced a hotel. The corpus-level count is
still wrong, and the graph agent presents it as fact.

**Recommendation:** This is a defect in the module's own argument, and it is worse than
the vector arm's failure. The vector agent said "at least 3" and flagged its limits. The
graph agent said "168" and flagged nothing. Print the source-derived 175 beside the
graph's 168 as M2-2b already requires, and use the difference to teach that a graph
answers exactly what was extracted into it. Do not present 168 as ground truth.

## Chicago does not separate the two arms on the answer

The vector arm answered Chicago correctly in 6 of 6 trials, grounded every time. Both
Chicago documents land in the top three, so `k=3` is sufficient and the AND predicate
never gets to matter for the vector side. The graph arm was also correct 6 of 6.

The test still separates the arms on mechanism. The graph applies both conditions in
the query, while the vector arm gets both documents by luck of a two-hotel city and
reads the amenities out of the text. That is a real distinction and it is worth showing,
but the module cannot claim the vector arm fails here, because it does not.

**Recommendation:** Keep Chicago and keep the Chicago fix from M2-7, because Cairo
excludes nothing at all. Reframe the lesson from "the vector arm gets this wrong" to
"the graph applies the filter, the vector arm has to be handed the right documents
first." Note in the prose that a two-hotel city is inside `k=3` on purpose.

## M2-17 confirmed with numbers: the tool docstring does not hold the agent

The graph agent made 121 tool calls across 24 trials, a mean of 5.0 per trial against
1.6 for the vector arm. 32 of those calls, 26 percent, returned zero rows.

The agent repeatedly wrote Cypher against a schema that does not exist, even though the
docstring states the correct one:

| Off-schema token the agent wrote | Calls |
| --- | --- |
| `LOCATED_IN` | 24 |
| `City` | 20 |
| `HAS_AMENITY` | 13 |
| `rating` | 13 |
| `guestRating` | 6 |

The real schema is `OFFERS_AMENITY`, `guest_rating`, and the city inside `Hotel.address`.
The agent recovers by probing, which is why the graph arm costs 5 calls per answer.

This also indicts the architecture diagram. M2-8 records that the diagram draws a `City`
node and queries `h.rating`. The model invents both those same mistakes unprompted. The
diagram is drawn to the model's wrong prior rather than to the graph.

**Recommendation:** Do M2-17. Generate the docstring from `graph_schema.py`, and add the
one line the agent most needs, which is that there is no `City` node and no `LOCATED_IN`
relationship.

## Token cost after truncation is removed

Removing the 500-character slice did not cause a context problem. The largest mean was
43,345 total tokens for the Orlando vector trials, where the agent ran four searches and
each returned three complete documents of roughly 7,000 characters.

| Question | Vector mean total tokens | Graph mean total tokens |
| --- | --- | --- |
| Orlando aggregation | 43,345 | 36,132 |
| Pool counting | 21,282 | 25,872 |
| Chicago criteria | 13,891 | 32,807 |
| Antarctica | 9,610 | 9,118 |

The vector arm is cheaper on three of four questions. The module should not claim the
graph arm is cheaper. It is cheaper only where the vector arm loops.

## Gate decision

Phase 2 may proceed. The implementation defects M2-2 through M2-6 and M2-14 through
M2-18 are independent of this evidence and are all confirmed as worth fixing.

Phase 3 and Phase 4 must change on four points:

1. The module is renamed away from "hallucinates." The observed failure is incomplete
   evidence and a missing aggregation operator, not fabrication.
2. Pool counting becomes the core aggregation test. Orlando becomes the supporting
   example, described as a single-retrieval ceiling that an agent can sometimes work
   around.
3. The pool test prints 175 beside 168 and explains the difference. The graph's answer
   is what was extracted, not what the corpus says.
4. Chicago is presented as a mechanism contrast, not as a vector-arm failure.
