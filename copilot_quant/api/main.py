"""
FastAPI Main Application

Provides REST API endpoints for portfolio, positions, orders, and performance metrics.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .auth import verify_api_key
from .endpoints import portfolio, positions, orders, performance, health
from . import websocket

logger = logging.getLogger(__name__)


# Application state
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Copilot Quant API...")
    
    # Initialize components here (database connections, etc.)
    # app_state['db'] = TradeDatabase(...)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Copilot Quant API...")
    
    # Cleanup here
    # app_state['db'].close()


def create_app(
    title: str = "Copilot Quant API",
    version: str = "1.0.0",
    require_auth: bool = False
) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        title: API title
        version: API version
        require_auth: If True, require API key authentication on all endpoints
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        version=version,
        description="REST API for Copilot Quant Trading Platform",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store auth requirement in app state
    app.state.require_auth = require_auth
    
    # Include routers
    app.include_router(
        health.router,
        prefix="/health",
        tags=["health"]
    )
    
    # WebSocket routes (no auth for now)
    app.include_router(
        websocket.router,
        prefix="/ws",
        tags=["websocket"]
    )
    
    if require_auth:
        # Protected endpoints
        app.include_router(
            portfolio.router,
            prefix="/api/v1/portfolio",
            tags=["portfolio"],
            dependencies=[Depends(verify_api_key)]
        )
        app.include_router(
            positions.router,
            prefix="/api/v1/positions",
            tags=["positions"],
            dependencies=[Depends(verify_api_key)]
        )
        app.include_router(
            orders.router,
            prefix="/api/v1/orders",
            tags=["orders"],
            dependencies=[Depends(verify_api_key)]
        )
        app.include_router(
            performance.router,
            prefix="/api/v1/performance",
            tags=["performance"],
            dependencies=[Depends(verify_api_key)]
        )
    else:
        # Open endpoints (for development)
        app.include_router(
            portfolio.router,
            prefix="/api/v1/portfolio",
            tags=["portfolio"]
        )
        app.include_router(
            positions.router,
            prefix="/api/v1/positions",
            tags=["positions"]
        )
        app.include_router(
            orders.router,
            prefix="/api/v1/orders",
            tags=["orders"]
        )
        app.include_router(
            performance.router,
            prefix="/api/v1/performance",
            tags=["performance"]
        )
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "Copilot Quant API",
            "version": version,
            "status": "operational",
            "docs": "/docs",
            "health": "/health"
        }
    
    logger.info(f"FastAPI application created: {title} v{version}")
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
