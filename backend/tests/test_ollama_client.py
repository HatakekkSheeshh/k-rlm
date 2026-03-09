"""
tests/test_ollama_client.py — Tests for the Ollama client wrapper.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestOllamaClient:
    """Tests for ollama_client module functions."""

    @pytest.mark.asyncio
    async def test_generate_returns_valid_response(self):
        """Test that generate returns properly formatted response."""
        from app import ollama_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Hello world",
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ollama_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await ollama_client.generate("test prompt", "phi3:mini")

            assert result["output"] == "Hello world"
            assert result["usage"]["input_tokens"] == 10
            assert result["usage"]["output_tokens"] == 5

    @pytest.mark.asyncio
    async def test_list_models_returns_model_list(self):
        """Test that list_models returns list of model names."""
        from app import ollama_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "phi3:mini"},
                {"name": "gemma:7b"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ollama_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await ollama_client.list_models()

            assert result == ["phi3:mini", "gemma:7b"]

    @pytest.mark.asyncio
    async def test_get_embedding_returns_vector(self):
        """Test that get_embedding returns a list of floats."""
        from app import ollama_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3]]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(ollama_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await ollama_client.get_embedding("test text")

            assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_get_embedding_fallback_on_error(self):
        """Test that get_embedding falls back to hash vector on error."""
        from app import ollama_client

        with patch.object(ollama_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client

            result = await ollama_client.get_embedding("test text")

            # Should return 384-dimensional hash vector
            assert isinstance(result, list)
            assert len(result) == 384
            assert all(0 <= x <= 1 for x in result)
