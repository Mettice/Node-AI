"""
Vercel serverless function entry point for NodeAI backend.

This file must be at /api/index.py for Vercel to detect it as a serverless function.
All API routes will be handled by this function.
"""

import sys
from pathlib import Path

# Add project root to Python path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

# Import the FastAPI app
from backend.main import app

# Vercel Python runtime expects handler to be the ASGI app
# The @vercel/python builder will wrap this correctly
handler = app

