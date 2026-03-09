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

## RLM Inference Flow

```
[User Question]
       │
       ▼
[Strategy Check]
       │
       ├─► Standard RAG ──► Direct SLM generation
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
