# Phase 1.5 evidence retention policy

**Status:** Historical evaluation, facilitator-only.

The active learner path uses Neo4j retrieval and does not use FAISS. The
committed FAISS corpus, index, manifest, loader, rebuild utility, harness, and
tests remain supported as an optional facilitator evaluation baseline.

## Tracked compact evidence

The repository retains these compact decision records:

- `README.md`, this ownership and retention policy;
- `PHASE-1.5-FINDINGS.md`, the retracted initial interpretation and the
  deterministic observations that motivated the curriculum rename;
- `PHASE-1.5-AMENITY-RECHECK.md`, the corrected source and graph facts from the
  accepted graph.

Every retained report marks historical grounding labels invalid. No grounding
rate from the earlier runs is eligible for publication. The earlier evaluator
truncated judge evidence, accepted loose JSON, resolved ties by sample order,
selected an unrelated first-sample rationale, and overstated trials per cell.

## Local-only artifacts

The following workspace artifacts are intentionally excluded from Git:

- generated detailed Phase 1.5 Markdown reports;
- raw and merged trial JSON;
- command logs and live-run manifests;
- executed notebooks;
- the archived `2.1_vector_rag_hallucinates.ipynb` notebook;
- release-smoke and Module 3 rerun bundles under `evidence/release-evidence/`.

These files have no recorded durable external URI. They are local diagnostic
material, not release evidence, and another clone is not expected to contain
them. A future publication must copy its raw bundle to approved durable storage
and record the immutable URI and checksum in a tracked compact report.

## Publication gate

The optional benchmark uses ten trials in each question, arm, and prompt
condition cell. It remains outside the learner workflow and must run only after
the offline evaluator tests pass. A publishable run must satisfy all of these
conditions:

- the judge received the complete evidence shown to the evaluated agent;
- every judge response matched the exact JSON fields and allowed labels;
- every vote produced a unique winning label;
- the evidence gate accepted every trial with no tool or judge errors;
- raw counts and rates are reported separately from statistical claims;
- repeated observations are analyzed by question and evaluation cell;
- the raw bundle has an immutable durable URI and checksum.

Until those conditions hold, cite only the deterministic source and graph facts
in the tracked compact reports.
