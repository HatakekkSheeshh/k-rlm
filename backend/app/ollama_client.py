"""
Ollama REST API client.
Endpoints: /api/generate, /api/embeddings, /api/tags, /api/pull
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=httpx.Timeout(settings.ollama_timeout),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()


@traceable(name="ollama_generate", run_type="llm")
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
async def generate(prompt: str, model: str = settings.default_model, system: str | None = None) -> dict:
    """Non-streaming generate - returns response dict with usage info."""
    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    client = get_client()
    resp = await client.post("/api/generate", json=payload)
    resp.raise_for_status()
    raw = resp.json()

    return {**raw, "output": raw.get("response", ""), "usage": {"input_tokens": raw.get("prompt_eval_count", 0), "output_tokens": raw.get("eval_count", 0)}}


async def generate_stream(prompt: str, model: str = settings.default_model, system: str | None = None) -> AsyncIterator[str]:
    """Streaming generate - yields token chunks."""
    payload: dict = {"model": model, "prompt": prompt, "stream": True}
    if system:
        payload["system"] = system

    client = get_client()
    async with client.stream("POST", "/api/generate", json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            yield chunk.get("response", "")
            if chunk.get("done"):
                break


async def list_models() -> list[str]:
    """List models available in Ollama."""
    client = get_client()
    resp = await client.get("/api/tags")
    resp.raise_for_status()
    return [m["name"] for m in resp.json().get("models", [])]


async def pull_model(model: str) -> dict:
    """Pull model from Ollama registry. Returns last status."""
    client = get_client()
    last: dict = {}
    async with client.stream("POST", "/api/pull", json={"name": model}) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if line:
                last = json.loads(line)
    logger.info("pull %s finished: %s", model, last.get("status"))
    return last


async def get_embedding(text: str, model: str = "all-minilm") -> list[float]:
    """Generate embeddings using Ollama. Falls back to hash-based vector on failure."""
    try:
        client = get_client()
        resp = await client.post("/api/embeddings", json={"model": model, "prompt": text})
        resp.raise_for_status()
        embedding = resp.json().get("embedding")
        if embedding:
            return embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}, using fallback.")

    import hashlib
    hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    return [(hash_val >> (i * 8)) % 256 / 255.0 for i in range(384)]
