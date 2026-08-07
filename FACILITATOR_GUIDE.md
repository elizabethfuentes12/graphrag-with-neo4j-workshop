# Facilitator Guide — Grounded AI Agents with Neo4j and AWS

**Visible to Workshop Studio authenticated users only.**

---

## Workshop Overview

| Detail | Value |
|--------|-------|
| Duration | 95 minutes (all three modules) |
| Core path | 01 → 02 → 03 |
| Audience | Developers and architects evaluating Graph-RAG and knowledge graph-backed agents |
| AWS services | Amazon Bedrock (Claude Sonnet, Amazon Nova 2 Embeddings) |
| External service | Neo4j Aura (free tier) — participants create their own instance before the event |

---

## Pre-Event Checklist

- [ ] Verify Amazon Bedrock model access is enabled in `us-east-1`\: `us.anthropic.claude-sonnet-4-6` and `amazon.nova-2-multimodal-embeddings-v1\:0`
- [ ] Confirm Workshop Studio CloudFormation deploys without errors (test event)
- [ ] Send participants the "before you attend" instructions at least 48 hours early\:
  - Create a Neo4j Aura free-tier instance
  - Save the credentials file
  - Have Python 3.9+ and `uv` installed on their laptop
- [ ] Verify the hotel FAQ dataset (`hotel-faqs.zip`) is accessible from the S3 assets bucket
- [ ] Run Module 01 (lite version) end-to-end in the workshop environment — confirm Neo4j graph builds

---

## Module Timings

| Module | Minimum | Full |
|--------|---------|------|
| Setup (Step 0) | 10 min | 15 min |
| Module 01 — Graph-RAG vs. RAG | 25 min | 35 min |
| Module 02 — Retrieval Patterns | 20 min | 30 min |
| Module 03 — Grounded Agent | 35 min | 45 min |
| Cleanup | 5 min | 10 min |
| **Total** | **95 min** | **135 min** |

For a 2-hour session, use the minimum timings and skip Module 02 (have participants run it self-paced).

---

## Common Issues and Resolutions

### Neo4j Aura connection refused

Most common cause\: the Aura free instance paused after inactivity. Ask the participant to open the [Aura console](https://console.neo4j.io/), click **Resume**, wait 60 seconds, and retry.

### Graph build slower than expected (Module 01)

The lite version (30 documents) takes 10–15 minutes. The full version (300 documents) takes ~2 hours — do not run the full version in a workshop session. Confirm participants are running `build_graph_lite.py`, not `build_graph.py`.

### Amazon Bedrock throttling

Nova 2 Embeddings has a default quota. If participants hit throttling errors during the graph build, space out the `build_graph_lite.py` runs across the room. The lite version makes ~30 embedding calls.

### Module 03 fixtures not found

The `graph_setup.py` file looks for `fixtures/hotel_ids.json`. Confirm the file exists at `notebooks/fixtures/hotel_ids.json`. If missing, the participant needs to pull the latest from the repository.

### `strands` import error

Ensure participants ran `uv pip install -r requirements.txt` inside the `notebooks/` directory, not the repo root.

---

## Key Teaching Points

### Module 01

Pause after Test 1 (aggregation) and Test 4 (out-of-domain) — these are the highest-impact demonstrations. Ask participants\: "What did RAG return? What did Graph-RAG return? Which answer would you trust in production?"

### Module 02

The postal code demonstration (Pattern 2\: HybridRetriever) is the most surprising moment for most audiences. Have participants note where the exact code appears in vector-only results (usually rank 10–15), then show it jumping to rank 1 with `alpha=0.2`.

### Module 03

The rule rejection (Section 4) is the clearest demonstration of the workshop's core point\: business rules in a graph transaction cannot be bypassed by prompt manipulation. After the rejection, ask\: "What would have happened if this rule was only in the system prompt?"

The idempotent write (Section 5) is easy to skip but important for architects. The `duplicate\: true` return on replay is exactly how distributed reservation systems must behave.

---

## Modular Delivery Options

| Format | Modules | Notes |
|--------|---------|-------|
| Full workshop (95 min) | 01 + 02 + 03 | All three modules in sequence |
| Short session (60 min) | 01 + 03 | Skip Module 02; participants run it self-paced |
| Demo only (30 min) | 01 (Tests 1 and 4 only) | Facilitator runs notebook, participants observe |
| Deep-dive (2 hours) | 01 + 02 + 03 + discussion | Add Q&A after each module |

---

## Architecture Discussion Points

Use these questions to drive discussion after Module 03\:

1. **Who owns what?** "Which layer enforces the 10-guest rule — the LLM, the application, or the graph? Why does that matter?"

2. **Prompt vs. grounding\:** "If you moved the 10-guest rule to the system prompt, when would it fail? (Answer\: a jailbreak, a model update, a prompt injection, or a long conversation that causes the model to forget the instruction.)"

3. **Idempotency\:** "Why does the reservation command use `MERGE` on `request_id` instead of `CREATE`? What happens in a distributed system without this pattern?"

4. **Abstention\:** "The agent abstained from answering the availability question. In your system, what questions should your agent refuse to answer? How do you enforce that boundary?"

---

## Cleanup Reminder

Remind participants at the end\:
- Run the Cypher cleanup cells in the notebook (or the `04_cleanup.ipynb` notebook)
- Amazon Bedrock charges are pay-per-use — stopping use stops charges
- Neo4j Aura free-tier instances do not incur charges
