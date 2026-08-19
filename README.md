# Grounded AI Agents with Neo4j and AWS

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg?style=flat&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph--RAG-4581C3.svg?style=flat&logo=neo4j)](https://neo4j.com)
[![Strands Agents](https://img.shields.io/badge/Strands_Agents-1.27+-00B4D8.svg?style=flat)](https://strandsagents.com)
[![Workshop Studio](https://img.shields.io/badge/AWS-Workshop_Studio-FF9900.svg?style=flat&logo=amazon-aws)](https://workshops.aws)

> AI agents that answer from memory hallucinate. Agents grounded in a knowledge graph answer only from what is actually there — and say nothing when it is not.

An AWS Workshop Studio workshop teaching four progressive skills: detecting RAG hallucinations with Graph-RAG, choosing the right Neo4j retrieval strategy, deploying production-grade tools and memory with Amazon Bedrock AgentCore, and comparing AgentCore Memory against inspectable Neo4j graph memory.

---

## Modules

| Module | Notebooks | What You Build |
|--------|-----------|----------------|
| 01 — Build the Graph *(page and notebook not yet written)* | `1.1_build_graph.ipynb` | Live extraction of five held-out hotel documents, pinned schema, constraints, both retrieval indexes |
| [02 — Vector RAG Hallucinates](./workshop-content/content/02-vector-rag-hallucinates/) | `2.1_vector_rag_hallucinates.ipynb` | Two agents, four hallucination tests, token comparison |
| [03 — Retrieval Patterns and the Grounded Booking Agent](./workshop-content/content/03-retrieval-patterns/) | `3.1_retrieval_patterns.ipynb` + `3.2_grounded_booking_agent.ipynb` | Four retrievers, decision table, grounded booking agent |
| [04 — Production Agent with AgentCore](./workshop-content/content/04-production-agent/) | `4.1_agentcore_gateway.ipynb` + `4.2_agentcore_memory.ipynb` | Gateway Lambda tools, IAM-authenticated MCP, cross-session memory |
| 05 — Deploy to AgentCore Runtime *(page and notebook not yet written)* | `5.1_deploy.ipynb` | Containerized agent on AgentCore Runtime, one request correlated end to end |
| [06 — Inspectable Neo4j Memory](./workshop-content/content/06-neo4j-memory/) | `6.1_neo4j_memory.ipynb` | Graph-backed preference storage with full provenance tracing |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Participant laptop                           │
│                                                                 │
│  Jupyter Notebook ──► Strands Agent ──► @tool                  │
│                              │                                  │
│                    ┌─────────┴──────────┐                       │
│                    │                    │                       │
│             ┌──────▼──────┐    ┌────────▼────────┐             │
│             │ Neo4j Aura  │    │ Amazon Bedrock  │             │
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

## Quick Start

### Prerequisites

- Python 3.9+, [`uv`](https://docs.astral.sh/uv/) package manager
- AWS account with Amazon Bedrock access enabled in `us-east-1`
- Neo4j Aura free-tier instance — [create one here](https://neo4j.com/cloud/platform/aura-graph-database/)

### Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Neo4j Aura credentials and AWS region

# 2. Install dependencies
cd notebooks
uv venv && uv pip install -r requirements.txt

# 3. Run modules in order
uv run jupyter lab
# Open 02-vector-rag-hallucinates/2.1_vector_rag_hallucinates.ipynb and follow the instructions
```

---

## Workshop Content

This repository is deployed as an [AWS Workshop Studio](https://workshops.aws) workshop. The `workshop-content/content/` directory contains the workshop pages. Participants run the notebooks in `notebooks/` during the session.

| Directory | Purpose |
|-----------|---------|
| `workshop-content/content/` | Workshop Studio markdown pages |
| `notebooks/` | Jupyter notebooks (one per module) |
| `static/` | Architecture diagrams and IAM policies |
| `contentspec.yaml` | Workshop Studio configuration |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING](CONTRIBUTING.md) for more information.

---

## Security

If you discover a potential security issue in this project, notify AWS/Amazon Security via the [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public GitHub issue.

---

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.
