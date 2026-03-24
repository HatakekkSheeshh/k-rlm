# K-RLM: Knowledge Graph + Recursive Language Model

Full-stack research platform with Knowledge Graph extraction and RLM-based inference.

## Quick Start

```bash
cp backend/.env.example backend/.env
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
4. **RAPTOR Trees** → Hierarchical document retrieval with multi-level abstraction

## Retrieval Strategies

- **Standard RAG**: Direct LLM generation
- **Graph Traversal**: Entity-based retrieval from Neo4j
- **Recursive RLM**: Query decomposition + graph retrieval
- **RAPTOR (Hierarchical)**: Multi-level tree retrieval (new!)

## Tech Stack

- **Frontend**: React, ForceGraph2D
- **Backend**: FastAPI, Python 3.11
- **LLM**: Ollama (phi3:mini)
- **Graph DB**: Neo4j
- **Vector DB**: Qdrant (cloud)
- **OCR**: Kreuzberg (PaddleOCR)

## API Endpoints

| Endpoint                    | Method | Description                         |
| --------------------------- | ------ | ----------------------------------- |
| `/api/v1/health`            | GET    | Health check                        |
| `/api/v1/inference`         | POST   | Run inference (Standard RAG or RLM) |
| `/api/v1/models`            | GET    | List Ollama models                  |
| `/api/v1/models/pull`       | POST   | Pull model                          |
| `/api/v1/graph/extract`     | POST   | Upload document, extract KG         |
| `/api/v1/graph/data`        | GET    | Get graph for visualization         |
| `/api/v1/graph/communities` | GET    | Get community summaries             |
| `/api/v1/graph/raptor/build`| POST   | Build RAPTOR hierarchical tree      |
| `/api/v1/graph/raptor/stats`| GET    | Get RAPTOR tree statistics          |

## Documentation

- [Architecture Flows](docs/Flows.md)
- [Backend Docs](backend/README.md)
- [RAPTOR Usage Guide](backend/RAPTOR_USAGE.md)
