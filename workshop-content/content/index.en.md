---
title: "GraphRAG with Neo4j on AWS: Controlling Agent Hallucination"
weight: 0
---

## Stop Your Agent from Making Things Up

AI agents that answer from vector search will guess. An agent grounded in a knowledge graph answers only from what is actually connected — and says nothing when it is not.

This workshop uses a hotel booking scenario to show four hallucination failure modes, build the retrievers that prevent them, and wire a production agent with :link[Amazon Bedrock AgentCore]{href="https://aws.amazon.com/bedrock/agentcore/" external=true}, :link[Neo4j]{href="https://neo4j.com/" external=true} retrieval tools, and inspectable graph memory.

:::alert{type="info" header="Region"}
This workshop runs in **us-east-1 (N. Virginia)**. Your AWS account and Neo4j database are pre-configured.
:::

---

## Workshop Flow

| Module | What You Will Build |
|--------|---------------------|
| **Setup** | Open Code Editor, verify Neo4j and :link[Amazon Bedrock]{href="https://aws.amazon.com/bedrock/" external=true} access |
| **Module 1: Build the Graph** | Extract five held-out hotel documents into the graph, pin the extraction schema, create both retrieval indexes |
| **Module 2: Vector RAG Hallucinates** | Two agents, four hallucination failure modes, side-by-side comparison |
| **Module 3: Retrieval Patterns and the Grounded Booking Agent** | Four retrieval patterns, plus a grounded booking agent that abstains and writes safely |
| **Module 4: Production Agent with AgentCore** | AgentCore Gateway, IAM-authenticated MCP, cross-session memory |
| **Module 5: Deploy to AgentCore Runtime** | Containerize the agent, launch it on Runtime, correlate one request end to end |
| **Module 6: Inspectable Neo4j Memory** | Graph-backed preferences, full provenance, AgentCore comparison |
| **Wrap-up and Cleanup** | Review, next steps, resource cleanup |

---

## Architecture

:image[Production agent architecture: Strands Agent in AgentCore Runtime calls Lambda tools via AgentCore Gateway, stores memory in AgentCore Memory, and queries Neo4j on ECS Fargate]{src="../images/03-agentcore-architecture.png" width=800}

**Neo4j owns:** hotel knowledge, retrieval indexes, business rules, reservation writes, and graph memory.
**Amazon Bedrock owns:** reasoning over retrieved evidence, embeddings, and managed memory.

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
This workshop creates AWS resources that incur charges. Follow the cleanup instructions at the end. Estimated cost\: under $2.
:::

::children{depth=2 variant=list}
