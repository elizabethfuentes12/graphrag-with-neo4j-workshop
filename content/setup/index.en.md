---
title: "Setup"
weight: 10
---

## Get Your Environment Ready (~10 minutes)

Choose your path\:

| Path | When to use |
|------|------------|
| [Workshop Studio Access](./workshop-studio-access/) | AWS-hosted event — your account is pre-provisioned |
| [Own Account Setup](./own-account-setup/) | Self-paced — your own AWS account |

## What Gets Configured

Both paths end with the same verified environment\:

- **Code Editor** — browser-based VS Code with the workshop repository cloned
- **Neo4j on ECS Fargate** — hotel knowledge graph pre-loaded from a database dump
- **Amazon Bedrock** — Claude Sonnet 4 and Amazon Nova 2 Embeddings accessible
- **Neo4j credentials** — URI, username, and password available in your environment

## Quick Verification Checklist

After completing your path, confirm\:

- [ ] Code Editor opens in the browser
- [ ] `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` are set in the terminal
- [ ] Neo4j connection test returns 296 hotels
- [ ] Bedrock embedding call returns 1024 dimensions

::children{depth=1 variant=list}
