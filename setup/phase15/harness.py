# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Phase 1.5: measure the repaired FAISS baseline against the Neo4j graph.

This harness is deliberately independent of Module 2's notebook. The notebook
still carries the loading, truncation, model-pinning, agent-reuse, and
exception-swallowing defects catalogued in defects.md, and any one of them
would contaminate the measurement. Everything here uses the committed
manifest-validated FAISS artifact, the pinned workshop model, the shared AWS
and Neo4j helpers, and read-only database sessions.

Each trial gets a fresh agent, so token counts and tool histories never carry
across questions. Retrieval evidence is captured before the model speaks, which
makes the evidence the deterministic part of the record and the answer an
observation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase

SETUP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SETUP_DIR.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
MODULE_DIR = NOTEBOOKS_DIR / "02-connected-context"
for entry in (str(NOTEBOOKS_DIR), str(Path(__file__).resolve().parent)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from reference_facts import graph_facts, source_facts
from strands import Agent, tool
from strands.models import BedrockModel
from workshop.aws_region import configure_aws_region
from workshop.bedrock_providers import BEDROCK_CONFIG, default_model_id
from workshop.faiss_artifacts import (
    corpus_sha256,
    load_faiss_artifacts,
    prepare_faiss_query,
)
from workshop.graph_connection import (
    graph_database,
    neo4j_auth,
    neo4j_uri,
    require_neo4j_env,
)
from workshop.retrieval_contract import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_ID,
    EMBEDDING_PURPOSE,
)

TOP_K = 3

QUESTIONS: list[dict[str, str]] = [
    {
        "key": "orlando_aggregation",
        "label": "Orlando aggregation",
        "prompt": "What is the average guest rating of hotels in Orlando?",
    },
    {
        "key": "pool_counting",
        "label": "Pool counting",
        "prompt": "How many hotels in the database have a swimming pool?",
    },
    {
        "key": "chicago_criteria",
        "label": "Chicago multiple criteria",
        "prompt": "Which hotels in Chicago have both a spa and a swimming pool?",
    },
    {
        "key": "antarctica_no_match",
        "label": "Antarctica no match",
        "prompt": "Tell me about hotels in Antarctica.",
    },
    # The two questions below are the traversal arm of the design. Run 1 asked
    # only about aggregation, counting, a conjunction, and a no-match, so it
    # never posed a question a knowledge graph is supposed to win.
    #
    # This one is bounded on purpose. Both Chicago documents fit inside k=3, so
    # the vector arm has every fact it needs and the only thing being measured
    # is the set intersection itself, separated from corpus scale.
    {
        "key": "chicago_shared_amenities",
        "label": "Chicago shared amenities (bounded traversal)",
        "prompt": (
            "Which amenities do the hotels in Chicago all have in common with "
            "each other?"
        ),
    },
    # This one is unbounded, and it joins two relationship types rather than
    # filtering one. Answering it from top-k retrieval would require reading
    # most of the corpus.
    {
        "key": "suite_and_spa",
        "label": "Suite under $600 with a spa (traversal at scale)",
        "prompt": (
            "How many hotels offer a suite priced under $600 per night and "
            "also have a full-service spa?"
        ),
    },
]

# Both prompts are the notebook's own, verbatim. Run 1 gave the vector arm an
# extra "base your answer on what the search returns" sentence and the graph arm
# nothing, which is the exact intervention that turns fabrication into hedging.
# That single asymmetry could produce run 1's headline on its own.
NOTEBOOK_VECTOR_PROMPT = (
    "You are a travel agent. Use vector search to find relevant FAQ information."
)

NOTEBOOK_GRAPH_PROMPT = (
    "You are a travel agent. Use the knowledge base to answer questions "
    "accurately. You can run multiple queries."
)

# The grounding instruction is now a condition applied to both arms, so its
# effect is a measurement rather than a confound.
GROUNDING_SUFFIX = " Base your answer on what the tool returns."

CONDITIONS = ("notebook", "grounded")


def system_prompt(arm: str, condition: str) -> str:
    """Return one arm's prompt under one condition, symmetric across arms."""
    base = NOTEBOOK_VECTOR_PROMPT if arm == "vector" else NOTEBOOK_GRAPH_PROMPT
    return base + GROUNDING_SUFFIX if condition == "grounded" else base

