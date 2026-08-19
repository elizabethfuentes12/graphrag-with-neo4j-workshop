---
title: "Module 3: Production Agent with AgentCore"
weight: 40
---

## From Local to Production

The booking agent from Module 2 runs entirely in-process. Three things break at production scale:

| Gap | Fix |
|---|---|
| Tools as in-process functions | :link[Bedrock AgentCore]{href="https://aws.amazon.com/bedrock/agentcore/" external=true} Gateway + :link[AWS Lambda]{href="https://aws.amazon.com/lambda/" external=true} — managed MCP endpoints |
| No authentication | **IAM SigV4** — no API keys to manage |
| Stateless between sessions | **AgentCore Memory** — cross-session fact and preference recall |

:image[AgentCore Gateway sits between the agent and the reservation tools; AgentCore Memory persists facts across sessions]{src="../../images/03-agentcore-architecture.png" width=800}

---

## Part 1 — Gateway and Lambda Tools

Open `notebooks/03a_agentcore_gateway.ipynb`.

:::alert{type="warning" header="AWS resources created"}
Three Lambda functions + AgentCore Gateway. The cleanup notebook removes them.
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

---

## Part 2 — AgentCore Memory

Open `notebooks/03b_agentcore_memory.ipynb`.

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
Fast to wire up, but the extraction is asynchronous and opaque. Module 4 shows what you give up.
:::

## Next

Head to [Module 4](../04-neo4j-memory/).
