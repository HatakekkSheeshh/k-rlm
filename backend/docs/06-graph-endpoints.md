# 06 — Graph Endpoints

## New Endpoints

### POST /api/v1/graph/extract
Extracts entities and relations from document, stores in Neo4j, runs community pipeline.

**Request:** Multipart form data
- `file` (required): Document file to upload
- `model` (optional, default: `"phi3:mini"`): Ollama model tag
- `summarize` (optional, default: `true`): Whether to run community pipeline

**Response:**
```json
{
  "filename": "document.pdf",
  "graph": {
    "nodes": [
      {"id": "Alice", "label": "PERSON", "properties": {}}
    ],
    "edges": [
      {"source": "Alice", "target": "Bob", "relation": "KNOWS", "properties": {}}
    ]
  },
  "raw_text": "Extracted text...",
  "metrics": {
    "model": "phi3:mini",
    "strategy": "extraction_chunked",
    "latency_s": 5.678
  },
  "community_summaries": [
    {
      "community_id": 1,
      "node_count": 12,
      "edge_count": 8,
      "summary": "This community represents...",
      "stored_in_qdrant": true
    }
  ]
}
```

### GET /api/v1/graph/data
Retrieves full graph for visualization.

**Query Params:**
- `document` (optional): Filter by document name

**Response:**
```json
{
  "nodes": [
    {"id": "Alice", "label": "PERSON", "properties": {}}
  ],
  "edges": [
    {"source": "Alice", "target": "Bob", "relation": "KNOWS"}
  ]
}
```

### GET /api/v1/graph/communities
Retrieves community summaries from Qdrant.

**Query Params (all required):**
- `document` (required): Document name to get communities for
- `run_pipeline` (optional, default: `false`): Run pipeline if no summaries exist
- `model` (optional, default: `"phi3:mini"`): Model to use for summarization

**Response:**
```json
{
  "document": "document.pdf",
  "communities": [
    {
      "community_id": 1,
      "node_count": 12,
      "edge_count": 8,
      "context": "Entity: Alice (type: PERSON)\nRelation: Alice --[KNOWS]--> Bob"
    }
  ]
}
```

## Integration
- `/extract` runs the full pipeline: extract → store → detect communities → summarize → Qdrant
- `/data` fetches raw nodes/edges for frontend graph visualization
- `/communities` fetches LLM-generated summaries for context display

## Files Changed
- `app/routers/graph.py` — Added /data and /communities endpoints
- `app/schemas.py` — Added GraphDataResponse, CommunitySummaryResponse
