# K-RLM: Knowledge Graph + Recursive Language Model

Full-stack research platform with Knowledge Graph extraction and RLM-based inference.

## Quick Start

```bash
docker compose up -d
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- Qdrant Dashboard: http://localhost:6333

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────►│   Backend   │────►│   Ollama    │
│   (React)   │     │  (FastAPI) │     │   (phi3)    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │  Neo4j  │  │ Qdrant  │  │  Local  │
        │ (Graph) │  │ (Vector)│  │   OCR   │
        └─────────┘  └─────────┘  └─────────┘
```

## Key Features

1. **Document Upload** → OCR (Kreuzberg) → Chunk → LLM → KG (Neo4j)
2. **Community Detection** → LLM Summarization → Qdrant (embeddings)
3. **RLM Inference** → Multi-hop reasoning over knowledge graph

## Tech Stack

- **Frontend**: React, ForceGraph2D
- **Backend**: FastAPI, Python 3.11
- **LLM**: Ollama (phi3:mini)
- **Graph DB**: Neo4j
- **Vector DB**: Qdrant (cloud)
- **OCR**: Kreuzberg (PaddleOCR)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/inference` | POST | Run inference (Standard/RLM) |
| `/api/v1/graph/extract` | POST | Upload document, extract KG |
| `/api/v1/graph/data` | GET | Get graph for visualization |
| `/api/v1/graph/communities` | GET | Get community summaries |

## Documentation

- [Architecture Flows](docs/Flows.md)
- [Backend Docs](backend/docs/)
