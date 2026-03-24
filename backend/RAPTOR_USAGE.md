# RAPTOR Integration Guide

## Overview

RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) is now integrated into K-RLM, providing hierarchical document retrieval alongside your existing graph-based and RLM strategies.

## Architecture

RAPTOR builds a **hierarchical tree** with multiple abstraction levels:

```
         Level 2: Global Summary
              /        |         \
    Level 1: Mid-level Summaries
        /  |  \            /  |  \
   Level 0: Base Chunks (400 words each)
```

### Key Features

- **Multi-level Retrieval**: Searches across all tree levels simultaneously
- **Hierarchical Context**: Combines high-level overviews with specific details
- **Automatic Clustering**: Uses K-means with silhouette scoring to find optimal clusters
- **Recursive Summarization**: Each level summarizes clusters from the level below

## Installation

The RAPTOR service requires additional dependencies:

```bash
cd backend
poetry add numpy scikit-learn
# or
poetry install
```

## API Endpoints

### 1. Build RAPTOR Tree

Build a hierarchical tree from a document:

```bash
POST /api/v1/graph/raptor/build

Form Data:
- file: <document file> (PDF, image, etc.)
- model: "phi3:mini" (optional, default)
- chunk_size: 400 (optional, words per chunk)
- max_levels: 3 (optional, max tree depth)
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/graph/raptor/build \
  -F "file=@research_paper.pdf" \
  -F "model=phi3:mini" \
  -F "chunk_size=400" \
  -F "max_levels=3"
```

**Response:**

```json
{
  "status": "success",
  "document": "research_paper.pdf",
  "message": "RAPTOR tree built with 3 levels and 47 nodes",
  "stats": {
    "document": "research_paper.pdf",
    "levels": 3,
    "total_nodes": 47,
    "level_breakdown": [
      {"level": 0, "nodes": 30},
      {"level": 1, "nodes": 12},
      {"level": 2, "nodes": 5}
    ]
  }
}
```

### 2. Get RAPTOR Tree Stats

Check if a tree exists and view statistics:

```bash
GET /api/v1/graph/raptor/stats?document=research_paper.pdf
```

**Response:**

```json
{
  "document": "research_paper.pdf",
  "total_nodes": 47,
  "levels": 3,
  "level_breakdown": [
    {"level": 0, "nodes": 30},
    {"level": 1, "nodes": 12},
    {"level": 2, "nodes": 5}
  ]
}
```

### 3. Query with RAPTOR Strategy

Use RAPTOR for inference by specifying the strategy:

```bash
POST /api/v1/inference

Body:
{
  "prompt": "What are the main conclusions of the research?",
  "model": "phi3:mini",
  "strategy": "RAPTOR (Hierarchical)"
}
```

**Response:**

```json
{
  "answer": "The research concludes that...",
  "metrics": {
    "model": "phi3:mini",
    "strategy": "RAPTOR (Hierarchical)",
    "latency_s": 6.234
  },
  "trace": [
    {
      "id": 1,
      "type": "split",
      "text": "Accessing RAPTOR tree with 3 levels and 47 nodes",
      "details": {"levels": 3, "total_nodes": 47}
    },
    {
      "id": 2,
      "type": "retrieve",
      "text": "Retrieved 5 relevant nodes from 3 tree levels",
      "details": {
        "total_contexts": 5,
        "levels_used": [0, 1, 2],
        "top_similarities": ["0.892", "0.847", "0.821"]
      }
    },
    {
      "id": 3,
      "type": "reason",
      "text": "Synthesizing answer from hierarchical context (3428 chars)",
      "details": {"context_length": 3428}
    },
    {
      "id": 4,
      "type": "resolve",
      "text": "Generated answer using RAPTOR hierarchical retrieval",
      "details": {"levels_used": [0, 1, 2], "contexts_used": 5}
    }
  ]
}
```

## Strategy Comparison

### When to Use Each Strategy

| Strategy | Best For | Latency | Strengths |
|----------|----------|---------|-----------|
| **Standard RAG** | Simple queries, general knowledge | ~1-2s | Fast, no preprocessing |
| **Graph Traversal** | Entity relationships, multi-hop reasoning | ~5-10s | Entity-centric, relationship tracking |
| **Recursive RLM** | Complex queries with sub-problems | ~5-10s | Query decomposition, focused retrieval |
| **RAPTOR (Hierarchical)** | Document QA, need both overview + details | ~5-10s | Multi-level context, comprehensive answers |

