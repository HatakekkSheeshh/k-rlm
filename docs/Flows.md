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
[SLM Entity Extraction] ──► phi3:mini extracts nodes + edges
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
[SLM Summarization] ──► Generate community summaries
       │
       ▼
[Qdrant] ──► Store embeddings + summaries
```

## RAPTOR Tree Building Flow

```
[Document Upload]
       │
       ▼
[Kreuzberg OCR] ──► Extract text from PDF/image
       │
       ▼
[Chunk Text] ──► Split into ~400 word chunks (Level 0)
       │
       ▼
[Embed Chunks] ──► Generate embeddings for all chunks
       │
       ▼
[Store Level 0] ──► Base chunks as leaf nodes
       │
       ▼
[Cluster Chunks] ──► K-means clustering of embeddings
       │
       ▼
[Summarize Clusters] ──► SLM creates summaries (Level 1)
       │
       ▼
[Embed Summaries] ──► Generate embeddings for summaries
       │
       ▼
[Recursive Clustering] ──► Repeat until convergence (Level 2, 3, ...)
       │
       ▼
[RAPTOR Tree Complete] ──► Hierarchical tree with multi-level abstractions
       │
       ▼
[Optional: Store in Qdrant] ──► Persist tree for later retrieval
```

## Retrieval Strategy Comparison

### 1. Standard RAG
- **Process**: Direct LLM generation with optional prompt template
- **Use Case**: Simple queries, no context needed
- **Latency**: Fastest (~1-2s)

### 2. Graph Traversal / Recursive RLM
- **Process**: 
  1. Decompose query into sub-questions
  2. Retrieve entities from Neo4j knowledge graph
  3. Synthesize answer from graph context
- **Use Case**: Complex queries requiring entity relationships
- **Latency**: Medium (~5-10s)
- **Strength**: Multi-hop reasoning over entities

### 3. RAPTOR (Hierarchical)
- **Process**:
  1. Retrieve relevant nodes from tree across multiple levels
  2. High-level summaries provide context
  3. Low-level chunks provide specific details
  4. Synthesize answer from hierarchical context
- **Use Case**: Document QA requiring both overview and details
- **Latency**: Medium (~5-10s)
- **Strength**: Multi-level abstraction, captures both macro and micro information

## RLM Inference Flow

```
[User Question]
       │
       ▼
[Strategy Check]
       │
       ├─► Standard RAG ──► Direct SLM generation
       │
       ├─► Recursive RLM / Graph Traversal
       │      │
       │      ▼
       │   [Decompose Query] ──► Sub-questions
       │      │
       │      ▼
       │   [Retrieve from Neo4j]
       │      │
       │      ▼
       │   [Synthesize Answer]
       │
       └─► RAPTOR (Hierarchical)
              │
              ▼
       [Check Tree Exists]
              │
              ▼
       [Retrieve Multi-Level Nodes]
              │
              ├─► Level 2+: High-level summaries (context)
              ├─► Level 1: Mid-level summaries (themes)
              └─► Level 0: Specific chunks (details)
              │
              ▼
       [Hierarchical Context Assembly]
              │
              ▼
       [Synthesize Answer]
```
