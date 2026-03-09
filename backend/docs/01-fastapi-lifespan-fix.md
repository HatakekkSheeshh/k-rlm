# 01 — FastAPI Lifespan Fix

## Problem
`app/main.py` used `@app.on_event("startup")` and `@app.on_event("shutdown")` which are deprecated since FastAPI 0.109+.

## Fix
Replaced with `lifespan` async context manager.

## Before
```python
@app.on_event("startup")
async def startup() -> None:
    await neo4j_client.connect()
    await qdrant_client.connect()

@app.on_event("shutdown")
async def shutdown() -> None:
    await close_client()
    await neo4j_client.close()
    await qdrant_client.close()
```

## After
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.neo4j_client import neo4j_client
    from app.services.qdrant_client import qdrant_client
    await neo4j_client.connect()
    await qdrant_client.connect()
    yield
    await close_client()
    await neo4j_client.close()
    await qdrant_client.close()

app = FastAPI(..., lifespan=lifespan)
```

## Files Changed
- `app/main.py`
