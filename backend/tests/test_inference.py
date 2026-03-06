"""
tests/test_inference.py — integration-style tests for /api/v1/inference.
Requires Ollama to be running (use docker compose up).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_inference_missing_prompt(client):
    """Empty prompt should return 422."""
    resp = await client.post("/api/v1/inference", json={"prompt": "", "model": "phi3:mini"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ollama_reachable" in data
