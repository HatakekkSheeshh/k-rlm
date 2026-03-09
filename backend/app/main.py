"""
app/main.py — FastAPI application factory.
"""

from __future__ import annotations

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ollama_client import close_client
from app.routers import health, inference, models, graph

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.services.neo4j_client import neo4j_client
    from app.services.qdrant_client import qdrant_client
    await neo4j_client.connect()
    await qdrant_client.connect()
    yield
    # Shutdown
    await close_client()
    await neo4j_client.close()
    await qdrant_client.close()


app = FastAPI(
    title="K-RLM Architecture API",
    version="0.1.0",
    description="Backend inference & evaluation service for the K-RLM research platform.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(inference.router, prefix=settings.api_prefix)
app.include_router(models.router, prefix=settings.api_prefix)
app.include_router(graph.router, prefix=settings.api_prefix)

# ── Inline lightweight endpoint: template list ──────────────────────────────────
from app.prompts import TEMPLATES


@app.get(f"{settings.api_prefix}/templates", tags=["Inference"])
def list_templates():
    """Return available prompt templates (id + label) for the frontend."""
    return [{"id": t["id"], "label": t["label"]} for t in TEMPLATES]
