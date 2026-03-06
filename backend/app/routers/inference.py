"""
app/routers/inference.py — /api/v1/inference endpoints.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from app import ollama_client
from app.schemas import InferenceMetrics, InferenceRequest, InferenceResponse

router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("", response_model=InferenceResponse, summary="Run single-turn inference")
async def run_inference(body: InferenceRequest) -> InferenceResponse:
    """
    Sends a prompt to the requested Ollama model and returns a synthesised answer
    plus generation metrics (tokens, latency).
    """
    t0 = time.perf_counter()
    try:
        raw = await ollama_client.generate(
            prompt=body.prompt,
            model=body.model,
            system=body.system,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}") from exc

    latency = time.perf_counter() - t0

    return InferenceResponse(
        answer=raw.get("response", ""),
        metrics=InferenceMetrics(
            model=body.model,
            strategy=body.strategy,
            eval_count=raw.get("eval_count"),
            eval_duration=raw.get("eval_duration"),
            latency_s=round(latency, 3),
        ),
    )
