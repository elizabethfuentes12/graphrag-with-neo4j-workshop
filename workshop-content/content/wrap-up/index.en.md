---
title: "Wrap-up"
weight: 90
---

# Workshop Wrap-up

**Congratulations on completing the GraphRAG workshop.**

## What You Accomplished

### Module 1: Built the Graph
- Extracted the **held-out hotel documents** into :link[Neo4j]{href="https://neo4j.com/" external=true}
- **Pinned the schema** so extraction produced predictable node labels and relationships
- Verified the **uniqueness constraints** that keep entities de-duplicated
- Created **both retrieval indexes** (vector and full-text) that every later module queries

### Module 2: Witnessed the Problem
- Saw pure vector RAG **hallucinate** on relational queries
- Understood **why** semantic similarity fails for multi-hop reasoning
- Measured the gap between vector retrieval and ground truth

### Module 3: Implemented Solutions
- **Four retrievers** on one graph, and the decision table for choosing between them
- **Hybrid retrieval** - a vector arm and a full-text arm fused, then a reviewed traversal
- **A grounded booking agent** that abstains when the graph is silent, and writes only inside a transaction that has already checked the rules

### Modules 4 and 5: Built Production Infrastructure
- **AgentCore Gateway** - Lambda retrieval tools exposed as a managed MCP endpoint
- **IAM SigV4 authentication** - signed tool calls with no API keys to manage
- **AgentCore Memory** - cross-session fact and preference recall
- **AgentCore Runtime** - the agent containerized, launched on Runtime, and one request correlated end to end

### Module 6: Made Memory Inspectable
- Stored preferences as **graph nodes** instead of opaque managed records
- Kept **full provenance** - every `Preference` links back to its source `Message` and to the real `Hotel` node
- Corrected a wrong preference with a single `SET`, no delete and re-extract
- Weighed **Neo4j memory against AgentCore Memory** on write timing, auditability, correction, and who operates it

---

## Key Concepts to Remember

1. **Vector similarity is not relational reasoning.** Similar text and connected facts are different things, and only one of them survives an aggregation.
2. **A graph gives structural precision.** A named field can be asserted on, queried, and handed to a write path. A sentence cannot.
3. **MCP keeps tool integration clean.** The agent code did not change when the tools moved behind a Gateway, and it did not change again when the agent moved onto Runtime.
4. **Graph memory gives long-term context you can audit.** Provenance is what turns a wrong preference from an outage into a one-line correction.

---

## Architecture You Built

```text
                    User Query
                         │
                         ▼
┌──────────────────────────────────────────────────┐
│                AgentCore Runtime                 │
│  ┌────────────────────────────────────────────┐  │
│  │               Strands Agent                │  │
│  │  us.anthropic.claude-sonnet-5 + Tool Use   │  │
│  └────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────┘
                         │ IAM-authenticated MCP (SigV4)
                         ▼
┌──────────────────────────────────────────────────┐
│                AgentCore Gateway                 │
│            managed MCP tool endpoint             │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────┐
│              Lambda Retrieval Tools              │
│     one function per graph retrieval pattern     │
└────────────────────────┬─────────────────────────┘
                         │ Cypher
                         ▼
               ┌────────────────────┐
               │       Neo4j        │
               │  Hotel Knowledge   │
               │       Graph        │
               └────────────────────┘
```

---

## Next Steps

### Start with your own data
1. **Adapt the schema** - swap the hotel entities for your own, and pin them the same way
2. **Re-run the extraction** - the pipeline in Module 1 does not care what the documents are about
3. **Find the questions that still break** - the four failure modes are a test suite, not a story

### Then tune what you built
1. **Tune retrieval quality** - adjust the hybrid `alpha` and the expansion Cypher against your own query logs
2. **Add guardrails** - validate generated Cypher, and keep it off the write path
3. **Set up monitoring** - the Runtime traces from Module 5 are the starting point

### Then operate it
1. **Deploy from your own pipeline** - the container the workshop built is the same one CI would build
2. **Close the feedback loop** - collect corrections and write them back as graph memory, with provenance
3. **Automate graph maintenance** - refresh, re-embed, and re-index on a schedule

---

## Resources

### Documentation
- [Amazon Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [Neo4j GraphRAG for Python](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Strands Agents](https://strandsagents.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

### Code Repositories
- [Neo4j MCP Server](https://github.com/neo4j-contrib/mcp-neo4j)
- [LangChain Neo4j Integration](https://python.langchain.com/docs/integrations/graphs/neo4j_cypher)

### Further Learning
- [AWS Workshop: Amazon Bedrock Agents](https://catalog.workshops.aws/amazon-bedrock-agents)
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/)

---

## Feedback

:::alert{type="info" header="Share your experience"}
What worked well? What would you change? Tell us, so the next room gets a better version of this.
:::

## Thank You

We hope you enjoyed learning about GraphRAG and how knowledge graphs keep an agent honest.

Happy building.
