# 03 — JSON Sanitization

## Problem
LLM output often contains invalid JSON due to:
- Control characters (ASCII 0-31, 127-159)
- Trailing commas before closing braces/brackets
- Single quotes instead of double quotes
- Missing commas between properties (e.g., `{"id": "foo" "label": "bar"}`)
- Missing colons after keys
- Markdown code block wrappers
- Unterminated strings or braces
- Surrounding explanatory text
- Multiple JSON objects concatenated ("Extra data" error)

## Fix
Implemented `sanitize_json()` with `_aggressive_cleanup()` helper.

## Implementation

### Step 1: Extract JSON substring
Strip everything before first `{` and after last `}`:
```python
first_brace = text.find('{')
last_brace = text.rfind('}')
text = text[first_brace:last_brace+1]
```

### Step 2: Try direct parse
```python
return json.loads(text, strict=False)
```

### Step 3-5: Fallback strategies
- Strategy 2: Extract from markdown code blocks
- Strategy 3: Brace matching + cleanup
- Strategy 4: Aggressive cleanup only

### Aggressive Cleanup (`_aggressive_cleanup`)
```python
# Remove // comments (LLM sometimes injects these)
text = re.sub(r'//[^\n]*', '', text)

# Remove trailing commas
text = re.sub(r',\s*([\]}])', r'\1', text)

# Replace single quotes
text = re.sub(r"'([^']*)'", r'"\1"', text)

# Fix missing commas between properties: "value" "key" -> "value", "key"
text = re.sub(r'"\s*\n\s*"', '", "', text)

# Fix missing commas between objects: } { -> }, {
text = re.sub(r'}\s*{', '}, {', text)

# Fix missing colon: "key" "value" -> "key": "value"
text = re.sub(r'"(\w+)"\s+"', r'"\1": "', text)

# Fix missing comma after } or ]: } "key" -> }, "key"
text = re.sub(r'([}\]])\s+"', r'\1, "', text)
```

### Strategy 5: Regex Extraction (Last Resort)
When JSON is structurally broken (e.g., LLM hallucinated garbage mid-output), use regex to extract individual valid node/edge objects:

```python
def _regex_extract_nodes_edges(text):
    # Find node-like: {"id": "...", "label": "..."}
    node_pattern = re.finditer(r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"label"\s*:\s*"([^"]+)"[^}]*\}', text)

    # Find edge-like: {"source": "...", "target": "...", "relation": "..."}
    edge_pattern = re.finditer(r'\{\s*"source"\s*:\s*"([^"]+)"\s*,\s*"target"\s*:\s*"([^"]+)"\s*,\s*"relation"\s*:\s*"([^"]+)"[^}]*\}', text)

    return {"nodes": [...], "edges": [...]}
```

## Note on Per-Item Validation
After JSON parsing, nodes and edges are validated individually (not via Pydantic bulk).
Malformed edges (missing `target` or `relation`) are skipped instead of failing the whole batch.
See `09-timeout-concurrency-fix.md` for details.

## Files Changed
- `app/services/document_processor.py`