### Example Use Cases

**RAPTOR is ideal for:**
- "Summarize the key findings and their implications"
- "What methodology was used and what were the results?"
- "Explain the background and main contributions"
- Questions requiring both high-level understanding and specific details

**Graph Traversal is ideal for:**
- "How are Company A and Company B related?"
- "What entities are connected to this person?"
- "Show me the path from concept X to concept Y"

## Frontend Integration

The frontend now includes RAPTOR in the strategy selector:

```javascript
// frontend/src/data/constants.js
export const STRATEGIES = [
  'Standard RAG',
  'Graph Traversal',
  'Recursive RLM',
  'RAPTOR (Hierarchical)'  // ← New option
];
```

Users can select "RAPTOR (Hierarchical)" from the dropdown to use hierarchical retrieval.

## Workflow

### Complete Pipeline

1. **Build Tree** (one-time per document):
   ```bash
   POST /api/v1/graph/raptor/build
   # Upload document, builds hierarchical tree
   ```

2. **Query** (multiple times):
   ```bash
   POST /api/v1/inference
   # Set strategy: "RAPTOR (Hierarchical)"
   # Ask questions about the document
   ```

### Example Python Client

```python
import httpx

# 1. Build tree
with open("document.pdf", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/graph/raptor/build",
        files={"file": f},
        data={"model": "phi3:mini", "max_levels": 3}
    )
    print(response.json())

# 2. Query
response = httpx.post(
    "http://localhost:8000/api/v1/inference",
    json={
        "prompt": "What are the main findings?",
        "model": "phi3:mini",
        "strategy": "RAPTOR (Hierarchical)"
    }
)
print(response.json()["answer"])
```

## Configuration

### RAPTOR Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 400 | Words per base chunk (Level 0) |
| `max_clusters_per_level` | 5 | Max clusters when grouping nodes |
| `max_levels` | 3 | Maximum tree depth |
| `model` | "phi3:mini" | LLM for summarization |

### Tuning Guidelines

- **Larger documents**: Increase `chunk_size` and `max_levels`
- **More granular retrieval**: Decrease `chunk_size`, increase `max_clusters_per_level`
- **Faster building**: Decrease `max_levels`, increase `chunk_size`

## Technical Details

### Tree Building Algorithm

1. **Chunking**: Split document into ~400 word chunks
2. **Embedding**: Generate embeddings for all chunks (Level 0)
3. **Clustering**: Use K-means with silhouette score optimization
4. **Summarization**: LLM summarizes each cluster
5. **Recursion**: Repeat steps 2-4 until convergence or max level reached

### Retrieval Algorithm

1. **Query Embedding**: Embed user query
2. **Multi-level Search**: Calculate cosine similarity across all levels
3. **Top-K Selection**: Retrieve top-K most similar nodes
4. **Context Assembly**: Order by level (high to low abstraction)
5. **LLM Synthesis**: Generate answer from hierarchical context

### Storage

- **In-Memory**: Trees cached in `_raptor_trees` dictionary (current implementation)
- **Persistent** (optional): Can store in Qdrant using `insert_raptor_nodes()`

## Troubleshooting

### "No RAPTOR tree found"

**Problem**: Query returns "No RAPTOR tree found for document: X"

**Solution**: Build the tree first using `/api/v1/graph/raptor/build`

### Low Quality Summaries

**Problem**: Summaries are too generic or miss key details

**Solution**: 
- Decrease `chunk_size` for more granular base chunks
- Try a different model (e.g., larger context window)
- Increase `max_levels` for more abstraction layers

### Out of Memory

**Problem**: Tree building fails with memory error

**Solution**:
- Decrease `chunk_size` to create fewer base chunks
- Decrease `max_levels` to limit tree depth
- Process smaller documents or split into sections

## Next Steps

1. **Install dependencies**: `poetry install` in backend/
2. **Build a tree**: Upload a document via `/graph/raptor/build`
3. **Test retrieval**: Query with strategy "RAPTOR (Hierarchical)"
4. **Tune parameters**: Adjust chunk_size and max_levels for your use case

## References

- Original RAPTOR Paper: [arXiv:2401.18059](https://arxiv.org/abs/2401.18059)
- K-RLM Documentation: [docs/Flows.md](../docs/Flows.md)
