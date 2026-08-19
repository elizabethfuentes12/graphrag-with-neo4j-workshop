---
title: "Wrap-up"
weight: 90
---

# Workshop Wrap-up

**Congratulations on completing the GraphRAG workshop!**

## What You Accomplished

You:

### Module 1: Built the Graph
- Extracted the **held-out hotel documents** into :link[Neo4j]{href="https://neo4j.com/" external=true}
- **Pinned the schema** so extraction produced predictable node labels and relationships
- Created the **uniqueness constraints** that keep entities de-duplicated
- Created **both retrieval indexes** (vector and full-text) that every later module queries

### Module 2: Witnessed the Problem
- Saw pure vector RAG **hallucinate** on relational queries
- Understood **why** semantic similarity fails for multi-hop reasoning
- Measured the gap between vector retrieval and ground truth

### Module 3: Implemented Solutions
- **Hybrid Retrieval** - Vector entry points + graph expansion
- **Template Cypher** - LLM-parameterized query patterns
- **Text2Cypher** - Full natural language to graph query generation

### Modules 4 and 5: Built Production Infrastructure
- **AgentCore Gateway** - Lambda retrieval tools exposed as a managed MCP endpoint
- **IAM SigV4 authentication** - Signed tool calls with no API keys to manage
- **AgentCore Memory** - Cross-session fact and preference recall
- **AgentCore Runtime** - The agent containerized, launched on Runtime, and one request correlated end to end

### Module 6: Made Memory Inspectable
- Stored preferences as **graph nodes** instead of opaque managed records
- Kept **full provenance** - every `Preference` links back to its source `Message` and to the real `Hotel` node
- Corrected a wrong preference with a single `SET`, no delete and re-extract
- Weighed **Neo4j memory against AgentCore Memory** on write timing, auditability, correction, and who operates it

## Key Takeaways

```text
┌─────────────────────────────────────────────────────────────────┐
│                    GRAPHRAG DECISION MATRIX                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Question Type          →  Best Approach                        │
│  ─────────────────────────────────────────────                  │
│  Entity lookup          →  Hybrid Retrieval                     │
│  Known query patterns   →  Template Cypher                      │
│  Ad-hoc analysis        →  Text2Cypher                          │
│  Production agents      →  MCP + All approaches                 │
│                                                                 │
│  Memory Strategy        →  Use Case                             │
│  ─────────────────────────────────────────────                  │
│  Built-in              →  Short sessions, prototyping           │
│  Graph-based           →  Persistence, entity tracking          │
│  Hybrid                →  Production (recommended)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Before vs. After

| Query type | Vector RAG | GraphRAG |
|------------|------------|----------|
| Aggregation ("average guest rating in Paris") | ❌ Estimated from three chunks | ✅ `AVG()` across every hotel |
| Counting ("hotels with a pool") | ❌ Undercounted the retrieved chunks | ✅ `COUNT()` on the full graph |
| Multi-hop ("Cairo hotels with a spa **and** a pool") | ❌ Partial match on similarity | ✅ Traversed Hotel → Amenity |
| Out-of-domain ("hotels in Antarctica") | ❌ Fabricated from lookalike docs | ✅ Honest "no results found" |

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

## Next Steps

### Immediate (This Week)
1. **Adapt to your domain** - Swap the hotel entities for your own business data
2. **Expand the schema** - Add more node types and relationships
3. **Test edge cases** - Find queries that still need tuning

### Short-term (This Month)
1. **Tune retrieval quality** - Adjust the hybrid `alpha` and expansion Cypher against your own query logs
2. **Implement guardrails** - Add query validation and safety checks
3. **Set up monitoring** - Track query patterns and accuracy metrics

### Long-term (This Quarter)
1. **Production deployment** - Deploy to Lambda or ECS
2. **User feedback loop** - Collect and incorporate corrections
3. **Graph maintenance** - Automate data updates and refresh

## Resources

### Documentation
- [Amazon Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Neo4j GraphRAG for Python](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

### Code Repositories
- [Neo4j MCP Server](https://github.com/neo4j-contrib/mcp-neo4j)
- [LangChain Neo4j Integration](https://python.langchain.com/docs/integrations/graphs/neo4j_cypher)

### Further Learning
- [AWS Workshop: Amazon Bedrock Agents](https://catalog.workshops.aws/amazon-bedrock-agents)
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/)

## Feedback

We'd love to hear your feedback on this workshop!

:::alert{type="info" header="Share Your Experience"}
What worked well? What could be improved? Let us know!
:::

## Don't Forget!

⚠️ **Complete the cleanup in the next section** to avoid unexpected AWS charges.

Click **Next** to proceed to Cleanup.
