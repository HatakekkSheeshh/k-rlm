"""
tests/test_neo4j_client.py — Tests for Neo4j client and community detection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.neo4j_client import safe_label, Community


class TestSafeLabel:
    """Tests for the safe_label function."""

    def test_normal_string(self):
        assert safe_label("PERSON") == "PERSON"
        assert safe_label("ORGANIZATION") == "ORGANIZATION"

    def test_spaces_and_dashes(self):
        assert safe_label("Hello World") == "HELLOWORLD"
        assert safe_label("my-variable") == "MY_VARIABLE"

    def test_special_characters(self):
        assert safe_label("Hello@World!") == "HELLOWORLD"
        assert safe_label("Test#123") == "TEST123"

    def test_empty_string(self):
        assert safe_label("") == "UNKNOWN"

    def test_none_input(self):
        assert safe_label(None) == "UNKNOWN"


class TestCommunity:
    """Tests for the Community class."""

    def test_context_text(self):
        nodes = [
            {"id": "Alice", "label": "PERSON"},
            {"id": "Bob", "label": "PERSON"},
        ]
        edges = [
            {"source": "Alice", "target": "Bob", "relation": "KNOWS"},
        ]
        community = Community(community_id=1, nodes=nodes, edges=edges)
        context = community.context_text()

        assert "Entity: Alice (type: PERSON)" in context
        assert "Entity: Bob (type: PERSON)" in context
        assert "Alice --[KNOWS]--> Bob" in context


class TestNeo4jClient:
    """Tests for Neo4jClient (unit tests without actual DB connection)."""

    def test_client_initialization(self):
        """Test that client can be instantiated."""
        from app.services.neo4j_client import Neo4jClient
        client = Neo4jClient()
        assert client._driver is None

    @pytest.mark.asyncio
    async def test_insert_graph_no_driver(self):
        """Test insert skips when driver is None."""
        from app.services.neo4j_client import Neo4jClient
        client = Neo4jClient()

        # Mock graph result
        mock_graph = MagicMock()
        mock_graph.nodes = []
        mock_graph.edges = []

        # Should not raise, just warn
        await client.insert_graph_result("test.pdf", mock_graph)

    @pytest.mark.asyncio
    async def test_get_full_graph_no_driver(self):
        """Test get_full_graph returns empty when driver is None."""
        from app.services.neo4j_client import Neo4jClient
        client = Neo4jClient()

        result = await client.get_full_graph()
        assert result == {"nodes": [], "edges": []}

    @pytest.mark.asyncio
    async def test_detect_communities_no_driver(self):
        """Test detect_communities returns empty when driver is None."""
        from app.services.neo4j_client import Neo4jClient
        client = Neo4jClient()

        result = await client.detect_communities("test.pdf")
        assert result == []