GRAPH_TOOL_DOC = """Execute a read-only Cypher query against the hotel knowledge graph.

Node labels: Hotel, Room, Amenity, Policy, Service
Hotel properties: name, address, guest_rating, total_rooms, email, phone, hotel_id
Room properties: type, bed_configuration, max_occupancy, min_rate, max_rate
Amenity properties: name, description, fee
Policy properties: name, description
Service properties: name, description, is_available, is_complimentary, hours, cost

Relationships: (Hotel)-[:HAS_ROOM]->(Room), (Hotel)-[:OFFERS_AMENITY]->(Amenity),
               (Hotel)-[:HAS_POLICY]->(Policy), (Hotel)-[:PROVIDES_SERVICE]->(Service)

Location lives in Hotel.address. Use: WHERE toLower(h.address) CONTAINS 'chicago'
Property names are snake_case: guest_rating, not guestRating.
"""

JUDGE_SYSTEM_PROMPT = """You score one answer from a retrieval-augmented hotel agent.

Score factual correctness and grounding SEPARATELY. They are different failures.

factuality is one of:
  correct     every material claim agrees with the reference facts
  partial     the answer is directionally right but a material value is wrong or missing
  incorrect   a material claim conflicts with the reference facts

grounding is one of:
  grounded              every material claim follows from the evidence the tool returned
  insufficient          the model declines, qualifies, or states the evidence cannot
                        establish the requested corpus-wide result
  unsupported_correct   a claim is factually correct but the tool evidence does not
                        support it, so it came from the model's own knowledge
  fabricated            the answer asserts specific hotels, values, amenities, or counts
                        that the evidence does not contain and that are not correct

Return ONLY a JSON object, no prose and no code fence:
{"factuality": "...", "grounding": "...", "rationale": "one or two sentences"}
"""


@dataclass
class Retrieval:
    """One vector retrieval, captured before the model sees it."""

    query: str
    filenames: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)


@dataclass
class CypherCall:
    """One graph tool call, captured with the query the model wrote."""

    cypher: str
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def bedrock_client(region: str) -> Any:
    """Return the shared-config Bedrock runtime client used for embeddings."""
    return boto3.client("bedrock-runtime", region_name=region, config=BEDROCK_CONFIG)


def embed_query(client: Any, text: str) -> np.ndarray:
    """Embed one query on the contract the committed index was built with."""
    response = client.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        body=json.dumps(
            {
                "taskType": "SINGLE_EMBEDDING",
                "singleEmbeddingParams": {
                    "embeddingPurpose": EMBEDDING_PURPOSE,
                    "embeddingDimension": EMBEDDING_DIMENSIONS,
                    "text": {"truncationMode": "END", "value": text[:8000]},
                },
            }
        ),
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(response["body"].read())
    return prepare_faiss_query(payload["embeddings"][0]["embedding"])


def workshop_model(region: str, max_tokens: int | None = None) -> BedrockModel:
    """Return a fresh pinned model, so no trial inherits another's client."""
    extra = {"max_tokens": max_tokens} if max_tokens is not None else {}
    return BedrockModel(
        model_id=default_model_id(),
        region_name=region,
        boto_client_config=BEDROCK_CONFIG,
        **extra,
    )


# Run 1 removed the vector tool's 500-character slice, which is the M2-1 repair,
# but left the graph tool capped at 15 returned rows and 50 recorded ones. Seven
# Chicago calls returned 23 rows or more, so the graph agent and the judge both
# saw less than the vector side did. Rows are no longer capped. The budget below
# exists only to keep a runaway query from filling the context, and it says so in
# the text when it fires.
GRAPH_RESULT_BUDGET = 60_000


def render_records(records: list[dict[str, Any]]) -> str:
    """Render every row Neo4j returned, up to an explicit character budget."""
    if not records:
        return "No results found."
    lines = [f"Found {len(records)} results:"]
    used = 0
    for position, item in enumerate(records):
        line = f"  {item}"
        if used + len(line) > GRAPH_RESULT_BUDGET:
            lines.append(f"  ... {len(records) - position} more rows not shown")
            break
        lines.append(line)
        used += len(line)
    return "\n".join(lines)


