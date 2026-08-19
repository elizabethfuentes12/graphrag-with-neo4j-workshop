[< Back to the workshop README](../../README.md)

# Module 4: Production Agent with AgentCore

The booking agent from Module 3 runs entirely in-process: its tools are Python functions in the same kernel, and it forgets everything the moment the notebook restarts. This module moves the tools behind a managed MCP endpoint and gives the agent memory that outlives a session, without changing how the agent itself is written.

**The mechanism, in one sentence: the agent code does not change when a tool stops being a function call and starts being a signed request.**

**At a Glance**
- **Failure it stops:** retrieval that only works on the machine that authored it, an API key pasted into a notebook, and an agent that has to be told the same thing in every session.
- **Neo4j:** read-only, from inside Lambda. The Gateway is a read path and exposes no write.
- **AWS:** AgentCore Gateway, AWS Lambda, IAM SigV4, Secrets Manager for the Neo4j credential, and AgentCore Memory.
- **You'll build:** Lambda functions under the `hotel-booking-*` prefix, one Gateway, the IAM roles under `workshop-*`, and one AgentCore Memory resource.

---

## The two notebooks

| Notebook | What it proves |
|---|---|
| [`4.1_agentcore_gateway.ipynb`](4.1_agentcore_gateway.ipynb) | The same retrieval, reached over IAM-authenticated MCP, with no API key anywhere |
| [`4.2_agentcore_memory.ipynb`](4.2_agentcore_memory.ipynb) | A preference stated in session one, recalled in session two by an agent with no history |

Run `4.1` first. `4.2` connects to the Gateway `4.1` created.

## Part 1: the Gateway is a read path

The Lambda functions expose retrieval patterns, not writes. That is a deliberate boundary: the reservation command from Module 3 stays where the transaction is, and nothing a model can reach through MCP can change hotel data.

Authentication is IAM SigV4 through `mcp-proxy-for-aws`, which signs every request with the caller's own AWS credentials. There is no key to rotate, and no key to leak into a notebook output.

:warning: Naming is dictated by the participant IAM policy, which scopes by ARN prefix. Lambda functions are `hotel-booking-*`, IAM roles are `workshop-*` or `AmazonBedrockAgentCoreSDK*`, and secrets are `workshop-*`, `neo4j-ws-*`, or `bedrock-agentcore-*`. A name outside its prefix works for whoever authored it under broader credentials and fails as `AccessDenied` for every participant.

## Part 2: managed memory, and its cost

AgentCore Memory runs two extraction strategies over the raw transcript: `SEMANTIC` for facts, `USER_PREFERENCE` for preferences. Both run asynchronously, so `4.2` waits for the extraction and then reads the records straight from the Memory service before opening a second session. Seeing what was extracted, and how long it took to appear, is the part that does not come across in a diagram.

The second session shares the actor and carries no conversation history. There is no preferences tool on the Gateway, so a correct answer there can only have come from long-term memory.

What that costs is inspectability. The recalled preference arrives through a service API with no link back to the message that produced it or to the `Hotel` node it is about, and correcting a wrong one means deleting and re-extracting. Module 6 is the direct comparison.

## Files in this folder

| File | Purpose |
|---|---|
| `4.1_agentcore_gateway.ipynb` | Gateway, Lambda tools, IAM-authenticated MCP |
| `4.2_agentcore_memory.ipynb` | AgentCore Memory across two sessions |
| `lambda_tools/` | One directory per Lambda handler, plus the shared requirements |

## The workshop page

`workshop-content/content/04-production-agent/index.en.md`
