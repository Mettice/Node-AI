"""
Vercel serverless entry point for NodeAI backend.
"""

from backend.main import app

# This is what Vercel will call
handler = app

