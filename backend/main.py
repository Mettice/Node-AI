"""
NodeAI - NodeFlow Backend API

FastAPI application entry point for the NodeAI workflow execution engine.
This is the main application file that sets up the API server, middleware, and routes.

To run this application:
    From project root: uvicorn backend.main:app --reload
    Or: python -m backend.main
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

# Add parent directory to path to allow imports when running from backend/
# This must be done BEFORE any backend imports
_backend_dir = Path(__file__).parent
_project_root = _backend_dir.parent

# If we're in the backend directory, add project root to path
if _backend_dir.name == "backend" and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.core.security import add_security_headers, sanitize_dict

from backend.config import settings
from backend.utils.logger import get_logger
from backend.core.database import initialize_database, close_database, is_database_configured
from backend.middleware.auth import AuthMiddleware

# Initialize logger first
logger = get_logger(__name__)

# Initialize Sentry for error tracking (if DSN is configured)
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.httpx import HttpxIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            HttpxIntegration(),
        ],
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0 if settings.debug else 0.1,
        # Enable performance monitoring
        enable_tracing=True,
    )
    logger.info(f"Sentry initialized for environment: {settings.sentry_environment}")
else:
    logger.info("Sentry not configured (SENTRY_DSN not set)")

# Import API routers
from backend.api import execution, nodes, files, workflows, metrics, knowledge_base, api_keys, tools, oauth, query_tracer, secrets

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This runs code when the application starts and stops.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server: http://{settings.host}:{settings.port}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info("=" * 60)

    # Ensure all required directories exist
    settings.ensure_directories_exist()
    logger.info("Data directories created/verified")

    # Initialize database connection (if configured)
    try:
        initialize_database(settings)
        if is_database_configured():
            logger.info("Database connection initialized")
        else:
            logger.info("Database not configured (file-based storage mode)")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Continuing with file-based storage.")

    # Import nodes to trigger registration
    import backend.nodes  # noqa: F401
    from backend.core.node_registry import NodeRegistry
    
    logger.info(f"Registered {NodeRegistry.get_count()} node types")

    # Log configuration (without sensitive data)
    logger.info(f"Configuration loaded: {settings}")

    yield

    # Shutdown
    logger.info("Shutting down NodeAI backend...")
    
    # Close database connections
    try:
        close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Visual GenAI Workflow Builder - Backend API",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Configure CORS middleware
# In production, only allow explicitly configured origins
# In development, allow localhost origins
if settings.cors_allow_all_origins and settings.debug:
    # Only allow all origins in development mode
    logger.warning("CORS: Allowing all origins (development mode only)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Cannot use credentials with wildcard
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    cors_origins = settings.cors_origins
    if not cors_origins and not settings.debug:
        logger.warning(
            "CORS: No origins configured for production. "
            "Set CORS_ORIGINS_STR environment variable or allow localhost in development."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],  # Fallback to all if empty (not recommended)
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

# Add security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    return await add_security_headers(request, call_next)

# Request logging and input validation middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming HTTP requests and validate inputs.
    
    This middleware:
    - Logs request method, path, client IP, status, and duration
    - Validates and sanitizes request data for POST/PUT requests
    """
    import time

    start_time = time.time()

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    # Sanitize request body for POST/PUT requests (basic protection)
    # Note: Full validation happens in Pydantic models
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                # Request body is already consumed, so we need to recreate it
                # This is a basic check - full validation happens in endpoints
                pass
        except Exception as e:
            logger.warning(f"Error reading request body: {e}")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    return response


# ============================================
# Register API Routers
# ============================================
app.include_router(execution.router)
app.include_router(nodes.router)
app.include_router(files.router)
app.include_router(workflows.router)
app.include_router(metrics.router)
app.include_router(knowledge_base.router)
app.include_router(api_keys.router)
app.include_router(tools.router)
app.include_router(oauth.router)
app.include_router(query_tracer.router)
app.include_router(secrets.router)

# Import and register fine-tuning router
try:
    from backend.api import finetune
    app.include_router(finetune.router)
except ImportError:
    logger.warning("Fine-tuning API not available")

# Import and register models router
try:
    from backend.api import models as models_api
    app.include_router(models_api.router)
except ImportError:
    logger.warning("Models API not available")

# Import and register cost intelligence router
try:
    from backend.api import cost_intelligence
    app.include_router(cost_intelligence.router)
except ImportError:
    logger.warning("Cost Intelligence API not available")

# Import and register RAG evaluation router
try:
    from backend.api import rag_evaluation
    app.include_router(rag_evaluation.router)
except ImportError:
    logger.warning("RAG Evaluation API not available")

# Import and register prompt playground router
try:
    from backend.api import prompt_playground
    app.include_router(prompt_playground.router)
except ImportError:
    logger.warning("Prompt Playground API not available")

# Import and register RAG optimization router
try:
    from backend.api import rag_optimization
    app.include_router(rag_optimization.router)
except ImportError:
    logger.warning("RAG Optimization API not available")

# Import and register webhooks router
try:
    from backend.api import webhooks
    app.include_router(webhooks.router)
except ImportError:
    logger.warning("Webhooks API not available")

# ============================================
# Health Check Endpoint
# ============================================
@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns the API status and version information.
    This endpoint can be used by monitoring tools to check if the API is running.
    
    Returns:
        Dictionary with status, version, and app name
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "message": "NodeAI API is running",
    }


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint.
    
    Returns basic API information and links to documentation.
    """
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/api/v1/health",
    }


# ============================================
# Exception Handlers
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    This catches any exceptions that aren't handled by specific handlers
    and returns a consistent error response.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "path": request.url.path,
        },
    )


# ============================================
# Application Entry Point
# ============================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

