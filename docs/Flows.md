# K-RLM Architecture Flows

## Document Processing Flow

```
[Document Upload]
       │
       ▼
[Kreuzberg OCR] ──► Extract text from PDF/image
       │
       ▼
[Chunk Text] ──► Split into ~300 word chunks
       │
       ▼
[LLM Entity Extraction] ──► phi3:mini extracts nodes + edges
       │
       ▼
[sanitize_json] ──► Parse & fix malformed JSON
       │
       ▼
[Neo4j] ──► Store entities & relationships
       │
       ▼
[Community Detection] ──► Group entities by label
       │
       ▼
[LLM Summarization] ──► Generate community summaries
       │
       ▼
[Qdrant] ──► Store embeddings + summaries
```

## RLM Inference Flow

```
[User Question]
       │
       ▼
[Strategy Check]
       │
       ├─► Standard RAG ──► Direct LLM generation
       │
       └─► Recursive RLM / Graph Traversal
              │
              ▼
       [Generate partial answer]
              │
              ▼
       [Check: needs more info?] ──► Pattern matching on response
              │
              ├─► YES ──► [Retrieve from Neo4j] ──► [Add to context] ──► LOOP
              │
              └─► NO ──► [Generate final answer]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/inference` | POST | Run inference (Standard RAG or RLM) |
| `/api/v1/models` | GET | List Ollama models |
| `/api/v1/models/pull` | POST | Pull model |
| `/api/v1/graph/extract` | POST | Upload document, extract KG |
| `/api/v1/graph/data` | GET | Get graph for visualization |
| `/api/v1/graph/communities` | GET | Get community summaries |
