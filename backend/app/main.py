"""
app/main.py — FastAPI application factory.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ollama_client import close_client
from app.routers import health, inference, models

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

app = FastAPI(
    title="K-RLM Architecture API",
    version="0.1.0",
    description="Backend inference & evaluation service for the K-RLM research platform.",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(health.router,    prefix=settings.api_prefix)
app.include_router(inference.router, prefix=settings.api_prefix)
app.include_router(models.router,    prefix=settings.api_prefix)


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown() -> None:
    await close_client()
