"""
app/routers/graph.py — Endpoints for graph entity extraction.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from app.services.document_processor import GraphEntityProcessor
from app.services.community_summarizer import run_community_pipeline
from app.services.neo4j_client import neo4j_client
from app.schemas import (
    DocumentProcessResponse,
    GraphDataResponse,
    CommunitySummaryResponse,
)

router = APIRouter(prefix="/graph", tags=["Graph Extraction"])


@router.post("/extract", response_model=DocumentProcessResponse)
async def extract_graph(
    file: UploadFile = File(...),
    model: str = Form("phi3:mini"),
    summarize: bool = Form(True),
    max_batches: int = Form(None),
) -> DocumentProcessResponse:
    """Extract KG from document: OCR → LLM → Neo4j → Community → Qdrant."""
    processor = GraphEntityProcessor(model=model)
    suffix = Path(file.filename).suffix
    temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        path = Path(temp_file.name)
        response = await processor.process_document(path, model_override=model, max_batches=max_batches)
        response.filename = file.filename

        if response.graph:
            await neo4j_client.insert_graph_result(file.filename, response.graph)

        if summarize and response.graph:
            try:
                response.community_summaries = await run_community_pipeline(
                    document_name=file.filename,
                    model=model,
                )
            except Exception as e:
                print(f"Community pipeline failed: {e}")

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        path = Path(temp_file.name)
        if path.exists():
            path.unlink()


@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data(document: Optional[str] = Query(None)) -> GraphDataResponse:
    """Get graph for visualization."""
    try:
        return GraphDataResponse(**(await neo4j_client.get_full_graph(document)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities", response_model=CommunitySummaryResponse)
async def get_communities(
    document: str = Query(...),
    run_pipeline: bool = Query(False),
    model: str = Query("phi3:mini"),
) -> CommunitySummaryResponse:
    """Get community summaries from Neo4j."""
    if run_pipeline:
        try:
            await run_community_pipeline(document_name=document, model=model)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    try:
        communities = await neo4j_client.detect_communities(document)
        return CommunitySummaryResponse(
            document=document,
            communities=[
                {
                    "community_id": c.id,
                    "node_count": len(c.nodes),
                    "edge_count": len(c.edges),
                    "context": c.context_text(),
                }
                for c in communities
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
