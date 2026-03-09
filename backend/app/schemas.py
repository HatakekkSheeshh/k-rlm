"""
app/schemas.py — Pydantic request / response models.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Inference ────────────────────────────────────────────────────────────────

class ExecutionStep(BaseModel):
    """Represents a single step in the RLM execution trace."""
    id: int = Field(..., description="Step number (1-based)")
    type: str = Field(..., description="Step type: split, retrieve, reason, resolve")
    text: str = Field(..., description="Human-readable description of this step")
    details: dict = Field(default_factory=dict, description="Additional details (entities, context, etc.)")


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
    trace: list[ExecutionStep] = Field(default_factory=list, description="Execution trace for RLM reasoning")


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

# ─── Graph / Entities ─────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str = Field(..., description="Unique ID or normalized name of the node.")
    label: str = Field(..., description="Type or category of the node (e.g., PERSON, ORGANIZATION, PRODUCT, CONCEPT).")
    properties: dict = Field(default_factory=dict, description="Additional properties associated with the node.")

class GraphEdge(BaseModel):
    source: str = Field(..., description="ID of the source node.")
    target: str = Field(..., description="ID of the target node.")
    relation: str = Field(..., description="Type of relationship between source and target.")
    properties: dict = Field(default_factory=dict, description="Additional properties associated with the edge.")

class GraphResult(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list, description="Extracted distinct entities (nodes).")
    edges: list[GraphEdge] = Field(default_factory=list, description="Extracted relationships (edges).")
    
class DocumentProcessResponse(BaseModel):
    filename: str
    graph: GraphResult | None
    raw_text: str | None = Field(default=None, description="Raw text extracted by OCR/Kreuzberg.")
    metrics: InferenceMetrics | None
    community_summaries: list[dict] | None = Field(default=None, description="Community summaries from Qdrant")


class GraphDataResponse(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class CommunitySummaryResponse(BaseModel):
    document: str
    communities: list[dict] = Field(default_factory=list)
