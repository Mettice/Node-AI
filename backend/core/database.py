"""
Database connection and utilities for Supabase PostgreSQL.

This module provides database connection management and utilities for interacting
with Supabase PostgreSQL database.
"""

import os
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from supabase import create_client, Client

from backend.config import Settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Global connection pool
_connection_pool: Optional[ThreadedConnectionPool] = None
_supabase_client: Optional[Client] = None
_settings: Optional[Settings] = None


def initialize_database(settings: Settings) -> None:
    """
    Initialize database connection pool and Supabase client.
    
    Args:
        settings: Application settings containing database configuration
    """
    global _connection_pool, _supabase_client, _settings
    
    _settings = settings
    
    # Initialize Supabase client if configured
    if settings.supabase_url:
        try:
            # Use service role key for administrative operations if available
            # This allows us to bypass RLS for system operations while still respecting user context
            supabase_key = getattr(settings, 'supabase_service_role_key', None) or settings.supabase_anon_key
            
            if supabase_key:
                _supabase_client = create_client(
                    settings.supabase_url,
                    supabase_key
                )
                logger.info(f"Supabase client initialized successfully (using {'service role' if supabase_key != settings.supabase_anon_key else 'anonymous'} key)")
            else:
                logger.warning("No Supabase key available (neither service role nor anonymous key)")
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    # Initialize PostgreSQL connection pool if configured
    if settings.supabase_url:
        # Extract database connection string from Supabase URL
        # Supabase URL format: https://xxx.supabase.co
        # Connection string format: postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
        # Try to get from settings first, then fallback to environment variable
        db_url = getattr(settings, 'database_url', None) or os.getenv("DATABASE_URL")
        
        # If DATABASE_URL is incomplete, try to fix it
        if db_url:
            # Extract project reference from SUPABASE_URL to validate DATABASE_URL
            project_ref = None
            if settings.supabase_url:
                # Extract project ref from URL like https://xxx.supabase.co
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(settings.supabase_url)
                    # Get subdomain (project ref)
                    hostname = parsed.hostname or ''
                    if '.supabase.co' in hostname:
                        project_ref = hostname.replace('.supabase.co', '')
                except Exception:
                    pass
            
            # Fix common issues with DATABASE_URL
            # 1. Add 'db.' prefix if missing (Supabase requires db. prefix)
            if '@' in db_url and '.supabase.co' in db_url:
                parts = db_url.split('@')
                if len(parts) == 2:
                    host = parts[1].split('/')[0].split(':')[0]
                    if not host.startswith('db.'):
                        # Replace the host with db. prefix
                        db_url = db_url.replace(f'@{host}', f'@db.{host}')
                        logger.info(f"Fixed DATABASE_URL: Added 'db.' prefix to hostname")
                    
                    # Validate hostname matches project ref if available
                    if project_ref and project_ref not in host:
                        logger.warning(
                            f"DATABASE_URL hostname '{host}' doesn't match project ref '{project_ref}'. "
                            f"Please verify your DATABASE_URL is correct."
                        )
            
            # 2. Add port if missing
            if '@' in db_url and ':5432' not in db_url and ':6543' not in db_url:
                # Insert port before the host
                parts = db_url.split('@')
                if len(parts) == 2:
                    host_part = parts[1]
                    if ':' not in host_part.split('/')[0]:
                        # No port specified, add default 5432
                        host = host_part.split('/')[0]
                        rest = '/' + '/'.join(host_part.split('/')[1:]) if '/' in host_part else ''
                        db_url = f"{parts[0]}@{host}:5432{rest}"
                        logger.info(f"Fixed DATABASE_URL: Added port 5432")
            
            # 3. Add database name if missing
            if not db_url.endswith('/postgres') and '/' not in db_url.split('@')[-1].split(':')[-1]:
                db_url = db_url + '/postgres'
                logger.info(f"Fixed DATABASE_URL: Added database name '/postgres'")
            
            # Log the (masked) final URL for debugging
            if '@' in db_url:
                masked_url = db_url.split('@')[0] + '@' + '***@' + db_url.split('@')[1] if '@' in db_url else db_url
                logger.debug(f"Using DATABASE_URL: {masked_url}")
        
        if db_url:
            try:
                # Test the connection first
                test_conn = psycopg2.connect(db_url, connect_timeout=5)
                test_conn.close()
                logger.info("Database connection test successful")
                
                # Create connection pool
                # minconn=1, maxconn=10 connections
                _connection_pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=db_url
                )
                logger.info("Database connection pool initialized successfully")
            except psycopg2.OperationalError as e:
                logger.error(f"Failed to connect to database: {e}")
                logger.warning("Database connection pool not initialized. Will use Supabase client as fallback.")
                # Don't raise - allow Supabase client to be used as fallback
            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {e}")
                logger.warning("Database connection pool not initialized. Will use Supabase client as fallback.")
                # Don't raise - allow Supabase client to be used as fallback
        else:
            logger.warning(
                "DATABASE_URL not set. Database connection pool not initialized. "
                "Will use Supabase client if available."
            )


