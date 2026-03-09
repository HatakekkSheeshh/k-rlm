# 08 — Frontend Adjustments (Graph & Community)

## New Graph API Endpoints

The backend now exposes two new endpoints for graph visualization:

### GET /api/v1/graph/data
Returns nodes and edges for visualization.

```javascript
// Frontend fetch
const response = await fetch('/api/v1/graph/data?document=doc.pdf');
const data = await response.json();

// Response format
{
  "nodes": [
    { "id": "Alice", "label": "PERSON", "properties": {} },
    { "id": "Acme Corp", "label": "ORGANIZATION", "properties": {} }
  ],
  "edges": [
    { "source": "Alice", "target": "Acme Corp", "relation": "WORKS_AT" }
  ]
}
```

### GET /api/v1/graph/communities
Returns LLM-generated summaries for communities.

```javascript
// Frontend fetch
const response = await fetch('/api/v1/graph/communities?document=doc.pdf');
const data = await response.json();

// Response format
{
  "communities": [
    {
      "community_id": 1,
      "node_count": 12,
      "edge_count": 8,
      "summary": "This community represents the main actors in the organization..."
    }
  ]
}
```

## Frontend Integration

### Graph Visualization
Use `/api/v1/graph/data` to populate ForceGraph2D or D3.js.

```javascript
// Example with react-force-graph
const response = await fetch(`${API_BASE_URL}/graph/data?document=${docId}`);
const { nodes, edges } = await response.json();

const graphData = {
  nodes: nodes.map(n => ({ id: n.id, name: n.id, group: n.label })),
  links: edges.map(e => ({ source: e.source, target: e.target }))
};
```

### Community Panel
Use `/api/v1/graph/communities` to display summaries in a sidebar or panel.

```javascript
const response = await fetch(`${API_BASE_URL}/graph/communities?document=${docId}`);
const { communities } = await response.json();

// Display as expandable cards
communities.forEach(c => {
  console.log(`Community ${c.community_id}: ${c.summary}`);
});
```

## Updated Extract Response

The `/api/v1/graph/extract` endpoint returns `DocumentProcessResponse`:

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
      "summary": "This community represents the main actors...",
      "stored_in_qdrant": true
    }
  ]
}
```

## Files to Update

| File | Change |
|------|--------|
| `GraphView.jsx` | Add fetch to `/graph/data` and `/graph/communities` |
| State management | Store graph data in context or local state |
| Sidebar/Panel | Render community summaries |

## Summary
- Use `/graph/data` for node/edge visualization
- Use `/graph/communities` for LLM-generated context summaries
- Both endpoints support optional `document` query param for filtering

## See Also
- `FRONTEND_ADJUSTMENTS.md` — Full integration guide (models, inference, templates)
