"""
tests/test_qdrant_client.py — Tests for Qdrant client.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.qdrant_client import QdrantConnector


class TestQdrantConnector:
    """Tests for QdrantConnector (unit tests without actual DB connection)."""

    def test_initialization(self):
        connector = QdrantConnector()
        assert connector._client is None
        assert connector.collection_name == "community_summaries"
        assert connector.vector_size == 384

    @pytest.mark.asyncio
    async def test_insert_summary_no_client(self):
        """Test insert skips when client is None."""
        connector = QdrantConnector()
        # Should not raise, just warn
        await connector.insert_summary(
            community_id="test-id",
            summary_text="Test summary",
            vector=[0.1] * 384,
        )

    @pytest.mark.asyncio
    async def test_close_clears_client(self):
        connector = QdrantConnector()
        connector._client = MagicMock()
        await connector.close()
        assert connector._client is None

    @pytest.mark.asyncio
    async def test_insert_summary_with_metadata(self):
        """Test insert with metadata payload."""
        connector = QdrantConnector()
        connector._client = AsyncMock()
        connector._client.upsert = AsyncMock()

        await connector.insert_summary(
            community_id="test-id",
            summary_text="Test summary",
            vector=[0.1] * 384,
            metadata={"document": "test.pdf", "community_id": 1},
        )

        connector._client.upsert.assert_called_once()