def make_vector_agent(
    index: Any,
    documents: list[dict[str, Any]],
    client: Any,
    region: str,
    condition: str,
    record: list[Retrieval],
) -> Agent:
    """Build a fresh vector agent whose tool records evidence and never swallows."""

    @tool
    def search_faqs(query: str) -> str:
        """Search the hotel FAQ documents by vector similarity."""
        vector = embed_query(client, query)
        scores, indices = index.search(vector, TOP_K)
        retrieval = Retrieval(query=query)
        blocks = []
        for score, position in zip(scores[0], indices[0]):
            document = documents[int(position)]
            retrieval.filenames.append(document["filename"])
            retrieval.scores.append(float(score))
            retrieval.texts.append(document["text"])
            blocks.append(f"[{document['filename']}]\n{document['text']}")
        record.append(retrieval)
        return "\n\n".join(blocks)

    return Agent(
        name="VectorAgent",
        model=workshop_model(region),
        system_prompt=system_prompt("vector", condition),
        tools=[search_faqs],
    )


def make_graph_agent(
    driver: Any,
    database: str,
    region: str,
    condition: str,
    record: list[CypherCall],
) -> Agent:
    """Build a fresh graph agent whose tool records the Cypher the model wrote."""

    @tool
    def query_knowledge_graph(cypher_query: str) -> str:
        cypher = cypher_query
        call = CypherCall(cypher=cypher)
        record.append(call)
        try:
            with driver.session(database=database, default_access_mode="READ") as session:
                result = session.run(cypher, timeout=30)
                records = [dict(item) for item in result]
        except Exception as exc:  # recorded, then re-raised into the trial
            call.error = f"{type(exc).__name__}: {exc}"
            raise
        call.records = records
        return render_records(records)

    query_knowledge_graph.__doc__ = GRAPH_TOOL_DOC
    return Agent(
        name="GraphAgent",
        model=workshop_model(region),
        system_prompt=system_prompt("graph", condition),
        tools=[query_knowledge_graph],
    )


def usage_of(result: Any) -> dict[str, int] | None:
    """Return this agent's token usage. Fresh agents make it per-trial."""
    metrics = getattr(result, "metrics", None)
    if metrics is None:
        return None
    usage = getattr(metrics, "accumulated_usage", None)
    if not usage:
        return None
    return {key: int(value) for key, value in dict(usage).items() if isinstance(value, int)}


# One judge sample decided every label in run 1. Three samples with a majority
# vote costs three calls per answer and keeps a single stochastic grade from
# deciding the module's claim, which is the same reason the trials repeat.
JUDGE_SAMPLES = 3

# The agents see untruncated tool output, which is the point of removing the row
# caps. The grader is a different budget: a 78-row result set beside a long answer
# ran it out of output tokens. Both arms are trimmed by the same rule so the
# grader's view stays symmetric, and the trim announces itself.
JUDGE_EVIDENCE_BUDGET = 40_000


def trim_for_judge(evidence: str) -> str:
    """Bound the grader's copy of the evidence, identically for both arms."""
    if len(evidence) <= JUDGE_EVIDENCE_BUDGET:
        return evidence
    dropped = len(evidence) - JUDGE_EVIDENCE_BUDGET
    return (
        evidence[:JUDGE_EVIDENCE_BUDGET]
        + f"\n\n[{dropped} further characters of tool evidence not shown to the judge]"
    )


def judge_once(
    region: str, question: str, reference: Any, evidence: str, answer: str
) -> dict[str, str]:
    """Score one answer once, with a fresh pinned grader."""
    grader = Agent(
        name="Judge",
        model=workshop_model(region, max_tokens=8192),
        system_prompt=JUDGE_SYSTEM_PROMPT,
    )
    prompt = (
        f"QUESTION\n{question}\n\n"
        f"REFERENCE FACTS\n{json.dumps(reference, indent=2)}\n\n"
        f"TOOL EVIDENCE THE AGENT RECEIVED\n{trim_for_judge(evidence)}\n\n"
        f"AGENT ANSWER\n{answer}\n"
    )
    raw = str(grader(prompt)).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1]).strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"factuality": "unscored", "grounding": "unscored", "rationale": raw[:400]}
    return {
        "factuality": str(parsed.get("factuality", "unscored")),
        "grounding": str(parsed.get("grounding", "unscored")),
        "rationale": str(parsed.get("rationale", ""))[:600],
    }


