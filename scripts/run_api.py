#!/usr/bin/env python
"""
API Server Launcher

Starts the Copilot Quant REST API server.

Usage:
    python scripts/run_api.py [--port 8000] [--host 0.0.0.0] [--auth]
"""

import argparse
import sys
import uvicorn
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.api import create_app


def main():
    parser = argparse.ArgumentParser(description="Run Copilot Quant API Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Enable API key authentication"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Create app
    app = create_app(require_auth=args.auth)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Copilot Quant REST API Server                    ║
╠══════════════════════════════════════════════════════════╣
║  URL:          http://{args.host}:{args.port}                        ║
║  Docs:         http://{args.host}:{args.port}/docs                   ║
║  Health:       http://{args.host}:{args.port}/health                 ║
║  Metrics:      http://{args.host}:{args.port}/metrics/json           ║
║  Auth:         {'Enabled' if args.auth else 'Disabled'}                              ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
