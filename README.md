# Grounded AI Agents with Neo4j and AWS

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg?style=flat&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph--RAG-4581C3.svg?style=flat&logo=neo4j)](https://neo4j.com)
[![Strands Agents](https://img.shields.io/badge/Strands_Agents-1.27+-00B4D8.svg?style=flat)](https://strandsagents.com)
[![Workshop Studio](https://img.shields.io/badge/AWS-Workshop_Studio-FF9900.svg?style=flat&logo=amazon-aws)](https://workshops.aws)

> AI agents that answer from memory hallucinate. Agents grounded in a knowledge graph answer only from what is actually there — and say nothing when it is not.

An AWS Workshop Studio workshop in six modules, teaching five skills: why vector RAG hallucinates on aggregation, counting, multi-hop, and out-of-domain queries; how to choose between the Vector, Hybrid, VectorCypher, and Text2Cypher retrievers; how to build a grounded agent that abstains honestly and enforces its rules atomically; how to deploy tools to Amazon Bedrock AgentCore Gateway and run the agent on AgentCore Runtime over IAM-authenticated MCP; and why explicit graph memory gives you auditability that managed memory cannot.

---

## Modules

| Module | Notebooks | What You Build |
|--------|-----------|----------------|
| [01 — Build the Graph](./workshop-content/content/01-build-graph/) | `1.1_build_graph.ipynb` | Live extraction of five held-out hotel documents, pinned schema, both retrieval indexes |
| [02 — Vector RAG Hallucinates](./workshop-content/content/02-vector-rag-hallucinates/) | `2.1_vector_rag_hallucinates.ipynb` | Two agents, four hallucination tests, token comparison |
| [03 — Retrieval Patterns and the Grounded Booking Agent](./workshop-content/content/03-retrieval-patterns/) | `3.1_retrieval_patterns.ipynb` + `3.2_grounded_booking_agent.ipynb` | Four retrievers, decision table, grounded booking agent |
| [04 — Production Agent with AgentCore](./workshop-content/content/04-production-agent/) | `4.1_agentcore_gateway.ipynb` + `4.2_agentcore_memory.ipynb` | Gateway Lambda tools, IAM-authenticated MCP, cross-session memory |
| [05 — Deploy to AgentCore Runtime](./workshop-content/content/05-agentcore-deploy/) | `5.1_deploy.ipynb` | Containerized agent on AgentCore Runtime, one request correlated end to end |
| [06 — Inspectable Neo4j Memory](./workshop-content/content/06-neo4j-memory/) | `6.1_neo4j_memory.ipynb` | Graph-backed preference storage with full provenance tracing |

Each module folder under `notebooks/` carries its own `README.md`: an At a Glance summary, what the module proves, and what every file in the folder is for.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Code Editor (browser)                        │
│                                                                 │
│  Jupyter Notebook ──► Strands Agent ──► @tool                  │
│                              │                                  │
│                    ┌─────────┴──────────┐                       │
│                    │                    │                       │
│             ┌──────▼──────┐    ┌────────▼────────┐             │
│             │ Neo4j (ECS) │    │ Amazon Bedrock  │             │
│             │             │    │                 │             │
│             │ • Hotel KG  │    │ • Claude Sonnet │             │
│             │ • Indexes   │    │ • Nova 2 Embed  │             │
│             │ • Rules     │    │                 │             │
│             │ • Writes    │    │                 │             │
│             └─────────────┘    └─────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

Neo4j owns: connected hotel knowledge, retrieval indexes, business rules, and reservation writes.
Amazon Bedrock owns: reasoning over retrieved evidence and query embedding.

---

## Getting Started

This is a hosted workshop. Almost everyone runs it the first way.

### At an AWS event

Everything is provisioned before you arrive: an AWS account with Amazon Bedrock model access enabled in `us-east-1`, a Neo4j instance on ECS Fargate with the hotel graph already restored from a dump, and a browser-based Code Editor with this repository cloned at `/Workshop`. There is nothing to install locally, no Neo4j account to create, and no model access to request.

1. Open the **CodeEditorURL** from the Workshop Studio **Outputs** panel and sign in with **CodeEditorUser**.
2. In the Code Editor terminal, export `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, and `AWS_REGION` from the same Outputs panel, and write them to `notebooks/.env`.
3. Install dependencies: `cd /Workshop/notebooks && uv venv && uv pip install -r requirements.txt`
4. Open `notebooks/01-build-graph/1.1_build_graph.ipynb` and work forward through the modules in order.

The [Setup](./workshop-content/content/setup/) pages carry the exact commands and a verification snippet that checks both Neo4j and Bedrock before Module 1 starts. Run that check first; every failure it catches is cheaper here than three modules in.

### Self-paced, in your own AWS account

You supply what the event would otherwise have provisioned. See [Own Account Setup](./workshop-content/content/setup/own-account-setup/) for the full path, including the CloudFormation stack that stands up Neo4j and the Code Editor.

To run the notebooks against a Neo4j instance you already have:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Neo4j connection details and AWS region

# 2. Install dependencies
cd notebooks
uv venv && uv pip install -r requirements.txt

# 3. Build the graph the hosted environment restores from a dump
uv run python 02-vector-rag-hallucinates/prepare_graph.py

# 4. Run the modules in order
uv run jupyter lab
# Open 01-build-graph/1.1_build_graph.ipynb first
```

Prerequisites for this path are Python 3.9+, [`uv`](https://docs.astral.sh/uv/), an AWS account with Amazon Bedrock model access enabled in `us-east-1`, and a reachable Neo4j instance. A [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/) free-tier database is enough.

`prepare_graph.py` wipes and rebuilds. Module 1's notebook uses the additive path instead, so it extends a restored graph without deleting anything a participant has already built.

---

## Workshop Content

This repository is deployed as an [AWS Workshop Studio](https://workshops.aws) workshop. The `workshop-content/content/` directory contains the workshop pages. Participants run the notebooks in `notebooks/` during the session.

| Directory | Purpose |
|-----------|---------|
| `workshop-content/content/` | Workshop Studio markdown pages |
| `workshop-content/images/` | Diagram images referenced by the workshop pages |
| `notebooks/` | Jupyter notebooks (one or two per module) |
| `static/` | Architecture diagrams (PNG exports and drawio sources) |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING](CONTRIBUTING.md) for more information.

---

## Security

If you discover a potential security issue in this project, notify AWS/Amazon Security via the [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public GitHub issue.

---

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.
