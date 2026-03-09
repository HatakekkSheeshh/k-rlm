import json
import logging
import re
import time
import asyncio
from pathlib import Path
from typing import Optional

from kreuzberg import extract_file, OcrConfig, ExtractionConfig, ExtractionResult
from app.ollama_client import generate
from app.schemas import GraphResult, GraphNode, GraphEdge, DocumentProcessResponse, InferenceMetrics

logger = logging.getLogger(__name__)


def sanitize_json(text: str) -> Optional[dict]:
    """Parse JSON from LLM output with fallback strategies."""
    if not text:
        return None
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)

    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace+1]

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    json_match = None
    if "```json" in text:
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    elif "```" in text:
        json_match = re.search(r'```\s*([\s\S]*?)\s*```', text)

    if json_match:
        candidate = json_match.group(1).strip()
        candidate = _aggressive_cleanup(candidate)
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        candidate = _aggressive_cleanup(candidate)
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass

    candidate = _aggressive_cleanup(text)
    try:
        return json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        pass

    result = _regex_extract_nodes_edges(text)
    if result and (result.get("nodes") or result.get("edges")):
        logger.info(f"Regex fallback recovered {len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges")
        return result

    logger.warning(f"JSON parse failed after all strategies")
    return None


def _regex_extract_nodes_edges(text: str) -> Optional[dict]:
    """Regex fallback for broken JSON."""
    nodes = []
    edges = []
    for m in re.finditer(r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"label"\s*:\s*"([^"]+)"[^}]*\}', text):
        nodes.append({"id": m.group(1), "label": m.group(2), "properties": {}})
    for m in re.finditer(r'\{\s*"source"\s*:\s*"([^"]+)"\s*,\s*"target"\s*:\s*"([^"]+)"\s*,\s*"relation"\s*:\s*"([^"]+)"[^}]*\}', text):
        edges.append({"source": m.group(1), "target": m.group(2), "relation": m.group(3), "properties": {}})
    return {"nodes": nodes, "edges": edges} if nodes or edges else None


def _aggressive_cleanup(text: str) -> str:
    """Fix malformed JSON."""
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r',\s*([\]}])', r'\1', text)
    text = re.sub(r"'([^']*)'", r'"\1"', text)
    text = re.sub(r'"\s*\n\s*"', '", "', text)
    text = re.sub(r'}\s*{', '}, {', text)
    text = re.sub(r']\s*\[', '], [', text)
    text = re.sub(r'"(\w+)"\s+"', r'"\1": "', text)
    text = re.sub(r'([}\]])\s+"', r'\1, "', text)
    lines = [l for l in text.split('\n') if not l.strip().startswith('#') and not l.strip().startswith('Here is')]
    text = re.sub(r'\n+', ' ', '\n'.join(lines))
    return text.strip()


class KreuzbergExtractor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, backend: str = "paddleocr", language: str = "vi"):
        if not hasattr(self, "_initialized"):
            self.config = ExtractionConfig(ocr=OcrConfig(backend=backend, language=language))
            self._initialized = True
            logger.info(f"KreuzbergExtractor initialized | backend={backend} | language={language}")

    async def extract_text(self, file_path: Path) -> Optional[str]:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        logger.info(f"Processing document: {file_path.name}")
        try:
            result: ExtractionResult = await extract_file(file_path, config=self.config)
            logger.info(f"Done: {file_path.name} | {len(result.content)} chars")
            return result.content
        except Exception as e:
            logger.error(f"Extraction failed for {file_path.name}: {e}")
            return None


