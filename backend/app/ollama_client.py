"""
app/ollama_client.py — async HTTP client wrapper for Ollama REST API.

Endpoints used:
  POST /api/generate      → single-turn text generation
  GET  /api/tags          → list available (pulled) models
  POST /api/pull          → pull a model (streaming, we consume until done)
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Shared async client (reuse across requests) ──────────────────────────────
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


# ─── API helpers ──────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate(
    prompt: str,
    model:  str = settings.default_model,
    system: str | None = None,
) -> dict:
    """
    Non-streaming generate — returns full response as a dict.
    Keys: model, created_at, response, done, eval_count, eval_duration …
    """
    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    client = get_client()
    resp = await client.post("/api/generate", json=payload)
    resp.raise_for_status()
    return resp.json()


async def generate_stream(
    prompt: str,
    model:  str = settings.default_model,
    system: str | None = None,
) -> AsyncIterator[str]:
    """
    Streaming generate — yields token chunks as they arrive.
    """
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
    """Return names of models already pulled into Ollama."""
    client = get_client()
    resp = await client.get("/api/tags")
    resp.raise_for_status()
    data = resp.json()
    return [m["name"] for m in data.get("models", [])]


async def pull_model(model: str) -> dict:
    """
    Pull a model from Ollama registry.
    Consumes the streaming response and returns the last status message.
    """
    client = get_client()
    last: dict = {}
    async with client.stream("POST", "/api/pull", json={"name": model}) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if line:
                last = json.loads(line)
    logger.info("pull %s finished: %s", model, last.get("status"))
    return last
