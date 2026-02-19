"""
Health Check Endpoints

Provides system health and status endpoints.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from copilot_quant.monitoring.health_monitor import get_health_monitor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    monitor = get_health_monitor()
    status = monitor.get_health_status()
    
    return {
        "status": status['overall_status'],
        "timestamp": datetime.now().isoformat(),
        "service": "copilot-quant-api"
    }


@router.get("/detailed")
async def detailed_health() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Returns:
        Detailed health information
    """
    monitor = get_health_monitor()
    return monitor.get_health_status()


@router.get("/ready")
async def readiness() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.
    
    Returns:
        Readiness status
    """
    monitor = get_health_monitor()
    status = monitor.get_health_status()
    
    return {
        "ready": status['overall_status'] in ['healthy', 'degraded'],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/live")
async def liveness() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.
    
    Returns:
        Liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat()
    }
