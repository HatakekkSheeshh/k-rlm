# Frontend Integration Guide

This document outlines the necessary adjustments for the frontend to properly integrate with the K-RLM backend API.

---

## API Base URL

The frontend should use `VITE_API_BASE_URL` environment variable. If not set, fallback to:
```
http://localhost:8000/api/v1
```

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Service health check |
| `/api/v1/inference` | POST | Run inference |
| `/api/v1/models` | GET | List available & supported models |
| `/api/v1/models/pull` | POST | Pull a model into Ollama |
| `/api/v1/templates` | GET | List prompt templates |
| `/api/v1/graph/extract` | POST | Extract graph entities from document |
| `/api/v1/graph/data` | GET | Get full graph for visualization |
| `/api/v1/graph/communities` | GET | Get community summaries |

---

## Frontend Adjustments Required

### 1. Models Endpoint (`/api/v1/models`)

**Current Issue**: Frontend uses static model list from `constants.js`

**Required Changes**:
- Fetch models from backend instead of using hardcoded list
- Backend response format:
```json
{
  "available": ["phi3:mini", "gemma:7b"],
  "supported": [
    { "tag": "phi3:mini", "label": "Phi-3 Mini" },
    { "tag": "gemma:7b", "label": "Gemma 7B" },
    { "tag": "mistral:7b-instruct-v0.2-q4_0", "label": "Mistral 7B v0.2" }
  ]
}
```

**Frontend Code**:
```javascript
// Fetch available models
const response = await fetch(`${API_BASE_URL}/models`);
const data = await response.json();
// data.available - models pulled in Ollama
// data.supported - curated list with display labels
```

---

### 2. Inference Endpoint (`/api/v1/inference`)

**Request Format**:
```json
{
  "prompt": "Your question here",
  "model": "phi3:mini",
  "strategy": "Standard RAG",
  "system": null,
  "prompt_template": "raw"
}
```

**Response Format**:
```json
{
  "answer": "The generated response...",
  "metrics": {
    "model": "phi3:mini",
    "strategy": "Standard RAG",
    "eval_count": 150,
    "eval_duration": 500000000,
    "latency_s": 1.234
  }
}
```

**Current Frontend Issue**: Frontend expects `result.time` as string (e.g., "1.234s") but backend returns `latency_s` as float.

**Required Changes**:
- Change `result.time` to use `data.metrics.latency_s`
- Format latency: `data.metrics.latency_s + 's'`

---

### 3. Templates Endpoint (`/api/v1/templates`)

**Response Format**:
```json
[
  { "id": "raw", "label": "Raw (No Template)" },
  { "id": "ocr_extraction", "label": "OCR — Price & Expiry Extraction" },
  { "id": "summarise", "label": "Summarise Text" }
]
```

**Current Status**: Already implemented correctly in `ChatTestView.jsx`

---

### 4. Graph Extraction Endpoint (`/api/v1/graph/extract`)

**Request**: Multipart form data
- `file`: File to upload
- `model`: Ollama model (default: "phi3:mini")
- `summarize`: Run community pipeline (default: true)

**Response Format** (`DocumentProcessResponse`):
```json
{
  "filename": "document.pdf",
  "graph": {
    "nodes": [
      { "id": "Entity Name", "label": "PERSON", "properties": {} }
    ],
    "edges": [
      { "source": "Source Entity", "target": "Target Entity", "relation": "RELATES_TO", "properties": {} }
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

**Current Frontend Issue**: In `GraphView.jsx`, the response mapping needs update:
- Response uses `graph.nodes` and `graph.edges` (not `links`)
- Node should use `id` field for label
- Edge uses `source`, `target`, `relation` (not `name`)

**Required Changes in GraphView.jsx**:
```javascript
// Current (needs fix):
const mappedData = {
  nodes: data.graph.nodes.map(n => ({ ...n, name: n.id })),
  links: data.graph.edges.map(e => ({ ...e, source: e.source, target: e.target, name: e.relation }))
};

// Actually this is already correct - ForceGraph2D expects source/target as strings
```

---

### 5. Health Endpoint (`/api/v1/health`)

**Response Format**:
```json
{
  "status": "ok",
  "ollama_reachable": true
}
```

**Usage**: Check if Ollama is available before making inference requests.

---

### 6. Model Pull Endpoint (`/api/v1/models/pull`)

**Request Format**:
```json
{
  "tag": "phi3:mini"
}
```

**Response Format**:
```json
{
  "tag": "phi3:mini",
  "status": "success"
}
```

**Note**: Pulling a model takes several minutes. Consider adding progress indication in UI.

---

### 7. Graph Data Endpoint (`/api/v1/graph/data`)

**Query Params:**
- `document` (optional): Filter by document name

**Response Format:**
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

Use this for ForceGraph2D visualization.

---

### 8. Graph Communities Endpoint (`/api/v1/graph/communities`)

**Query Params:**
- `document` (required): Document name
- `run_pipeline` (optional): Run summarization if not exists
- `model` (optional): Model to use

**Response Format:**
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

Use this for community panel/sidebar display.

---

## Constants.js Updates

Update `frontend/src/data/constants.js` to fetch from API:

```javascript
// Instead of static arrays, fetch from backend
export async function fetchModels() {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/models`);
  const data = await response.json();
  return data.supported; // or data.available for pulled models
}

// For initial load, use supported list
export const MODELS = []; // Will be populated from API

export const STRATEGIES = [
  'Standard RAG',
  'Graph Traversal',
  'Recursive RLM (Decomp)',
];

export const DATASETS = [
  'Medical (PubMed)',
  'Finance (SEC)',
  'General (Wiki)',
];
```

---

## Environment Variables

Frontend should define:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Error Handling

Handle these common HTTP status codes:

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 400 | Bad Request | Validate input |
| 422 | Validation Error | Check request body |
| 502 | Bad Gateway | Ollama/Service unavailable |
| 500 | Internal Server Error | Show error message |

---

## Testing Checklist

- [ ] Verify `/api/v1/health` returns correct status
- [ ] Verify `/api/v1/models` returns available and supported models
- [ ] Verify `/api/v1/inference` works with different templates
- [ ] Verify `/api/v1/graph/extract` uploads and processes files
- [ ] Verify `/api/v1/graph/data` returns nodes and edges
- [ ] Verify `/api/v1/graph/communities` returns community data
- [ ] Verify error handling for failed requests
- [ ] Verify latency display format

---

## Summary of Changes

| File | Change Required |
|------|-----------------|
| `constants.js` | Replace static MODELS with API fetch |
| `PlaygroundView.jsx` | Update latency formatting from `metrics.latency_s` |
| `GraphView.jsx` | Fetch from `/graph/data`, handle `community_summaries` in extract response |
| `EvalView.jsx` | Optionally fetch real metrics from backend |
| New: Community Panel | Fetch from `/graph/communities`, display summaries |

---

## Backend Is Ready

The backend is now fully functional with:
- Modern FastAPI lifespan management (no deprecated `on_event`)
- Complete environment configuration
- Proper error handling
- All required endpoints implemented
