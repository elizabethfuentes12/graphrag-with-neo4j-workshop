# Canva Diagram Prompts

Use these prompts in [Canva's AI image generator](https://www.canva.com/ai-image-generator/) or Magic Media to create professional diagrams for this workshop. After generating, export as PNG at 1600×900px and save to this directory.

---

## Diagram 1: RAG vs. Graph-RAG Problem
**Filename:** `01-rag-vs-graphrag-problem.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Clean, modern technical diagram on white background. Split into two columns:

LEFT COLUMN labeled "Traditional RAG" with orange warning icon:
- Show 3 document chunks floating, labeled "Top-3 chunks"
- Arrow pointing to a brain/LLM icon
- LLM generates a number with a question mark, labeled "Fabricated average"
- Small dashed border with text "Only sees 3 of 300 documents"

RIGHT COLUMN labeled "Graph-RAG" with green checkmark icon:
- Show a network/graph of connected nodes (hotels, amenities, cities)
- Arrow pointing to a database cylinder labeled "Neo4j"
- Database returns exact number, labeled "AVG() computed across all 300 hotels"
- Small solid border with text "Queries all 300 hotels"

Footer: "Same question: What is the average guest rating of hotels in Paris?"
Style: AWS workshop style, flat design, Inter font, colors: #232F3E dark navy, #FF9900 orange for RAG failures, #1DB954 green for Graph-RAG successes
```

---

## Diagram 2: RAG vs. Graph-RAG Architecture
**Filename:** `01-rag-vs-graphrag-architecture.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Clean AWS architecture diagram on white background showing two parallel retrieval paths.

TOP: "300 Hotel FAQ Documents" in a document stack icon

SPLIT INTO TWO PATHS:

LEFT PATH labeled "RAG Agent":
- FAISS index cylinder (blue) labeled "FAISS Vector Index"
- Arrow down to "Top-3 chunks" box
- Arrow down to LLM brain icon labeled "Amazon Bedrock Claude"
- Arrow down to speech bubble labeled "Summarized (possibly wrong)"

RIGHT PATH labeled "Graph-RAG Agent":
- Neo4j circle icon (cyan) labeled "Neo4j Knowledge Graph"
- Arrow down to code box showing "MATCH (h:Hotel) RETURN AVG(h.rating)"
- Arrow down to database result icon
- Arrow down to speech bubble labeled "Precise result"

BOTTOM: Arrow from both paths to "Same user query" box

Style: AWS architecture diagram style, flat icons, white background, #4581C3 for Neo4j, #FF9900 for AWS, clean sans-serif font
```

---

## Diagram 3: Retrieval Patterns Decision Tree
**Filename:** `02-retrieval-decision-tree.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Modern flowchart decision tree on white background with pastel node colors.

START: Diamond shape "What type of query?" at top

FOUR BRANCHES flowing down:

BRANCH 1 (leftmost, purple):
Label: "Semantic / paraphrased question"
Arrow to rounded rectangle: "VectorRetriever"
Sub-label: "embedding similarity"
Example: "cancellation policy for flexible rates"

BRANCH 2 (left-center, blue):
Label: "Exact name, code, or ID"
Arrow to rounded rectangle: "HybridRetriever"
Sub-label: "vector + full-text, low alpha"
Example: "hotel near ZIP 60611"

BRANCH 3 (right-center, teal):
Label: "Semantic entry + graph context"
Arrow to rounded rectangle: "VectorCypherRetriever"
Sub-label: "match chunk → traverse graph"
Example: "amenities at the harbor hotel"

BRANCH 4 (rightmost, orange):
Label: "Count or aggregate"
Arrow to rounded rectangle: "Text2CypherRetriever"
Sub-label: "LLM generates Cypher"
Example: "how many hotels have a pool?"

BOTTOM ROW: All four arrows connect to a final box "Neo4j Knowledge Graph"

Style: flat design, Poppins font, soft shadows, white background, colored borders matching branch colors
```

---

## Diagram 4: Retrieval Patterns Comparison
**Filename:** `02-retrieval-patterns-comparison.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Clean comparison table / infographic on white background showing four Neo4j retrieval patterns.

Four horizontal rows, each with:
- Colored left badge (icon + pattern name)
- "How it works" column with 2-line description
- "Best for" column with one-line use case
- Score bars for: Speed, Accuracy, Complexity

ROW 1 (purple badge): VectorRetriever
Icon: magnifying glass with waves
How: Embedding cosine similarity over Chunk nodes
Best for: Paraphrased semantic questions
Speed: ████████░░ | Accuracy: ██████░░░░ | Complexity: ██░░░░░░░░

ROW 2 (blue badge): HybridRetriever
Icon: two overlapping circles (venn)
How: Vector score + full-text score, weighted by alpha
Best for: Exact names, codes, identifiers
Speed: ███████░░░ | Accuracy: █████████░ | Complexity: ████░░░░░░

ROW 3 (teal badge): VectorCypherRetriever
Icon: magnifying glass + graph network
How: Vector finds entry chunk → Cypher expands to hotel
Best for: Semantic entry + connected context
Speed: ██████░░░░ | Accuracy: ████████░░ | Complexity: ██████░░░░

ROW 4 (orange badge): Text2CypherRetriever
Icon: chat bubble + database
How: LLM generates and executes Cypher query
Best for: Counts, aggregations, analytics
Speed: ████░░░░░░ | Accuracy: ██████████ | Complexity: ████████░░

Footer note (orange warning): "Text2CypherRetriever runs LLM-generated Cypher — use a read-only trust boundary in production"

Style: data table infographic, clean horizontal layout, Inter font, white background
```

---

## Diagram 5: Agent Failure Modes
**Filename:** `03-agent-failure-modes.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Landscape 16:9 infographic. HORIZONTAL layout — do NOT stack vertically. The three failure modes must sit SIDE BY SIDE in a single row across the full width of the image.

Dark background (#1a1a2e). Three equal-width columns arranged LEFT TO RIGHT filling the entire horizontal space.

TOP ROW — three columns side by side, each taking roughly 1/3 of the width:

LEFT COLUMN (red accent border, red warning icon at top):
Title: "Hallucinated Availability"
Illustration: chat bubble "Yes, rooms available!" with red X
Label below: "No inventory data in graph"
Tag at bottom: "LLM fabricated from training data"

CENTER COLUMN (orange accent border, orange warning icon at top):
Title: "Rule Bypass"
Illustration: booking form "Guests: 15" with wrong checkmark
Label below: "Policy: max 10 guests"
Tag at bottom: "Prompt instruction ignored"

RIGHT COLUMN (yellow accent border, yellow warning icon at top):
Title: "Duplicate Reservation"
Illustration: two identical booking confirmations side by side
Label below: "Network retry = double booking"
Tag at bottom: "No idempotency = data corruption"

BOTTOM BANNER (full width, green background, spans all three columns):
"Graph-grounded agents prevent all three" with three green checkmark icons

Style: dark tech infographic, landscape orientation, neon accent colors, bold sans-serif font, columns must be horizontal not stacked
```

---

## Diagram 6: Grounded Agent Architecture
**Filename:** `03-grounded-agent-architecture.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Clean architecture diagram on white background showing responsibility separation between Neo4j and AWS.

TWO-ZONE LAYOUT divided by a vertical dashed line:

LEFT ZONE labeled "Neo4j Aura" (cyan/teal theme, #4581C3):
Header: Neo4j logo + "Knowledge + Rules"

Boxes from top to bottom:
1. "Hotel Knowledge Graph" - network nodes icon
   (hotels, amenities, ratings, policies)
2. "Vector Index: hotel_chunk_embeddings" - cylinder icon
3. "Full-text Index: hotel_chunk_fulltext" - text search icon
4. "HybridCypherRetriever" - fixed traversal icon
5. "Maximum-Guests Rule (cap: 10)" - shield/rule icon
6. "Idempotent ReservationRequest Write" - database write icon

RIGHT ZONE labeled "Amazon Bedrock" (orange theme, #FF9900):
Header: AWS logo + "Reasoning only"

Boxes from top to bottom:
1. "Amazon Nova 2 Embeddings" - vector icon
   (1024-dim query embedding)
2. "Claude Sonnet" - brain/LLM icon
   (reasons over retrieved evidence only)
3. "Strands Agent" - tool calling icon
   (tool: search_hotel_knowledge_tool)

CENTER (connecting the zones):
Arrow from Neo4j retrieval → Bedrock: "Bounded evidence JSON"
Arrow from Bedrock decision → Neo4j write: "Validated command input"

BOTTOM BAR: "The LLM never sees the write path. Rules are enforced by the graph."

Style: AWS architecture style, two-tone zones, flat icons, clean labels, professional workshop look
```

---

## Usage Notes

- Generate each image at **1600 × 900 px** for crisp display at any Workshop Studio zoom level.
- Export as **PNG** (not JPEG) to preserve sharp text edges.
- After saving, reference in workshop content with\:
  `:image[Alt text]{src="/static/images/FILENAME.png" width=800}`
- All diagrams use brand-neutral colors. Do not include logos other than Neo4j and AWS marks.
