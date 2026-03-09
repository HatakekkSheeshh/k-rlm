# K-RLM Backend

Backend application for graph extraction, inference and evaluations.
Built using FastAPI.

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose (for full stack)

### Local Development

1. Install dependencies:

```bash
cd backend
poetry install
```

2. Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

3. Start services with Docker Compose:

```bash
docker compose up -d
```

4. Run the backend:

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Access API docs at: http://localhost:8000/docs

## Environment Variables

| Variable          | Description               | Default                                              |
| ----------------- | ------------------------- | ---------------------------------------------------- |
| `OLLAMA_BASE_URL` | Ollama service URL        | `http://ollama:11434`                                |
| `OLLAMA_TIMEOUT`  | Request timeout (seconds) | 300                                                  |
| `DEFAULT_MODEL`   | Default Ollama model      | `phi3:mini`                                          |
| `API_PREFIX`      | API route prefix          | `/api/v1`                                            |
| `CORS_ORIGINS`    | Allowed CORS origins      | `["http://localhost:5173", "http://localhost:3000"]` |
| `NEO4J_URI`       | Neo4j connection URI      | Required                                             |
| `NEO4J_USER`      | Neo4j username            | Required                                             |
| `NEO4J_PASSWORD`  | Neo4j password            | Required                                             |
| `QDRANT_URL`      | Qdrant URL                | Required                                             |
| `QDRANT_API_KEY`  | Qdrant API key            | Optional                                             |

## API Endpoints

### Health Check

```
GET /api/v1/health
```

### Inference

```
POST /api/v1/inference
```

Request:

```json
{
  "prompt": "Your question",
  "model": "phi3:mini",
  "strategy": "Standard RAG",
  "prompt_template": "raw"
}
```

### Models

```
GET /api/v1/models          # List available & supported models
POST /api/v1/models/pull    # Pull a model into Ollama
```

### Templates

```
GET /api/v1/templates       # List prompt templates
```

### Graph Extraction

```text
POST /api/v1/graph/extract     # Upload document and extract entities
GET  /api/v1/graph/data        # Get graph for visualization
GET  /api/v1/graph/communities # Get community summaries
```

## Project Structure

```text
app/
├── main.py              # FastAPI app factory
├── config.py            # Settings management
├── schemas.py           # Pydantic models
├── prompts.py           # Prompt template registry
├── ollama_client.py     # Ollama API wrapper
├── routers/
│   ├── health.py        # Health endpoints
│   ├── inference.py     # Inference endpoints
│   ├── models.py        # Model management
│   └── graph.py         # Graph extraction
└── services/
    ├── community_summarizer.py # Generates community summaries
    ├── document_processor.py   # Document OCR & entity extraction
    ├── neo4j_client.py         # Neo4j database client
    └── qdrant_client.py        # Qdrant vector DB client
```

## Testing

Run tests:

```bash
poetry run pytest
```

Run with coverage:

```bash
poetry run pytest --cov=app
```

## Dependencies

- **FastAPI**: Web framework
- **httpx**: Async HTTP client for Ollama
- **pydantic**: Data validation
- **tenacity**: Retry logic
- **langsmith**: Tracing/telemetry
- **kreuzberg**: Document OCR
- **neo4j**: Graph database
- **qdrant-client**: Vector database