def judge(
    region: str, question: str, reference: Any, evidence: str, answer: str
) -> dict[str, Any]:
    """Score one answer by majority vote over independent grader samples."""
    samples = [
        judge_once(region, question, reference, evidence, answer)
        for _ in range(JUDGE_SAMPLES)
    ]
    # Counter breaks a three-way split on first-seen order, so an unresolved
    # vote falls back to the first sample rather than to an arbitrary label.
    factuality = Counter(sample["factuality"] for sample in samples).most_common(1)
    grounding = Counter(sample["grounding"] for sample in samples).most_common(1)
    return {
        "factuality": factuality[0][0],
        "grounding": grounding[0][0],
        "factuality_votes": factuality[0][1],
        "grounding_votes": grounding[0][1],
        "rationale": samples[0]["rationale"],
        "judge_samples": samples,
    }


def vector_evidence_text(retrievals: list[Retrieval]) -> str:
    """Render the retrieved set the way the agent received it."""
    if not retrievals:
        return "(the agent made no retrieval call)"
    blocks = []
    for retrieval in retrievals:
        header = "\n".join(
            f"  {name}  score={score:.4f}"
            for name, score in zip(retrieval.filenames, retrieval.scores)
        )
        body = "\n\n".join(retrieval.texts)
        blocks.append(f"search_faqs({retrieval.query!r}) returned:\n{header}\n\n{body}")
    return "\n\n".join(blocks)


def graph_evidence_text(calls: list[CypherCall]) -> str:
    """Render the Cypher the model wrote and the rows Neo4j returned."""
    if not calls:
        return "(the agent made no graph call)"
    blocks = []
    for call in calls:
        detail = call.error if call.error else json.dumps(call.records, default=str)
        blocks.append(f"cypher:\n{call.cypher}\nresult:\n{detail}")
    return "\n\n".join(blocks)


def run_trial(
    arm: str,
    question: dict[str, str],
    condition: str,
    trial: int,
    build_agent: Any,
    reference: Any,
    region: str,
    skip_judge: bool,
) -> dict[str, Any]:
    """Run one fresh-agent trial and return its complete evidence record."""
    record: list[Any] = []
    agent = build_agent(record)
    started = datetime.now(timezone.utc)
    error = None
    answer = ""
    usage = None
    try:
        result = agent(question["prompt"])
        answer = str(result).strip()
        usage = usage_of(result)
    # A trial records its own failure rather than aborting the run: one throttled
    # or refused call must not cost the other 23 trials. The tool itself does not
    # swallow anything, which is what M2-1 is about, so whatever lands here is a
    # genuine failure and is reported as one.
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()

    if arm == "vector":
        evidence = vector_evidence_text(record)
        retrieval = [asdict(item) for item in record]
    else:
        evidence = graph_evidence_text(record)
        retrieval = [asdict(item) for item in record]

    scores: dict[str, Any] = {
        "factuality": "unscored",
        "grounding": "unscored",
        "rationale": "",
    }
    if answer and not skip_judge:
        # Same reasoning as the trial-level catch above, and it is here because
        # removing the graph row cap made this reachable: an uncapped result set
        # can push the grader into MaxTokensReachedException, which used to
        # escape run_trial and abort the whole slice.
        try:
            scores = judge(region, question["prompt"], reference, evidence, answer)
        except Exception as exc:  # noqa: BLE001
            scores["rationale"] = f"judge failed: {type(exc).__name__}: {exc}"

    print(
        f"  [{arm}/{condition}] {question['key']} trial {trial}: "
        f"{'ERROR ' + error if error else scores['factuality'] + '/' + scores['grounding']}"
        f"  ({elapsed:.1f}s)",
        flush=True,
    )
    return {
        "arm": arm,
        "condition": condition,
        "system_prompt": system_prompt(arm, condition),
        "question_key": question["key"],
        "question": question["prompt"],
        "trial": trial,
        "started_utc": started.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "tool_calls": len(record),
        "tool_error": error,
        "retrieval": retrieval,
        "answer": answer,
        "token_usage": usage,
        **scores,
    }


