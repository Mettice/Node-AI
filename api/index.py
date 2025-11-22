"""
Vercel serverless function entry point for NodeAI backend.

This file must be at /api/index.py for Vercel to detect it as a serverless function.
All API routes will be handled by this function.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

# Set environment for serverless (no file system writes)
os.environ.setdefault("VERCEL", "1")

# Disable directory creation in serverless
os.environ.setdefault("DISABLE_DIR_CREATION", "1")

# Import the FastAPI app
try:
    from backend.main import app
except Exception as e:
    # If import fails, create a minimal error handler
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/{path:path}")
    async def error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to initialize application",
                "message": str(e),
                "path": path
            }
        )

# Vercel Python runtime expects handler to be the ASGI app
handler = app

