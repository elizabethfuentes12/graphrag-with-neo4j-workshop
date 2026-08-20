[< Back to the workshop README](../../README.md)

# Module 5: Deploy to AgentCore Runtime

The grounded booking agent from Module 3.2 has only ever run in a notebook kernel on your laptop: your credentials make the Bedrock call, your shell environment holds the Neo4j password, and the agent stops answering the moment the kernel does. This module moves that same agent, unchanged in how it reasons, into a container that Amazon Bedrock AgentCore Runtime builds, starts, and holds.

**The mechanism, in one sentence: the agent's tools and grounding instructions do not change when its address becomes an ARN instead of a kernel.**

**At a Glance**
- **Failure it stops:** an agent that only answers questions from Jupyter, a laptop holding a Neo4j password in plaintext, and a deployment story that has never actually been run.
- **Neo4j:** read and write, from inside the deployed container, exactly as Module 3.2 does it. The maximum-guests rule and the idempotent reservation write stay enforced inside the same Neo4j transaction; moving the agent does not move the rule.
- **AWS:** one IAM execution role, one ECR repository, one CodeBuild project, and one AgentCore Runtime. Claude on Amazon Bedrock still does the reasoning, reached through a cross-region inference profile.
- **You'll build:** a running AgentCore Runtime named `GraphRagBookingAgent`, reachable by `InvokeAgentRuntime` from anywhere, tagged so the cleanup step below can find it.

---

## The notebook

| Notebook | What it proves |
|---|---|
| [`5.1_deploy.ipynb`](5.1_deploy.ipynb) | The same agent, reachable by `InvokeAgentRuntime` instead of a Jupyter kernel, passes five smoke tests that assert on the tools' structured verdicts rather than on the model's prose |

The notebook stages the shared `workshop` package and `reservation_command.py` into `runtime_app/` immediately before the build, since Docker only sees its own build context and both files live elsewhere in the repository. It then creates the execution role, launches the Runtime through the AgentCore starter toolkit, tags everything the toolkit created, and runs the five smoke tests against the live endpoint.

Every live cell checks `DEPLOY_READY` first and skips cleanly if AWS credentials or the four Neo4j environment variables are missing, so reading through the notebook without deploying anything is safe.

## Prerequisites

- Module 3.2's grounded booking agent working end to end, since this module deploys it unchanged.
- AWS credentials with permission to create an IAM role, an ECR repository, a CodeBuild project, and an AgentCore Runtime.
- The same four `NEO4J_*` values every other module reads from `.env`.

## Files in this folder

| File | Purpose |
|---|---|
| `5.1_deploy.ipynb` | The module notebook |
| `runtime_app/` | The container build context: `booking_agent.py`, `agent_requirements.txt`, and the `Dockerfile`. The `workshop` wheel, `reservation_command.py`, and `BUILD_INFO.txt` are staged here by the notebook and are not checked in |

## Cleanup

The IAM execution role, the ECR repository, the CodeBuild project, and the AgentCore Runtime itself all keep accruing charges for as long as they exist, and nothing in this module deletes them automatically. Each one carries the `WorkshopResource` tag the notebook applies, so they can be found and removed by that tag when you are finished. At an AWS Workshop Studio event the account is reclaimed for you when the event ends.

## The workshop page

`workshop-content/content/05-agentcore-deploy/index.en.md`
