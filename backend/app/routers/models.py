"""Model management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import ollama_client
from app.schemas import ModelInfo, ModelsListResponse, PullRequest, PullResponse

router = APIRouter(prefix="/models", tags=["models"])

SUPPORTED_MODELS: list[ModelInfo] = [
    ModelInfo(tag="phi3:mini", label="Phi-3 Mini"),
    ModelInfo(tag="gemma:7b", label="Gemma 7B"),
    ModelInfo(tag="mistral:7b-instruct-v0.2-q4_0", label="Mistral 7B v0.2"),
]


@router.get("", response_model=ModelsListResponse)
async def list_models() -> ModelsListResponse:
    """List supported & available models."""
    try:
        available = await ollama_client.list_models()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {exc}") from exc
    return ModelsListResponse(available=available, supported=SUPPORTED_MODELS)


@router.post("/pull", response_model=PullResponse)
async def pull_model(body: PullRequest) -> PullResponse:
    """Pull a model into Ollama."""
    valid_tags = {m.tag for m in SUPPORTED_MODELS}
    if body.tag not in valid_tags:
        raise HTTPException(status_code=422, detail=f"Tag '{body.tag}' not in supported list: {valid_tags}")
    try:
        result = await ollama_client.pull_model(body.tag)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pull failed: {exc}") from exc
    return PullResponse(tag=body.tag, status=result.get("status", "unknown"))
