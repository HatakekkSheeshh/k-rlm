"""
tests/test_document_processor.py — Tests for document processing and JSON sanitization.
"""
import pytest
from app.services.document_processor import sanitize_json, GraphEntityProcessor


class TestSanitizeJson:
    """Tests for the sanitize_json function."""

    def test_valid_json(self):
        text = '{"nodes": [], "edges": []}'
        result = sanitize_json(text)
        assert result == {"nodes": [], "edges": []}

    def test_json_in_code_block(self):
        text = 'Some text\n```json\n{"nodes": [], "edges": []}\n```\nMore text'
        result = sanitize_json(text)
        assert result == {"nodes": [], "edges": []}

    def test_json_in_plain_code_block(self):
        text = 'Some text\n```\n{"nodes": [], "edges": []}\n```\nMore text'
        result = sanitize_json(text)
        assert result == {"nodes": [], "edges": []}

    def test_trailing_commas(self):
        text = '{"nodes": [{"id": "A", "label": "X",},], "edges": []}'
        result = sanitize_json(text)
        assert result is not None
        assert result["nodes"][0]["id"] == "A"

    def test_single_quotes(self):
        text = "{'nodes': [], 'edges': []}"
        result = sanitize_json(text)
        assert result is not None
        assert result["nodes"] == []

    def test_control_characters(self):
        text = '{"nodes": [\n\t{"id": "A",\x00 "label": "X"}\n], "edges": []}'
        result = sanitize_json(text)
        assert result is not None
        assert result["nodes"][0]["id"] == "A"

    def test_empty_string(self):
        assert sanitize_json("") is None
        assert sanitize_json(None) is None

    def test_no_json(self):
        assert sanitize_json("This is just plain text") is None

    def test_json_with_surrounding_text(self):
        text = 'Here is the result: {"nodes": [{"id": "A", "label": "PERSON"}], "edges": []} end.'
        result = sanitize_json(text)
        assert result is not None
        assert len(result["nodes"]) == 1


class TestGraphEntityProcessor:
    """Tests for the GraphEntityProcessor chunking logic."""

    def test_chunk_text_basic(self):
        processor = GraphEntityProcessor()
        text = " ".join([f"word{i}" for i in range(600)])
        chunks = processor._chunk_text(text, word_limit=300)
        assert len(chunks) == 2
        assert len(chunks[0].split()) == 300
        assert len(chunks[1].split()) == 300

    def test_chunk_text_small_input(self):
        processor = GraphEntityProcessor()
        text = "hello world"
        chunks = processor._chunk_text(text, word_limit=300)
        assert len(chunks) == 1
        assert chunks[0] == "hello world"

    def test_chunk_text_empty(self):
        processor = GraphEntityProcessor()
        chunks = processor._chunk_text("", word_limit=300)
        assert chunks == []

    def test_create_batches_returns_chunks(self):
        processor = GraphEntityProcessor()
        chunks = ["chunk1", "chunk2", "chunk3"]
        batches = processor._create_batches(chunks)
        assert batches == chunks
