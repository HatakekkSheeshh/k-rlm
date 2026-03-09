# Backend Changelog & Documentation

All changes to the K-RLM backend are documented in this folder.

## Index

| File | Description |
|------|-------------|
| `01-fastapi-lifespan-fix.md` | Replaced deprecated on_event with lifespan |
| `02-env-config-update.md` | Added missing Neo4j/Qdrant to .env.example |
| `03-json-sanitization.md` | Robust JSON parsing for LLM output |
| `04-chunking-optimization.md` | Fixed batch size and concurrency |
| `05-community-pipeline.md` | Full community detection → summarization → Qdrant pipeline |
| `06-graph-endpoints.md` | New graph data and community endpoints |
| `07-tests.md` | Test suite for all modules |
| `08-frontend-adjustments.md` | What frontend needs to change |
| `09-timeout-concurrency-fix.md` | Timeout increase, sequential processing, per-edge validation |
| `10-rlm-pipeline.md` | RLM pipeline for multi-hop graph reasoning with execution trace |
