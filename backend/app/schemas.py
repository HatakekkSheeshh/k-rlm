"""
app/schemas.py — Pydantic request / response models.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Inference ────────────────────────────────────────────────────────────────

class InferenceRequest(BaseModel):
    prompt:          str         = Field(...,            min_length=1, description="User query or OCR text")
    model:           str         = Field("phi3:mini",    description="Ollama model tag")
    strategy:        str         = Field("Standard RAG", description="Reasoning strategy label")
    system:          str | None  = Field(None,           description="Optional system prompt override")
    prompt_template: str         = Field("raw",          description="Prompt template id from /api/v1/templates")


class InferenceMetrics(BaseModel):
    model:        str
    strategy:     str
    eval_count:   int   | None = None   # tokens generated
    eval_duration: int  | None = None   # nanoseconds
    latency_s:    float | None = None   # seconds (wall-clock)


class InferenceResponse(BaseModel):
    answer:  str
    metrics: InferenceMetrics


# ─── Model management ─────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    tag:   str
    label: str | None = None


class ModelsListResponse(BaseModel):
    available: list[str]    # already pulled in Ollama
    supported: list[ModelInfo]  # our curated list


class PullRequest(BaseModel):
    tag: str = Field(..., description="Ollama model tag to pull, e.g. 'phi3:mini'")


class PullResponse(BaseModel):
    tag:    str
    status: str


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:       str = "ok"
    ollama_reachable: bool
