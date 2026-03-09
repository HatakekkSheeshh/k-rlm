# 09 — Timeout & Concurrency Fix

## Problem
- Ollama HTTP 500 errors with "2m0s" duration — httpx timeout (120s) too short
- Concurrent requests overwhelming Ollama (multiple `/api/generate` calls at same time)
- JSON "Extra data" error — LLM returns multiple JSON objects
- Pydantic validation fails entire batch when one edge is malformed

## Fixes

### 1. Timeout Increased (config.py)
```python
# Before: 120 seconds
ollama_timeout: int = 120

# After: 300 seconds (5 minutes)
ollama_timeout: int = 300
```

### 2. Sequential Processing (document_processor.py)
```python
# Before: asyncio.gather fired all batches simultaneously
tasks = [self._extract_from_batch(batch, model) for batch in batches]
results = await asyncio.gather(*tasks)

# After: sequential loop with progress logging
for i, batch in enumerate(batches, 1):
    logger.info(f"Processing batch {i}/{len(batches)}...")
    result = await self._extract_from_batch(batch, model)
```

### 3. JSON Sanitization Improved
Added handling for "Extra data" error (multiple JSON objects):
```python
except json.JSONDecodeError as e:
    if "Extra data" in str(e):
        first_end = e.pos if e.pos else text.find('}')
        if first_end > 0:
            candidate = text[:first_end+1]
            return json.loads(candidate, strict=False)
```

### 4. Per-Edge Validation
Instead of failing entire batch on malformed edge, now validates individually:
```python
for edge_data in graph_data.get("edges", []):
    source = edge_data.get("source")
    target = edge_data.get("target")
    relation = edge_data.get("relation")
    if source and target and relation:
        valid_edges.append(GraphEdge(...))
    else:
        logger.warning(f"Skipping invalid edge: {edge_data}")
```

Also validates nodes:
```python
if isinstance(node_data, dict) and node_data.get("id") and node_data.get("label"):
    valid_nodes.append(GraphNode(...))
```

## Files Changed
- `app/config.py` — timeout 120 → 300
- `app/services/document_processor.py` — sequential loop, improved sanitization, per-item validation
