# 10 — RLM Pipeline Implementation

## Overview
Implemented the Recursive Language Model (RLM) pipeline for multi-hop reasoning over the knowledge graph.

## When Used
The RLM pipeline activates when the user selects:
- **"Recursive RLM (Decomp)"** strategy
- **"Graph Traversal"** strategy

Standard RAG uses simple prompt → Ollama → response (no graph traversal).

## Pipeline Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│ 1. DECOMPOSE (split)                │
│    LLM breaks query into 2-4        │
│    sub-questions                    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. RETRIEVE (per sub-question)      │
│    Search Neo4j for matching        │
│    entities using keywords          │
│    Extract nodes + edges            │
└─────────────────────────────────────┘
    │
    ▼ (for each sub-question)
┌─────────────────────────────────────┐
│ 3. RESOLVE (synthesize)             │
│    Combine all retrieved context    │
│    + final LLM synthesis           │
└─────────────────────────────────────┘
    │
    ▼
Final Answer + Execution Trace
```

## Backend Changes

### `app/schemas.py`
Added:
- `ExecutionStep` model (id, type, text, details)
- `trace` field in `InferenceResponse`

### `app/routers/inference.py`
Added:
- `_run_rlm_pipeline()` — orchestrates decompose → retrieve → synthesize
- `_extract_sub_questions()` — parses LLM JSON output
- Updated `run_inference()` to use RLM for Graph Traversal / RLM strategies

### `app/services/neo4j_client.py`
Added:
- `search_entities(query, limit)` — keyword-based entity search in Neo4j

## Frontend Changes

### `PlaygroundView.jsx`
- Now stores `traceSteps` from backend response
- Extracts `hops` and `nodesUsed` from trace data
- Falls back to static `DECOMPOSITION_STEPS` for non-RLM strategies

### `StepCard.jsx`
- Color-coded by step type:
  - **split** (purple) — query decomposition
  - **retrieve** (blue) — graph entity retrieval
  - **reason** (amber) — context synthesis
  - **resolve** (green) — final answer
- Shows details accordion with sub-questions, entities, etc.

## API Response Example

```json
{
  "answer": "Based on the knowledge graph...",
  "metrics": {
    "model": "phi3:mini",
    "strategy": "Recursive RLM (Decomp)",
    "eval_count": 150,
    "latency_s": 12.345
  },
  "trace": [
    {
      "id": 1,
      "type": "split",
      "text": "Analyzed the complex query into 3 sub-question(s).",
      "details": {
        "sub_questions": [
          "What is Mao Zedong's policy?",
          "How did Cuba respond?",
          "What relations exist?"
        ]
      }
    },
    {
      "id": 2,
      "type": "retrieve",
      "text": "Retrieved 5 entities for: What is Mao Zedong's...",
      "details": {
        "sub_question": "What is Mao Zedong's policy?",
        "entities": ["Mao Zedong", "Deng Xiaoping", "Cuba"],
        "node_count": 5
      }
    },
    {
      "id": 3,
      "type": "resolve",
      "text": "Generated final grounded answer utilizing multi-hop reasoning.",
      "details": {
        "context_used": 3,
        "sub_questions_answered": 3
      }
    }
  ]
}
```

## Logging
The RLM pipeline logs detailed progress to the backend container logs:

```
krlm-backend | INFO | app.routers.inference | === RLM PIPELINE START ===
krlm-backend | INFO | app.routers.inference | Step 1: Decomposing query into sub-questions...
krlm-backend | INFO | app.routers.inference | Decomposition raw response: ["What is Mao Zedong's policy?", "How did Cuba respond?"]
krlm-backend | INFO | app.routers.inference | Extracted sub-questions: ["What is Mao Zedong's policy?", "How did Cuba respond?"]
krlm-backend | INFO | app.routers.inference | Step 2: Retrieving entities for 2 sub-questions...
krlm-backend | INFO | app.routers.inference |   Processing sub-question 1/2: What is Mao Zedong's policy?...
krlm-backend | INFO | app.routers.inference |     Neo4j returned 3 nodes, 2 edges
krlm-backend | INFO | app.routers.inference |     Entities: ['Mao Zedong', 'Deng Xiaoping', 'Cuba']
krlm-backend | INFO | app.routers.inference | Step 3: Synthesizing final answer (context length: 2 chunks)
krlm-backend | INFO | app.routers.inference | === RLM PIPELINE COMPLETE ===
```

Run `docker compose logs -f backend` to watch the RLM pipeline execute in real-time.

## Files Changed
- `app/schemas.py` — Added ExecutionStep, trace field
- `app/routers/inference.py` — Added _run_rlm_pipeline, _extract_sub_questions, logging
- `app/services/neo4j_client.py` — Added search_entities method
- `frontend/src/components/views/PlaygroundView.jsx` — Trace integration
- `frontend/src/components/ui/StepCard.jsx` — Color-coded steps, details accordion
