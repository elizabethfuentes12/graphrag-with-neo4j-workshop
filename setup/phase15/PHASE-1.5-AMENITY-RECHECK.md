# Phase 1.5 amenity recheck

**Status: Complete**

The accepted 300-document graph was checked live on 2026-08-23. The release
smoke uses one trial in every configured evaluation cell. It demonstrates that
all configured question, retrieval, and prompt paths execute and produce a
scored result without tool errors. It is not a statistical benchmark.

## Live graph facts

The live graph queries agree with the deterministic source facts captured in
the same evidence file.

| Reference fact | Live graph result |
|---|---:|
| Hotels | 300 |
| Sources whose amenity list includes a pool | 175 |
| Orlando hotels | 5 |
| Orlando mean guest rating | 4.62 |
| Chicago hotels | 2 |
| Chicago hotels with both spa and pool | 1 |
| Hotels with a suite under $600 and a spa | 78 |
| Antarctica hotels | 0 |

The two Chicago hotels share `24-Hour Fitness Center`, `Complimentary
High-Speed Wifi`, and `On-Site Restaurant`. The source projection also records
300 documents, 1,632 amenity assertions, and 65 distinct amenity names. These
are the corrected values for the accepted graph and corpus.

The earlier Phase 1.5 reports remain historical evidence from the defective
292-Hotel graph. Their reported graph value of 168 pool-bearing Hotels must not
be rewritten or cited as the corrected result.

## Release smoke decision

**Status: Complete**

- [x] Exercise six questions across the vector and graph retrieval arms.
- [x] Exercise both the notebook and grounded prompt conditions.
- [x] Run one trial in each of the 24 resulting cells.
- [x] Require every trial to be scored and free of tool errors.
- [x] Preserve the merged evidence and stage logs.

The evidence gate passed with 24 trials in 24 cells, one trial per cell, no
tool errors, and no unscored results. The observed judge-label distributions
are counts from this single release smoke:

| Retrieval arm | Factuality labels | Grounding labels |
|---|---|---|
| Graph, 12 observations | 12 correct | 10 grounded; 2 unsupported correct |
| Vector, 12 observations | 6 correct; 5 partial; 1 incorrect | 8 grounded; 3 insufficient; 1 unsupported correct |
| Total, 24 observations | 18 correct; 5 partial; 1 incorrect | 18 grounded; 3 insufficient; 3 unsupported correct |

Each cell has only one observation, so these counts must not be presented as
success rates, stability estimates, or evidence of statistical significance.
A 10-trials-per-cell run would contain 240 trials and remains an optional
statistical benchmark. It is not required for the graph-artifact release.

## Evidence

- Live graph and source facts:
  `setup/release-evidence/live-20260823-final/phase15/graph-facts.json`
- Merged 24-cell smoke results:
  `setup/release-evidence/live-20260823-final/phase15/trials/phase15-merged.json`
- Release-smoke validation log:
  `setup/release-evidence/live-20260823-final/logs/agent_evidence_gate.log`
- Per-worker execution logs:
  `setup/release-evidence/live-20260823-final/logs/agent_evidence_worker_01.log`,
  `agent_evidence_worker_02.log`, and `agent_evidence_worker_03.log`
- Live-evidence stage manifest:
  `setup/release-evidence/live-20260823-final/release-evidence.json`

## Phase 1.5 completion

**Status: Complete**

- [x] Capture and reconcile the corrected live graph facts.
- [x] Complete the approved one-trial-per-cell release smoke.
- [x] Repair and rerun the notebook live smoke as a separate release stage.
- [x] Record the final notebook result after the rerun completes.
- [x] Defer the optional 240-trial statistical benchmark unless comparative
  stability or rate claims are later required.

The combined evidence bundle records Modules 1 and 2 as passing. Its Module 3
attempt exposed a negation-sensitive assertion even though the generated answer
correctly abstained from claiming live availability. The finalized assertion
accepts active and passive abstention wording while still rejecting an explicit
affirmative availability claim. Module 3 then passed all nine cells in a clean
rerun recorded at
`setup/release-evidence/module3-abstention-fix-20260823-final/summary.json`.
The original combined manifest remains failed as historical evidence of the
test defect; the successful rerun is the release result for Module 3.
