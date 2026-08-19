---
title: "Module 4: Production Agent with AgentCore"
weight: 50
---

## From Local to Production

The booking agent from Module 3 runs entirely in-process. Three things break at production scale:

| Gap | Fix |
|---|---|
| Tools as in-process functions | :link[Bedrock AgentCore]{href="https://aws.amazon.com/bedrock/agentcore/" external=true} Gateway + :link[AWS Lambda]{href="https://aws.amazon.com/lambda/" external=true} — managed MCP endpoints |
| No authentication | **IAM SigV4** — no API keys to manage |
| Stateless between sessions | **AgentCore Memory** — cross-session fact and preference recall |

:image[AgentCore Gateway sits between the agent and the reservation tools; AgentCore Memory persists facts across sessions]{src="../../images/03-agentcore-architecture.png" width=800}

---

## Part 1 — Gateway and Retrieval Lambdas

Open `notebooks/04-production-agent/4.1_agentcore_gateway.ipynb`.

:::alert{type="warning" header="These resources stay until you delete them"}
This part creates two Lambda functions (`hotel-booking-search-hotel-knowledge`, `hotel-booking-graph-query`), an AgentCore Gateway (`hotel-booking-gateway`) with one target per tool, a Secrets Manager secret (`neo4j-ws-retrieval`), and two IAM roles (`workshop-hotel-lambda-role`, `workshop-hotel-gateway-role`).

The Gateway and the secret bill while they exist, and the Lambdas bill per invocation. Nothing here removes them for you. In a Workshop Studio account they disappear when the event ends; in your own account, delete them from the console or the CLI when you are finished.
:::

The retrieval you ran in Module 3 does not change here. It moves behind a managed endpoint, and the same two functions run inside Lambda:

| Gateway tool | Retriever | Question shape |
|---|---|---|
| `search_hotel_knowledge` | `HybridCypherRetriever` | Semantic: rooms, amenities, policies, services |
| `graph_query` | `Text2CypherRetriever` | Structured: counts, averages, filters, multi-hop |

Both tools import from `notebooks/workshop/hybrid_retrieval.py`, the file Module 3 already ran. Each Lambda entry point is a wrapper that unwraps the event and calls one of them, so there is no second copy of retrieval to keep in step with the first.

**Neither tool writes.** The reservation write stays in the Module 3 notebook and is never exposed through the Gateway, so "the agent cannot change the graph" is a property of what is deployed rather than a promise in a prompt.

The Neo4j connection reaches the Lambdas through AWS Secrets Manager as `neo4j-ws-retrieval`, and the execution role `workshop-hotel-lambda-role` is allowed to read that one secret and invoke Bedrock models. Nothing else.

:::alert{type="info" header="What a production deployment would change here"}
These Lambdas connect with ordinary workshop credentials. In production this tool path would use a **read-only Neo4j role behind a read-only IAM policy**, because `graph_query` runs Cypher that a model generated rather than Cypher a human reviewed. `Text2CypherRetriever` plans every generated statement with `EXPLAIN` and refuses to execute anything the planner does not report as read-only, and the notebook proves that with a stub model that tries to write. A database-level read-only role is the control that still holds when the library is wrong.
:::

After deployment, the agent connects with one `uvx` command\:

:::code{language=python showCopyAction=true}
gateway_mcp = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=["mcp-proxy-for-aws@latest", GATEWAY_ENDPOINT_URL, "--region", "us-east-1"],
        env=os.environ.copy(),
    ))
)
with gateway_mcp:
    agent = Agent(tools=gateway_mcp.list_tools_sync(), ...)
:::

The proxy signs every request with your AWS credentials — nothing changes in the agent code.

### Verifying a tool that is allowed to say "I don't know"

A grounded tool that returns nothing and a broken tool that returns nothing look identical. A dead index, a wrong index name, a bad credential, or a retriever pointed at the wrong database all produce an empty result, and an empty result reads as a correct refusal.

So the notebook checks both tools in pairs: a **negative control**, where a hotel that does not exist produces no match, and a **positive control**, where a hotel that does exist returns one exact value — an address, and a guest rating. The positive control is the one that cannot pass against a dead index or an empty graph, which is why it is there.

---

## Part 2 — AgentCore Memory

Open `notebooks/04-production-agent/4.2_agentcore_memory.ipynb`.

:::alert{type="warning" header="AWS resources created"}
AgentCore Memory resource. Incurs charges until deleted.
:::

**Session 1** — a guest mentions name, loyalty number, and room preference.

AgentCore extracts asynchronously. The notebook polls and shows what was extracted:

:::code{language=bash}
🧠 Preferences (1): Prefers high floor, away from elevator
🧠 Facts (2): Name is Alice Chen | Loyalty number LY-88421
:::

**Session 2** — brand-new `session_id`, same `actor_id`. The agent recalls the preferences without being told again.

:::alert{type="info" header="The trade-off"}
Fast to wire up, but the extraction is asynchronous and opaque. Module 6 shows what you give up.
:::

## Next

Head to [Module 5](../05-agentcore-deploy/).
