# 04 — Chunking Optimization

## Problem
Original chunking used 20 words per chunk, producing ~5600 batches for a single document. This caused:
- Ollama overload and `ReadTimeout` errors
- `aborting completion request due to client closing the connection`
- Cascading retry failures

## Fix
Tuned chunk size, concurrency, and retry parameters.

## Changes

### Chunk Size
| Version | Words/Chunk | Batches (typical doc) |
|---------|-------------|----------------------|
| Original | 20 | ~5,600 |
| v2 | 2,000 | ~10-20 |
| v3 (final) | 300 | ~50-100 |

300 words balances context quality with LLM processing time.

### Concurrency
| Version | max_concurrent | Mode |
|---------|---------------|------|
| Original | 5 | Parallel via asyncio.gather |
| v2 | 2 | Parallel via asyncio.gather |
| v3 (final) | 1 | Sequential for loop |

**Important:** Even with `max_concurrent=1`, `asyncio.gather` was firing all tasks simultaneously.
The fix replaced `asyncio.gather` with a sequential `for` loop:
```python
for i, batch in enumerate(batches, 1):
    logger.info(f"Processing batch {i}/{len(batches)}...")
    result = await self._extract_from_batch(batch, model)
```
This ensures only one batch is processed at a time.

### Timeout
Also increased httpx timeout from 120s to 300s (see `09-timeout-concurrency-fix.md`).

### Retry
| Version | Attempts | Wait |
|---------|----------|------|
| Original | 3 | exponential 4-10s |
| Final | 2 | exponential 2-5s |

Fewer retries prevent timeout cascading.

## Files Changed
- `app/services/document_processor.py`
