# 05 — Community Pipeline

## Overview
Full pipeline: entity/relation extraction → Neo4j storage → community detection → LLM summarization → embedding → Qdrant storage.

## Pipeline Flow
```
Document
  → OCR/text extraction (Kreuzberg)
  → Chunking (300 words)
  → LLM entity-relation extraction (Ollama)
  → Store nodes/edges in Neo4j
  → Detect communities (label grouping + connected components)
  → Summarize each community via LLM
  → Generate embedding (Ollama nomic-embed-text)
  → Store summary + vector in Qdrant
```

## Community Detection (`neo4j_client.py`)
No Neo4j GDS plugin required. Uses two strategies:

### 1. Label-Based Grouping
Groups nodes by their Neo4j label (e.g., PERSON, ORGANIZATION).

### 2. Connected Components
Finds connected subgraphs within each label group using Cypher path traversal.

```python
async def detect_communities(document_name: str) -> list[Community]:
    # Get all labels for document
    # For each label, find connected components
    # Return list of Community objects
```

### Community Class
```python
class Community:
    def __init__(self, community_id, nodes, edges):
        self.id = community_id
        self.nodes = nodes
        self.edges = edges

    def context_text(self) -> str:
        # Returns formatted text for LLM summarization
```

## Community Summarization (`community_summarizer.py`)

### `summarize_community(community, model)`
Sends community context to LLM with prompt requesting a concise summary.

### `store_community_summary(community, summary, document_name)`
1. Generates embedding via `get_embedding()`
2. Creates deterministic UUID from `community_id + document_name`
3. Upserts into Qdrant with metadata payload

### `run_community_pipeline(document_name, model)`
Orchestrates the full flow: detect → summarize → store.

## Embedding (`ollama_client.py`)
```python
async def get_embedding(text, model="nomic-embed-text") -> list[float]:
    # Try Ollama /api/embed
    # Fallback: SHA-256 hash-based pseudo-vector (384 dims)
```

## Qdrant Storage (`qdrant_client.py`)
- Collection: `community_summaries`
- Vector size: 384
- Payload: `summary_text`, `community_id`, `document`, metadata

## Files Changed
- `app/services/neo4j_client.py` — Community class, detect_communities, get_full_graph
- `app/services/community_summarizer.py` — New file
- `app/ollama_client.py` — get_embedding with fallback
- `app/services/qdrant_client.py` — insert_summary
