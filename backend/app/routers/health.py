"""
app/routers/health.py — /api/v1/health endpoint.
"""
from fastapi import APIRouter

from app import ollama_client
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """Checks whether the backend can reach the Ollama service."""
    try:
        await ollama_client.list_models()
        reachable = True
    except Exception:
        reachable = False

    return HealthResponse(status="ok", ollama_reachable=reachable)
