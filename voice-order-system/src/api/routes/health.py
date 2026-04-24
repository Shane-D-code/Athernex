"""Health check and metrics endpoints — Tasks 18.1, 18.3."""

import platform
import torch
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from monitoring.metrics_collector import get_metrics_collector

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    gpu_name: str
    python_version: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check. Returns GPU availability and system info."""
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"
    return HealthResponse(
        status="ok",
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        python_version=platform.python_version(),
        message="Athernex Voice Pipeline is running",
    )


@router.get("/metrics", summary="Pipeline metrics (JSON)")
async def metrics_json():
    """
    Return pipeline metrics in JSON format.
    Includes latency percentiles, error rates, intent distribution, cache stats.
    Task 18.3
    """
    return get_metrics_collector().get_summary()


@router.get("/metrics/prometheus", response_class=PlainTextResponse,
            summary="Pipeline metrics (Prometheus text format)")
async def metrics_prometheus():
    """
    Return metrics in Prometheus text exposition format.
    Compatible with Grafana / Prometheus scraping.
    Task 18.3
    """
    return get_metrics_collector().prometheus_text()
