# 07 — Tests

## Test Suite
All tests use `pytest` + `pytest-asyncio` with mocked dependencies (no real DB/API calls).

## Test Files

### `tests/test_ollama_client.py`
- `test_generate_success` — Verifies LLM text generation
- `test_list_models` — Verifies model listing from `/api/tags`
- `test_get_embedding_success` — Verifies embedding generation via `/api/embed`
- `test_get_embedding_fallback` — Verifies hash-based fallback when Ollama fails

### `tests/test_document_processor.py`
- `test_sanitize_valid_json` — Direct valid JSON parsing
- `test_sanitize_json_code_block` — Extraction from markdown code blocks
- `test_sanitize_trailing_commas` — Trailing comma removal
- `test_sanitize_single_quotes` — Single-to-double quote conversion
- `test_sanitize_control_characters` — Control character stripping
- `test_sanitize_empty_input` — Handles None/empty input
- `test_sanitize_json_with_surrounding_text` — Extracts JSON from explanatory text
- `test_chunking_logic` — Verifies word-based chunking at 300 words

### `tests/test_neo4j_client.py`
- `test_safe_label` — Label sanitization (alphanumeric only)
- `test_community_context_text` — Community.context_text() output format
- `test_client_initialization` — Default state verification
- `test_no_driver_guards` — Methods return safely when driver is None

### `tests/test_community_summarizer.py`
- `test_community_hash_deterministic` — Same input → same UUID
- `test_summarize_community_success` — LLM summarization with mocked Ollama
- `test_summarize_community_empty` — Handles empty community
- `test_summarize_community_error` — Handles LLM failure gracefully
- `test_store_summary_success` — Qdrant upsert with mocked client
- `test_store_summary_error` — Handles Qdrant failure gracefully

### `tests/test_qdrant_client.py`
- `test_initialization` — Default collection name and vector size
- `test_insert_summary_no_client` — Skips insert when client is None
- `test_close_clears_client` — Client set to None after close
- `test_insert_summary_with_metadata` — Verifies upsert called with metadata

### `tests/test_graph_router.py`
- `test_get_graph_data_empty` — Empty graph response
- `test_get_graph_data_with_document` — Filtered graph response

## Running Tests
```bash
cd backend
pytest tests/ -v
```

## Files Changed
- `tests/test_ollama_client.py` — New
- `tests/test_document_processor.py` — New
- `tests/test_neo4j_client.py` — New
- `tests/test_community_summarizer.py` — New
- `tests/test_qdrant_client.py` — New
- `tests/test_graph_router.py` — New
