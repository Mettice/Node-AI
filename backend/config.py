"""
Configuration settings for NodeAI backend.

This module uses Pydantic Settings to load configuration from environment variables.
All settings are type-safe and validated on startup.
"""

from pathlib import Path
from typing import List, Optional
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root directory (parent of backend/)
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.resolve()
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Settings are loaded from:
    1. Environment variables
    2. .env file in the project root
    3. Default values (if specified)
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars not defined here
    )

    # ============================================
    # Application Information
    # ============================================
    app_name: str = Field(default="NodeAI", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    # ============================================
    # API Keys
    # ============================================
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings and chat completions",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API key for vector storage",
    )
    cohere_api_key: Optional[str] = Field(
        default=None,
        description="Cohere API key for reranking",
    )
    voyage_api_key: Optional[str] = Field(
        default=None,
        description="Voyage AI API key for embeddings and reranking",
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for embeddings and chat models",
    )
    neo4j_uri: Optional[str] = Field(
        default=None,
        description="Neo4j database URI (e.g., bolt://localhost:7687)",
    )
    neo4j_user: Optional[str] = Field(
        default=None,
        description="Neo4j database username",
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        description="Neo4j database password",
    )
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT token signing",
    )
    
    # ============================================
    # Intelligent Routing Configuration
    # ============================================
    enable_intelligent_routing: bool = Field(
        default=False,
        description="Enable intelligent data routing between nodes (uses LLM for semantic understanding)",
    )
    intelligent_router_provider: str = Field(
        default="openai",
        description="LLM provider for intelligent routing (openai, anthropic, gemini)",
    )
    intelligent_router_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model for intelligent routing (e.g., gpt-4o-mini, claude-3-5-sonnet-20241022)",
    )
    
    # ============================================
    # Supabase Configuration
    # ============================================
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL (e.g., https://xxx.supabase.co)",
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        description="Supabase anonymous key (public key)",
    )
    supabase_service_role_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key (private key, server-side only)",
    )
    vault_encryption_key: Optional[str] = Field(
        default=None,
        description="Master encryption key for secrets vault (32 bytes hex string)",
    )
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking (optional)",
    )
    sentry_environment: str = Field(
        default="development",
        description="Environment name for Sentry (development, staging, production)",
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry performance monitoring sample rate (0.0 to 1.0)",
    )

    # ============================================
    # Observability Configuration
    # ============================================
    langsmith_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key for observability (optional)",
    )
    langsmith_project: str = Field(
        default="nodeflow",
        description="LangSmith project name",
    )
    langfuse_public_key: Optional[str] = Field(
        default=None,
        description="LangFuse public key for observability (optional)",
    )
    langfuse_secret_key: Optional[str] = Field(
        default=None,
        description="LangFuse secret key for observability (optional)",
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="LangFuse host URL",
    )
    trace_storage_backend: str = Field(
        default="memory",
        description="Trace storage backend: 'memory' or 'database'",
    )
    trace_retention_days: int = Field(
        default=90,
        ge=1,
        description="Number of days to retain traces",
    )

    # ============================================
    # Server Configuration
    # ============================================
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server to",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for the backend API server",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode (True for development, False for production)",
    )

    # ============================================
    # CORS Configuration
    # ============================================
    cors_origins_str: Optional[str] = Field(
        default=None,
        description="Allowed origins for CORS (comma-separated string). If not set, uses defaults based on environment.",
    )
    cors_allow_all_origins: bool = Field(
        default=False,
        description="Allow all origins (only for development, not recommended for production)",
    )

    @property
    def cors_origins(self) -> List[str]:
        """
        Parse CORS origins from comma-separated string.
        
        In production, only allows explicitly configured origins.
        In development, allows localhost origins by default.
        """
        # If explicitly set, use that
        if self.cors_origins_str:
            if isinstance(self.cors_origins_str, str):
                origins = [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]
                if origins:
                    return origins
        
        # Production: require explicit configuration
        if not self.debug:
            # In production, default to empty list (no CORS) unless explicitly configured
            # This forces explicit configuration for security
            return []
        
        # Development: allow localhost origins
        return [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:8000",
        ]

    # ============================================
    # Data Storage Directories
    # ============================================
    data_dir: Path = Field(
        default=BACKEND_DIR / "data",
        description="Base directory for all data storage",
    )
    workflows_dir: Path = Field(
        default=BACKEND_DIR / "data" / "workflows",
        description="Directory for saved workflows (JSON files)",
    )
    executions_dir: Path = Field(
        default=BACKEND_DIR / "data" / "executions",
        description="Directory for execution traces and history",
    )
    vectors_dir: Path = Field(
        default=BACKEND_DIR / "data" / "vectors",
        description="Directory for vector indexes (FAISS)",
    )
    uploads_dir: Path = Field(
        default=BACKEND_DIR / "data" / "uploads",
        description="Directory for uploaded files",
    )

    @field_validator(
        "data_dir",
        "workflows_dir",
        "executions_dir",
        "vectors_dir",
        "uploads_dir",
        mode="before",
    )
    @classmethod
    def parse_path(cls, v):
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    # ============================================
    # Database Configuration
    # ============================================
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database connection URL (for Supabase). Format: postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres",
    )
    
    # Database Connection Pool Configuration
    db_pool_min_connections: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Minimum database connections in pool"
    )
    
    db_pool_max_connections: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Maximum database connections in pool"
    )

    # ============================================
    # Logging Configuration
    # ============================================
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional, leave empty for console only)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    # ============================================
    # Application Settings
    # ============================================
    max_upload_size: int = Field(
        default=10485760,  # 10MB
        ge=1,
        description="Maximum file upload size in bytes",
    )

    # ============================================
    # Feature Flags
    # ============================================
    enable_parallel_execution: bool = Field(
        default=True,
        description="Enable parallel node execution",
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching",
    )
    cache_ttl: int = Field(
        default=3600,  # 1 hour
        ge=1,
        description="Cache TTL in seconds",
    )

    def ensure_directories_exist(self) -> None:
        """
        Create all required directories if they don't exist.
        
        This should be called during application startup.
        """
        directories = [
            self.data_dir,
            self.workflows_dir,
            self.executions_dir,
            self.vectors_dir,
            self.uploads_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        """String representation, hiding sensitive information."""
        return (
            f"Settings("
            f"app_name={self.app_name!r}, "
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"debug={self.debug}, "
            f"data_dir={self.data_dir!r}"
            f")"
        )


# Global settings instance
# This will be imported and used throughout the application
settings = Settings()