def parse_args() -> argparse.Namespace:
    """Parse trial count and output location."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "evidence")
    parser.add_argument("--questions", nargs="*", default=None)
    parser.add_argument("--arms", nargs="*", default=["vector", "graph"])
    parser.add_argument("--conditions", nargs="*", default=list(CONDITIONS))
    parser.add_argument("--skip-judge", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the comparison and write the evidence file."""
    args = parse_args()
    load_dotenv(REPO_ROOT / ".env")
    region = configure_aws_region()
    require_neo4j_env()

    index, documents = load_faiss_artifacts(
        MODULE_DIR / "faqs_vector.index",
        MODULE_DIR / "faqs_docs.json",
        MODULE_DIR / "faqs_vector.manifest.json",
    )
    manifest = json.loads((MODULE_DIR / "faqs_vector.manifest.json").read_text())
    source = source_facts(documents)

    database = graph_database()
    driver = GraphDatabase.driver(neo4j_uri(), auth=neo4j_auth())
    with driver.session(database=database, default_access_mode="READ") as session:
        graph = graph_facts(session)

    client = bedrock_client(region)
    questions = [q for q in QUESTIONS if not args.questions or q["key"] in args.questions]
    # Source facts only. Run 1 handed the judge the graph aggregate alongside
    # the source fact, and the judge settled on the graph value every time,
    # including when grading the vector arm: its rationales read "the true count
    # is 168 hotels with pools" where the corpus says 175. That graded the graph
    # against itself and penalised the other arm for missing a number the corpus
    # does not contain. The extraction gap is reported separately, from
    # `graph_facts` in the run header, and is never the reference answer.
    reference_by_key = {
        "orlando_aggregation": source["orlando"],
        "pool_counting": source["pool"],
        "chicago_criteria": source["chicago"],
        "antarctica_no_match": source["antarctica"],
        "chicago_shared_amenities": source["chicago_shared_amenities"],
        "suite_and_spa": source["suite_and_spa"],
    }

    run = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": default_model_id(),
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "region": region,
        "top_k": TOP_K,
        "trials_per_cell": args.trials,
        "conditions": list(args.conditions),
        "judge_samples": JUDGE_SAMPLES,
        "run_generation": 2,
        "neo4j_uri": neo4j_uri(),
        "neo4j_database": database,
        "faiss_manifest": manifest,
        "corpus_sha256_now": corpus_sha256(MODULE_DIR / "faqs_docs.json"),
        "index_dimensions": int(index.d),
        "index_vectors": int(index.ntotal),
        "source_facts": source,
        "graph_facts": graph,
        "trials": [],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = run["run_utc"].replace(":", "").replace("-", "").split(".")[0]
    path = args.out / f"phase15-{stamp}Z.json"

    def flush() -> None:
        """Persist after every trial, so a killed run keeps what it paid for."""
        path.write_text(json.dumps(run, indent=2, default=str) + "\n", encoding="utf-8")

    flush()
    print(
        f"Model {run['model_id']} in {region}; {len(questions)} questions, "
        f"{args.trials} trials, arms {args.arms}, conditions {args.conditions}.",
        flush=True,
    )
    for question in questions:
        reference = reference_by_key[question["key"]]
        for condition in args.conditions:
            for trial in range(1, args.trials + 1):
                if "vector" in args.arms:
                    run["trials"].append(
                        run_trial(
                            "vector", question, condition, trial,
                            lambda record, condition=condition: make_vector_agent(
                                index, documents, client, region, condition, record
                            ),
                            reference, region, args.skip_judge,
                        )
                    )
                    flush()
                if "graph" in args.arms:
                    run["trials"].append(
                        run_trial(
                            "graph", question, condition, trial,
                            lambda record, condition=condition: make_graph_agent(
                                driver, database, region, condition, record
                            ),
                            reference, region, args.skip_judge,
                        )
                    )
                    flush()
    driver.close()

    flush()
    print(f"\nWrote {len(run['trials'])} trials to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
