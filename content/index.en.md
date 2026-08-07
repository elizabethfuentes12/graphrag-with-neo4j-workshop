---
title: "GraphRAG with Neo4j on AWS: Controlling Agent Hallucination"
weight: 0
---

## Stop Your Agent from Making Things Up

AI agents that answer from vector search will guess. An agent grounded in a knowledge graph answers only from what is actually connected — and says nothing when it is not.

This workshop uses a hotel booking scenario to show four hallucination failure modes, build the retrievers that prevent them, and wire a production agent with Amazon Bedrock AgentCore, a Neo4j MCP server, and inspectable graph memory.

:::alert{type="info" header="Region"}
This workshop runs in **us-east-1 (N. Virginia)**. Your AWS account and Neo4j database are pre-configured.
:::

---

## Workshop Flow

| Module | Duration | What You Will Build |
|--------|----------|---------------------|
| **Setup** | 10 min | Open Code Editor, verify Neo4j and Bedrock access |
| **Module 1: Vector RAG Hallucinates** | 25 min | Two agents, four hallucination failure modes, side-by-side comparison |
| **Module 2: GraphRAG Fixes It** | 35 min | Four retrieval patterns + grounded booking agent with safe reservations |
| **Module 3: Production Agent with AgentCore** | 35 min | AgentCore Gateway, IAM-authenticated MCP, cross-session memory |
| **Module 4: Inspectable Neo4j Memory** | 25 min | Graph-backed preferences, full provenance, AgentCore comparison |
| **Wrap-up and Cleanup** | 10 min | Review, next steps, resource cleanup |

**Total: ~2 hours**

---

## Architecture

:image[Production agent architecture: Code Editor connects to Neo4j on ECS Fargate and Amazon Bedrock, with AgentCore Gateway and Memory in Module 3]{src="/static/images/00-workshop-architecture.png" width=800}

```
┌─────────────────── Your Code Editor (EC2) ──────────────────────┐
│                                                                   │
│  Jupyter Notebook ──► Strands Agent ──► @tool / MCP client       │
│                              │                                    │
│          ┌───────────────────┼──────────────────────┐            │
│          │                   │                      │            │
│   ┌──────▼──────┐    ┌───────▼────────┐   ┌────────▼───────┐   │
│   │  Neo4j ECS  │    │ Amazon Bedrock │   │ Bedrock        │   │
│   │  Fargate    │    │ Claude Sonnet  │   │ AgentCore      │   │
│   │ Hotel graph │    │ Nova 2 Embeds  │   │ Gateway+Memory │   │
│   └─────────────┘    └────────────────┘   └────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

Neo4j owns\: hotel knowledge, retrieval indexes, business rules, reservation writes, and graph memory.
Amazon Bedrock owns\: reasoning over retrieved evidence, embeddings, and managed memory.

---

## What You Will Learn

1. Why vector RAG hallucinates on aggregation, counting, multi-hop, and out-of-domain queries
2. How to choose between Vector, Hybrid, VectorCypher, and Text2Cypher retrievers
3. How to build a grounded agent that abstains honestly and enforces rules atomically
4. How to deploy tools to AgentCore Gateway and connect agents over IAM-authenticated MCP
5. Why explicit graph memory gives you auditability that managed memory cannot

---

## Prerequisites

- Basic Python and AWS CLI familiarity
- No local setup required — everything runs in your Code Editor environment

:::alert{type="warning" header="Cost"}
This workshop creates AWS resources that incur charges. Follow the cleanup instructions at the end. Estimated cost for a 2-hour session\: under $2.
:::

::children{depth=2 variant=list}