def get_supabase_client() -> Optional[Client]:
    """
    Get the Supabase client instance.
    
    Returns:
        Supabase client or None if not initialized
    """
    return _supabase_client


def get_user_supabase_client(user_jwt_token: str) -> Optional[Client]:
    """
    Get a Supabase client authenticated with a user's JWT token.
    
    This creates a client that respects RLS policies for the specific user.
    
    Args:
        user_jwt_token: User's JWT token from authentication
        
    Returns:
        Authenticated Supabase client or None if not configured
    """
    if not _settings or not _settings.supabase_url or not _settings.supabase_anon_key:
        return None
        
    try:
        # Create a new client with anonymous key
        client = create_client(_settings.supabase_url, _settings.supabase_anon_key)
        
        # Override the client's default headers to include the user's JWT token
        # This ensures RLS policies can access auth.uid()
        original_headers = getattr(client, '_client', client).headers if hasattr(client, '_client') else {}
        auth_headers = {
            **original_headers,
            'Authorization': f'Bearer {user_jwt_token}',
            'apikey': _settings.supabase_anon_key
        }
        
        # Set headers on the underlying client
        if hasattr(client, '_client'):
            client._client.headers.update(auth_headers)
        elif hasattr(client, 'headers'):
            client.headers.update(auth_headers)
        
        return client
    except Exception as e:
        logger.error(f"Failed to create user-authenticated Supabase client: {e}")
        return None


@contextmanager
def get_db_connection():
    """
    Get a database connection from the pool.
    
    This is a context manager that yields a connection.
    The connection is automatically returned to the pool after use.
    
    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM workflows")
                result = cur.fetchall()
    
    Yields:
        Database connection
    """
    if _connection_pool is None:
        raise RuntimeError(
            "Database connection pool not initialized. "
            "Call initialize_database() first."
        )
    
    conn = _connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _connection_pool.putconn(conn)


def close_database() -> None:
    """Close all database connections and cleanup."""
    global _connection_pool
    
    if _connection_pool:
        _connection_pool.closeall()
        logger.info("Database connection pool closed")


def is_database_configured() -> bool:
    """
    Check if database is configured and connection pool is initialized.
    
    Returns:
        True if database connection pool exists, False otherwise
    """
    return _connection_pool is not None


def is_supabase_configured() -> bool:
    """
    Check if Supabase client is configured.
    
    Returns:
        True if Supabase client is initialized, False otherwise
    """
    return _supabase_client is not None and _settings is not None and _settings.supabase_url is not None


def execute_query(query: str, params: Optional[tuple] = None) -> list:
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
        
    Returns:
        List of result rows as dictionaries
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """
    Execute an INSERT/UPDATE/DELETE query.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
        
    Returns:
        Number of affected rows
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount

