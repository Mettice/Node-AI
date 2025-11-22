"""
Vercel serverless function entry point for NodeAI backend.
This file must be at /api/index.py for Vercel to detect it.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import the FastAPI app
from backend.main import app

# Vercel will call this
handler = app

