# 02 — Environment Config Update

## Problem
`.env.example` was missing required Neo4j and Qdrant variables. New developers copying `.env.example` would get startup errors.

## Fix
Added missing variables to `.env.example`.

## Added Variables
```ini
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Qdrant
QDRANT_URL=http://qdrant:6333
# QDRANT_API_KEY=your_key_here
```

## Qdrant Cloud
If using Qdrant Cloud instead of local Docker, set:
```ini
QDRANT_URL=https://<cluster-id>.cloud.qdrant.io
QDRANT_API_KEY=<your-api-key>
```

## Files Changed
- `.env.example`
- `.env` (updated QDRANT_URL to cloud endpoint)
