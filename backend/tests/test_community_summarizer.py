"""
tests/test_community_summarizer.py — Tests for community summarization pipeline.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.neo4j_client import Community
from app.services.community_summarizer import (
    _community_hash,
    summarize_community,
    store_community_summary,
)


class TestCommunityHash:
    """Tests for the _community_hash function."""

    def test_deterministic(self):
        h1 = _community_hash(1, "doc.pdf")
        h2 = _community_hash(1, "doc.pdf")
        assert h1 == h2

    def test_different_inputs(self):
        h1 = _community_hash(1, "doc.pdf")
        h2 = _community_hash(2, "doc.pdf")
        h3 = _community_hash(1, "other.pdf")
        assert h1 != h2
        assert h1 != h3


class TestSummarizeCommunity:
    """Tests for the summarize_community function."""

    @pytest.mark.asyncio
    async def test_summarize_returns_text(self):
        community = Community(
            community_id=1,
            nodes=[{"id": "Alice", "label": "PERSON"}],
            edges=[],
        )

        with patch("app.services.community_summarizer.generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"output": "Alice is a person entity."}
            result = await summarize_community(community, model="phi3:mini")

            assert result == "Alice is a person entity."
            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_empty_community(self):
        community = Community(community_id=1, nodes=[], edges=[])
        result = await summarize_community(community)
        assert result is None

    @pytest.mark.asyncio
    async def test_summarize_handles_error(self):
        community = Community(
            community_id=1,
            nodes=[{"id": "Alice", "label": "PERSON"}],
            edges=[],
        )

        with patch("app.services.community_summarizer.generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = Exception("LLM Error")
            result = await summarize_community(community)
            assert result is None


class TestStoreCommunity:
    """Tests for the store_community_summary function."""

    @pytest.mark.asyncio
    async def test_store_success(self):
        community = Community(
            community_id=1,
            nodes=[{"id": "Alice", "label": "PERSON"}],
            edges=[],
        )

        with patch("app.services.community_summarizer.get_embedding", new_callable=AsyncMock) as mock_embed, \
             patch("app.services.community_summarizer.qdrant_client") as mock_qdrant:
            mock_embed.return_value = [0.1] * 384
            mock_qdrant.insert_summary = AsyncMock()

            result = await store_community_summary(community, "Test summary", "doc.pdf")
            assert result is True
            mock_qdrant.insert_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_handles_error(self):
        community = Community(
            community_id=1,
            nodes=[{"id": "Alice", "label": "PERSON"}],
            edges=[],
        )

        with patch("app.services.community_summarizer.get_embedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.side_effect = Exception("Embedding Error")
            result = await store_community_summary(community, "Test summary", "doc.pdf")
            assert result is False
