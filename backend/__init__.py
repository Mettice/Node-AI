"""
NodeAI - NodeFlow Backend Package

This package contains the backend API for the NodeAI visual workflow builder.
It provides a FastAPI-based REST API for executing RAG workflows.
"""

__version__ = "0.1.0"
__app_name__ = "NodeAI"

# Import main components for easy access
from backend.config import settings
from backend.utils.logger import get_logger, main_logger

__all__ = [
    "settings",
    "get_logger",
    "main_logger",
    "__version__",
    "__app_name__",
]

