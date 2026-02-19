"""
Metrics Endpoints

Provides endpoints for Prometheus metrics export.
"""

import logging

from fastapi import APIRouter, Response

from copilot_quant.monitoring.metrics_exporter import get_metrics_exporter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/prometheus")
async def prometheus_metrics():
    """
    Export metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics
    """
    exporter = get_metrics_exporter()
    metrics_text = exporter.export_metrics()

    return Response(content=metrics_text, media_type="text/plain; version=0.0.4")


@router.get("/json")
async def json_metrics():
    """
    Export metrics as JSON.

    Returns:
        JSON-formatted metrics
    """
    exporter = get_metrics_exporter()
    return exporter.get_metrics_dict()
