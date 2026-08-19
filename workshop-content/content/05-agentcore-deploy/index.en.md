---
title: "Module 5: Deploy to AgentCore Runtime"
weight: 60
---

## The Agent Leaves Your Laptop

The grounded booking agent from Module 3 works. It also runs in your Jupyter kernel, holds your Neo4j password in your shell environment, and answers questions only for as long as that kernel is alive. None of that survives contact with production.

:link[Amazon Bedrock AgentCore Runtime]{href="https://aws.amazon.com/bedrock/agentcore/" external=true} takes the same agent and holds it for you.

| Module 3.2 | Module 5.1 |
|---|---|
| Runs in your kernel | Runs in a container AgentCore starts |
| Your laptop holds the Neo4j password | The Runtime holds it, injected at launch |
| Reachable only from Jupyter | Reachable by `InvokeAgentRuntime` from anywhere |
| Session is your kernel's memory | Each invocation isolated by session ID |

What does **not** change is how the agent reasons. Same two tools, same grounding instructions, same refusal to answer what the graph cannot support.

---

## What Gets Deployed

Open `notebooks/05-agentcore-deploy/5.1_deploy.ipynb`.

:::alert{type="warning" header="AWS resources created"}
One IAM execution role, one ECR repository, one CodeBuild project, and one AgentCore Runtime. The container build takes three to five minutes.

The Runtime, the ECR image, and the CodeBuild project keep accruing charges for as long as they exist, and nothing in this workshop deletes them. At an AWS Workshop Studio event the account is reclaimed for you when the event ends. If you are running this in your own account, remove those three yourself when you are finished.
:::

```
InvokeAgentRuntime
        |
        v
+------------------------------+
|  AgentCore Runtime           |
|  GraphRagBookingAgent        |
|                              |
|  booking_agent.py            |
|   |- search_hotel_knowledge -----> Neo4j hybrid retrieval
|   |- create_reservation ---------> Neo4j write, rule in-transaction
|   `- BedrockModel ---------------> Claude on Amazon Bedrock
+------------------------------+
```

Both tools run in-process against Neo4j. The maximum-guests rule stays where it has been since Module 3: in the graph, enforced inside the same transaction as the write. Moving the agent into a container does not move the rule, which is the whole reason this deployment is worth trusting.

---

## The Build Context Problem

Docker copies only its build context. The agent needs two things that live elsewhere in the repository:

- `notebooks/workshop/`, the package every module shares
- `notebooks/03-retrieval-patterns/reservation_command.py`, the graph-enforced write path

Step 2 of the notebook stages both into `runtime_app/` immediately before the build. The staged copies are gitignored and rewritten on every run, so one versioned copy of each stays the source of truth and an edit reaches the next build.

---

## Five Smoke Tests

The notebook invokes the deployed Runtime and asserts on structured tool verdicts rather than on the model's prose. A test that reads the response text passes when the model sounds right. A test that reads the verdict passes only when the graph agreed.

| Test | What it proves |
|---|---|
| Hero question | The answer carries the exact recorded address, `789 Corniche el-Nil, Cairo 11519, Egypt` |
| Hotel that does not exist | An ungrounded `hotel_id` never reaches the write, and nothing is recorded |
| Availability question | `answerable` is false, `missing_fact` is `live_room_availability` |
| 15-guest request | `status` is `rejected`, and the graph confirms no node was written |
| 10-guest request, delivered twice | One node created, replay returns `duplicate=true`, still one node |

:::alert{type="info" header="Why the first test carries the others"}
A refusal and a broken retriever produce the same silence. Point the vector index at nothing and every abstention test still passes, because abstaining is exactly what a dead index looks like from outside. The hero test is the control that separates them: it demands a specific value that only a working graph can supply, so the refusals below it mean the agent declined rather than that nothing was there. Every abstention in this notebook asserts a real retrieved fact alongside its refusal for the same reason.
:::

:::alert{type="info" header="Why the last two matter most"}
The rejection and the replay are the properties that make an agent safe to expose over an API. A caller can retry a request without creating a second reservation, and a model cannot talk its way past a limit that lives in the database.
:::

---

## Reading the Logs

Each invocation logs a start line, a completion line carrying the tools used and the command status, and nothing else. The `request_id` you pass in is the correlation key across all of them.

:::code{language=bash showCopyAction=true}
aws logs tail /aws/bedrock-agentcore/runtimes/<RUNTIME_ID>-DEFAULT --follow
:::

Failures log the exception type and never the message. A Neo4j driver error carries the connection URI, and sometimes the credential that failed, into a log group with broader read access than the `.env` it came from.

## Next

Head to [Module 6](../06-neo4j-memory/).
