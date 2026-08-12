# Canva Diagram Prompts

Use these prompts in [Canva's AI image generator](https://www.canva.com/ai-image-generator/) or Magic Media to create professional diagrams for this workshop. Set canvas size to **1600 × 900 px (16:9 landscape)** before generating. Export as PNG and save to this directory.

**Important:** Do not use the word "infographic" in prompts — it causes Canva AI to generate tall vertical layouts. Use "diagram", "illustration", or "visual" instead.

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
Clean comparison table on white background showing four Neo4j retrieval patterns, horizontal rows, landscape orientation.

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

Style: clean comparison diagram, horizontal rows, Inter font, white background
```

---

## Diagram 5: Agent Failure Modes
**Filename:** `03-agent-failure-modes.png`
**Dimensions:** 1600 × 900 px (16:9)

**Canva prompt:**
```
Wide landscape technical diagram, dark navy background (#1a1a2e), 16:9 horizontal format.

Three glowing warning cards arranged as a horizontal triptych — left card, center card, right card — each the same height and width, placed side by side like three panels of a comic strip, spanning the full width of the image.

Left card has a red glowing border. Icon: red warning triangle at top. Title: "Hallucinated Availability". Illustration: a chat bubble saying "Yes, rooms available!" with a red X over it. Small label: "No inventory data in graph". Footer tag: "LLM fabricated from training data".

Center card has an orange glowing border. Icon: orange warning triangle at top. Title: "Rule Bypass". Illustration: a booking form showing "Guests: 15" with a wrong checkmark. Small label: "Policy: max 10 guests". Footer tag: "Prompt instruction ignored".

Right card has a yellow glowing border. Icon: yellow warning triangle at top. Title: "Duplicate Reservation". Illustration: two identical booking confirmation receipts. Small label: "Network retry = double booking". Footer tag: "No idempotency = data corruption".

Below all three cards, a full-width green banner with text "Graph-grounded agents prevent all three" and three green checkmark icons evenly spaced.

Style: dark background, neon glow accents, flat bold sans-serif font, horizontal panoramic layout
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

- Set canvas to **1600 × 900 px (landscape 16:9)** before generating — this locks the horizontal format.
- Export as **PNG** (not JPEG) to preserve sharp text edges.
- After saving, reference in workshop content with\:
  `:image[Alt text]{src="/static/images/FILENAME.png" width=800}`
- All diagrams use brand-neutral colors. Do not include logos other than Neo4j and AWS marks.
