"""Metrics endpoint for Prometheus-compatible monitoring."""

from fastapi import APIRouter, Response
from monitoring.metrics_collector import get_metrics_collector

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus text format including:
    - Request counts by intent and language
    - Latency percentiles (p50, p95, p99)
    - Error rates
    - Cache hit rates
    """
    collector = get_metrics_collector()
    metrics_text = collector.prometheus_text()
    
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )