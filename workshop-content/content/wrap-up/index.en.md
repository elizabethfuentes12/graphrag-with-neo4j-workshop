---
title: "Wrap-up"
weight: 90
---

# Workshop Wrap-up

**Congratulations on completing the GraphRAG workshop!**

## What You Accomplished

You:

### Module 2: Witnessed the Problem
- Saw pure vector RAG **hallucinate** on relational queries
- Understood **why** semantic similarity fails for multi-hop reasoning
- Measured the gap between vector retrieval and ground truth

### Module 3: Implemented Solutions
- **Hybrid Retrieval** - Vector entry points + graph expansion
- **Template Cypher** - LLM-parameterized query patterns
- **Text2Cypher** - Full natural language to graph query generation

### Modules 4 and 5: Built Production Infrastructure
- **AgentCore Runtime** - Agent orchestration with tool use
- **MCP Gateway** - Model Context Protocol integration layer
- **Neo4j MCP Server** - Official graph database tools
- **Memory Strategies** - Session vs. persistent graph-based memory

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

| Metric | Vector RAG | GraphRAG |
|--------|------------|----------|
| Relational queries | ❌ Hallucinated | ✅ Accurate |
| Multi-hop reasoning | ❌ Failed | ✅ Traversed |
| Contact identification | ❌ Fabricated | ✅ Correct |
| Confidence alignment | ❌ Confidently wrong | ✅ Verified |

## Architecture You Built

```text
User Query
    │
    ▼
┌──────────────────────────────────────────────────┐
│              AgentCore Runtime                   │
│  ┌──────────────────────────────────────────┐   │
│  │ Claude 3 Sonnet + Tool Use               │   │
│  └──────────────────┬───────────────────────┘   │
│                     │                            │
│  ┌──────────────────▼───────────────────────┐   │
│  │           MCP Gateway                     │   │
│  └──────────────────┬───────────────────────┘   │
│                     │                            │
│  ┌──────────────────▼───────────────────────┐   │
│  │        Neo4j MCP Server                   │   │
│  │  • read_neo4j_cypher                      │   │
│  │  • get_neo4j_schema                       │   │
│  └──────────────────┬───────────────────────┘   │
└─────────────────────┼────────────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │    Neo4j     │
              │  Knowledge   │
              │    Graph     │
              └──────────────┘
```

## Next Steps

### Immediate (This Week)
1. **Adapt to your domain** - Replace IT entities with your business data
2. **Expand the schema** - Add more node types and relationships
3. **Test edge cases** - Find queries that still need tuning

### Short-term (This Month)
1. **Add vector indexes** - Enable hybrid semantic+graph search in Neo4j
2. **Implement guardrails** - Add query validation and safety checks
3. **Set up monitoring** - Track query patterns and accuracy metrics

### Long-term (This Quarter)
1. **Production deployment** - Deploy to Lambda or ECS
2. **User feedback loop** - Collect and incorporate corrections
3. **Graph maintenance** - Automate data updates and refresh

## Resources

### Documentation
- [Amazon Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Neo4j GraphRAG Documentation](https://neo4j.com/docs/cypher-manual/current/)
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
