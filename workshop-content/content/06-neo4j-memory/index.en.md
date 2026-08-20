---
title: "Module 6: Inspectable Neo4j Memory"
weight: 70
---

## Why You Cannot Debug AgentCore Memory

:link[AgentCore Memory]{href="https://aws.amazon.com/bedrock/agentcore/" external=true} works. But when the extracted preference is wrong — "near the elevator" instead of "away from it" — you cannot find the source message, correct the record, or link it to the hotel the guest actually booked.

:image[AgentCore Memory vs Neo4j Memory: managed black-box extraction vs explicit graph provenance]{src="../../images/04-memory-comparison.png" width=800}

---

## Graph Memory Structure

Open `notebooks/06-neo4j-memory/6.1_neo4j_memory.ipynb`.

```
(User)-[:HAS_PREFERENCE]->(Preference)-[:DERIVED_FROM]->(Message)
                                      ↘[:ABOUT_HOTEL]->(Hotel)
```

Every preference is linked to the exact source message and the real `Hotel` node — not a name string.

---

## What the Notebook Proves

**Actor A — `SESSION_A2` (no history):** preference recalled ✅

**Actor B — same query:** returns nothing ✅

**Full audit trail in one Cypher query\:**

:::code{language=cypher showCopyAction=true}
CYPHER 25
MATCH (u:User {identifier: $actor})
      -[:HAS_PREFERENCE]->(p:Preference)
      -[:DERIVED_FROM]->(m:Message)
      <-[:HAS_MESSAGE]-(c:Conversation),
      (p)-[:ABOUT_HOTEL]->(h:Hotel {name: $hotel_name})
RETURN u.identifier AS actor, p.preference AS preference, m.content AS source_message,
       c.session_id AS source_session, h.name AS hotel
:::

To correct a wrong preference\: `SET p.preference = "high floor, away from elevator"`. No delete, no re-extract.

---

## AgentCore vs Neo4j Memory

| | :link[Neo4j]{href="https://neo4j.com/" external=true} | AgentCore |
|---|---|---|
| Write timing | Synchronous | Async — seconds to minutes |
| Extraction | Explicit writes | LLM-driven |
| Auditability | Full graph provenance | :link[Amazon CloudWatch]{href="https://aws.amazon.com/cloudwatch/" external=true} logs only |
| Correction | `SET` | Delete + re-extract |
| Domain link | `[:ABOUT_HOTEL]→Hotel` | Not possible |
| Operations | You own it | AWS manages it |

## Next

Head to [Summary](../summary/).