class GraphEntityProcessor:
    def __init__(self, model: str = "phi3:mini", max_concurrent: int = 1):
        self._model = model
        self._extractor = KreuzbergExtractor()
        # Process sequentially (1 at a time) to avoid overwhelming Ollama
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _chunk_text(self, text: str, word_limit: int = 300) -> list[str]:
        """Split text into chunks of ~300 words (~1200 chars) for efficient LLM processing."""
        words = text.split()
        return [" ".join(words[i : i + word_limit]) for i in range(0, len(words), word_limit)]

    def _create_batches(self, chunks: list[str], batch_size: int = 1) -> list[str]:
        """Each chunk becomes a batch - no grouping (simpler, more accurate)."""
        return chunks

    async def _extract_from_batch(self, batch_text: str, model: str) -> Optional[GraphResult]:
        prompt = f"""
        You extract structured Knowledge Graph entities and relationships from the text.
        Your primary focus is capturing Entity-Relation-Entity triplets.

        Rules:
        - Identify distinct entities (nodes) such as PERSON, ORGANIZATION, LOCATION, CONCEPT, DATE.
        - Identify relationships (edges) between these entities to form the Entity-Relation-Entity structures.
        - Maintain exact entity names from the text where possible.
        - Each edge MUST have source, target, and relation fields.

        OCR / EXTRACTED BATCH TEXT:
        {batch_text}

        Return ONLY valid JSON in this exact structure:
        {{
            "nodes": [
                {{"id": "Entity Name", "label": "CATEGORY", "properties": {{}}}}
            ],
            "edges": [
                {{"source": "Source Entity ID", "target": "Target Entity ID", "relation": "RELATION TYPE", "properties": {{}}}}
            ]
        }}
        """

        async with self._semaphore:
            try:
                response_raw = await generate(
                    prompt=prompt,
                    model=model,
                    system="You are an expert knowledge graph extraction AI. Return ONLY valid JSON.",
                )
                output_text = response_raw.get("output", "")

                # Try sanitized JSON parsing with multiple fallback strategies
                graph_data = sanitize_json(output_text)
                if graph_data is None:
                    logger.warning(f"Could not parse JSON from LLM output, skipping batch. Raw (first 500 chars): {output_text[:500]}")
                    return None

                # Validate and build nodes individually (skip invalid)
                valid_nodes = []
                for node_data in graph_data.get("nodes", []):
                    if isinstance(node_data, dict) and node_data.get("id") and node_data.get("label"):
                        valid_nodes.append(GraphNode(
                            id=str(node_data["id"]),
                            label=str(node_data["label"]),
                            properties=node_data.get("properties", {}),
                        ))

                # Validate and build edges individually (skip invalid)
                valid_edges = []
                for edge_data in graph_data.get("edges", []):
                    if isinstance(edge_data, dict):
                        source = edge_data.get("source")
                        target = edge_data.get("target")
                        relation = edge_data.get("relation")
                        if source and target and relation:
                            valid_edges.append(GraphEdge(
                                source=str(source),
                                target=str(target),
                                relation=str(relation),
                                properties=edge_data.get("properties", {}),
                            ))
                        else:
                            logger.warning(f"Skipping invalid edge (missing fields): {edge_data}")

                return GraphResult(nodes=valid_nodes, edges=valid_edges)
            except Exception as e:
                logger.error(f"Failed to process batch: {e}")
                return None

    async def process_document(
        self, file_path: Path, model_override: str = None, max_batches: int = None
    ) -> DocumentProcessResponse:
        logger.info(f"========== DOCUMENT PROCESSING START: {file_path.name} ==========")
        t0 = time.perf_counter()

        logger.info("Starting OCR / Text Extraction using Kreuzberg...")
        raw_text = await self._extractor.extract_text(file_path)

        if not raw_text:
            logger.error("OCR failed or returned empty text. Aborting process.")
            return DocumentProcessResponse(filename=file_path.name, graph=None, metrics=None)

        logger.info(f"OCR Success. Extracted {len(raw_text)} characters.")

        model = model_override or self._model

        chunks = self._chunk_text(raw_text, word_limit=300)
        logger.info(f"Split document into {len(chunks)} chunks of roughly 300 words each.")

        batches = self._create_batches(chunks)

        # Apply max_batches limit if specified
        if max_batches and max_batches > 0:
            total_batches = len(batches)
            batches = batches[:max_batches]
            logger.info(f"Limited to {max_batches} batches (out of {total_batches} total)")
        else:
            logger.info(f"Processing {len(batches)} batches.")

        for i, batch in enumerate(batches, 1):
            logger.info(f"  - Batch {i} preview: {batch[:150]}...")

        logger.info(f"Extracting Entity-Relation-Entity sequentially using SLM ({model})...")

        # Process batches SEQUENTIALLY (one at a time) to avoid overwhelming Ollama
        merged_nodes = {}
        merged_edges = []

        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)}...")
            result = await self._extract_from_batch(batch, model)

            if not result:
                logger.warning(f"Batch {i} returned no valid data, skipping")
                continue

            # Validate and merge nodes
            for node in result.nodes:
                if node.id and node.label:
                    if node.id not in merged_nodes:
                        merged_nodes[node.id] = node

            # Validate and merge edges (skip malformed ones)
            for edge in result.edges:
                if edge.source and edge.target and edge.relation:
                    merged_edges.append(edge)
                else:
                    logger.warning(f"Skipping malformed edge: {edge}")

        final_graph = GraphResult(nodes=list(merged_nodes.values()), edges=merged_edges)

        node_count = len(final_graph.nodes)
        edge_count = len(final_graph.edges)
        logger.info(f"Extraction Success | Nodes: {node_count} | Edges: {edge_count}")

        latency = time.perf_counter() - t0
        logger.info(f"========== DOCUMENT PROCESSING COMPLETE in {latency:.2f}s ==========\n")

        # Basic aggregated metrics for chunked strategy
        metrics = InferenceMetrics(
            model=model,
            strategy="extraction_chunked",
            latency_s=round(latency, 3),
        )

        return DocumentProcessResponse(
            filename=file_path.name, graph=final_graph, raw_text=raw_text, metrics=metrics
        )
