"""
FastAPI application — entry point for the ML pipeline API layer.
Exposes REST endpoints for transcription, processing, synthesis,
and a WebSocket endpoint for real-time streaming.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes import health, pipeline, websocket_stream, metrics
from api.dependencies import startup_pipeline, shutdown_pipeline

logger = logging.getLogger(__name__)

# Project root (voice-order-system/)
_ROOT = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting Athernex Voice Pipeline API...")
    await startup_pipeline()
    yield
    logger.info("Shutting down Athernex Voice Pipeline API...")
    await shutdown_pipeline()


app = FastAPI(
    title="Athernex Voice Pipeline API",
    description=(
        "Multilingual voice order processing pipeline for Indian languages. "
        "Supports Hindi, Kannada, Marathi, English, and code-mixed speech."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for hackathon; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["Pipeline"])
app.include_router(websocket_stream.router, tags=["Streaming"])
app.include_router(metrics.router, tags=["Metrics"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to demo page."""
    return RedirectResponse(url="/demo")


@app.get("/demo", include_in_schema=False)
async def demo():
    """Serve the voice pipeline demo UI."""
    return FileResponse(_ROOT / "demo.html")
