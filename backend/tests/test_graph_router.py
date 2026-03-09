"""
tests/test_graph_router.py — Tests for graph extraction endpoints.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestGraphDataEndpoint:
    """Tests for GET /api/v1/graph/data."""

    @pytest.mark.asyncio
    async def test_get_graph_data_empty(self, client):
        """Test graph data returns empty when no data."""
        with patch("app.routers.graph.neo4j_client") as mock_neo4j:
            mock_neo4j.get_full_graph = AsyncMock(return_value={"nodes": [], "edges": []})
            resp = await client.get("/api/v1/graph/data")
            assert resp.status_code == 200
            data = resp.json()
            assert data["nodes"] == []
            assert data["edges"] == []

    @pytest.mark.asyncio
    async def test_get_graph_data_with_document(self, client):
        """Test graph data filtered by document."""
        mock_data = {
            "nodes": [{"id": "Alice", "label": "PERSON", "properties": {}}],
            "edges": [{"source": "Alice", "target": "Bob", "relation": "KNOWS"}],
        }
        with patch("app.routers.graph.neo4j_client") as mock_neo4j:
            mock_neo4j.get_full_graph = AsyncMock(return_value=mock_data)
            resp = await client.get("/api/v1/graph/data?document=test.pdf")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["nodes"]) == 1
            assert data["nodes"][0]["id"] == "Alice"
