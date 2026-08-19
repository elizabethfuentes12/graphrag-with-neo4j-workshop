---
title: "Workshop Studio Access"
weight: 1
---

## Step 1: Access Your AWS Account

1. In the Workshop Studio left panel, click **Open AWS Console**
2. Confirm you are in **us-east-1 (N. Virginia)** — check the top-right region selector

---

## Step 2: Open Code Editor

1. In the Workshop Studio left panel, find the **Outputs** section
2. Copy the **CodeEditorURL** value
3. Open it in a new browser tab
4. Log in with the **CodeEditorUser** and password from the Outputs section

:::alert{type="info" header="Code Editor is VS Code in the browser"}
The workshop repository is already cloned at `/Workshop`. Open a terminal with **Terminal → New Terminal**.
:::

---

## Step 3: Set Environment Variables

Your :link[Neo4j]{href="https://neo4j.com/" external=true} connection details are in the Workshop Studio Outputs. In the Code Editor terminal\:

:::code{language=bash showCopyAction=true}
# Paste your values from Workshop Studio Outputs
export NEO4J_URI="<Neo4jURI from Outputs>"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="<Neo4jPassword from Outputs>"
export NEO4J_DATABASE="neo4j"
export AWS_REGION="us-east-1"
:::

To make these permanent for the session, add them to a `.env` file\:

:::code{language=bash showCopyAction=true}
cd /Workshop/notebooks
cat > .env << EOF
NEO4J_URI=${NEO4J_URI}
NEO4J_USERNAME=${NEO4J_USERNAME}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
NEO4J_DATABASE=neo4j
AWS_REGION=us-east-1
EOF
:::

---

## Step 4: Install Dependencies

:::code{language=bash showCopyAction=true}
cd /Workshop/notebooks
uv venv && uv pip install -r requirements.txt
:::

---

## Step 5: Verify Everything Works

:::code{language=bash showCopyAction=true}
uv run python - << 'EOF'
import os, json, boto3
from dotenv import load_dotenv
load_dotenv()
from neo4j import GraphDatabase

# Neo4j
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")))
with driver.session() as s:
    n = s.run("MATCH (h:Hotel) RETURN count(h) as n").single()["n"]
print(f"✅ Neo4j: {n} hotels")
driver.close()

# Bedrock Nova 2 embeddings
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = bedrock.invoke_model(
    modelId="amazon.nova-2-multimodal-embeddings-v1:0",
    body=json.dumps({"taskType":"SINGLE_EMBEDDING","singleEmbeddingParams":{"embeddingPurpose":"GENERIC_INDEX","embeddingDimension":1024,"text":{"truncationMode":"END","value":"test"}}}),
    contentType="application/json", accept="application/json")
dims = len(json.loads(resp["body"].read())["embeddings"][0]["embedding"])
print(f"✅ Bedrock Nova 2: {dims}-dim embeddings")
EOF
:::

**Expected output\:**
:::code{language=bash}
✅ Neo4j: <N> hotels
✅ Bedrock Nova 2: 1024-dim embeddings
:::

Any hotel count above zero means the graph dump loaded. The exact number depends on the dump you were given.

:::alert{type="success" header="Ready"}
Proceed to [Module 1](../../01-vectorial-rag-hallucinates/).
:::

---

## Troubleshooting

:::expand{header="Neo4j connection refused" defaultExpanded=false}
The ECS Fargate task may still be starting (takes 2–3 minutes after stack creation). Wait 2 minutes and retry. You can check the task status in the ECS console under the workshop cluster.
:::

:::expand{header="Bedrock access denied" defaultExpanded=false}
Confirm you are in **us-east-1**. Amazon Nova 2 Multimodal Embeddings is an :link[Amazon Bedrock]{href="https://aws.amazon.com/bedrock/" external=true} model available only in us-east-1. Your workshop account has model access pre-enabled, so no console changes are needed.
:::
