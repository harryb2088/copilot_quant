"""
REST API Module

Provides FastAPI-based REST API for accessing portfolio, positions, orders,
and performance metrics.
"""

__all__ = ['create_app']

from .main import create_app
