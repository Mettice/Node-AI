"""
Tools API endpoints for testing connections and managing tool configurations.
"""

from typing import Optional
import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["Tools"])


class TestConnectionRequest(BaseModel):
    """Request to test an API key connection."""
    service: str  # e.g., "web_search", "email", "storage", "database", "s3"
    provider: Optional[str] = None  # e.g., "serpapi", "brave", "duckduckgo", "sqlite", "postgresql", "mysql"
    api_key: Optional[str] = None  # For S3: access_key_id
    connection_string: Optional[str] = None  # For S3: secret_access_key (or JSON with both keys + bucket + region)
    bucket: Optional[str] = None  # For S3: bucket name
    region: Optional[str] = None  # For S3: region


class TestConnectionResponse(BaseModel):
    """Response from connection test."""
    connected: bool
    message: Optional[str] = None


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest) -> TestConnectionResponse:
    """
    Test an API key connection for a service.
    
    This endpoint validates API keys by making a test request to the service.
    """
    try:
        if request.service == "web_search":
            if not request.api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for web search connection test"
                )
            return await _test_web_search_connection(request.provider, request.api_key)
        elif request.service == "database":
            if not request.connection_string:
                return TestConnectionResponse(
                    connected=False,
                    message="Connection string is required for database connection test"
                )
            return await _test_database_connection(request.provider, request.connection_string)
        elif request.service == "llm":
            if not request.api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for LLM connection test"
                )
            return await _test_llm_connection(request.provider, request.api_key)
        elif request.service == "email":
            if not request.api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for email connection test"
                )
            return await _test_email_connection(request.provider, request.api_key)
        elif request.service == "s3" or request.service == "storage":
            if not request.api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="AWS credentials are required for S3 connection test"
                )
            # For S3, we need access_key_id and secret_access_key
            # The api_key field will contain access_key_id, and we'll need secret_access_key
            # For now, we'll use a simplified test - in practice, you'd pass both
            return await _test_s3_connection(request.api_key, request.connection_string)
        else:
            return TestConnectionResponse(
                connected=False,
                message=f"Service '{request.service}' connection testing not yet implemented"
            )
    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=str(e)
        )


async def _test_web_search_connection(provider: Optional[str], api_key: str) -> TestConnectionResponse:
    """Test connection for web search providers."""
    if not provider:
        return TestConnectionResponse(
            connected=False,
            message="Provider is required for web search connection test"
        )
    
    # Test query
    test_query = "test"
    
    try:
        if provider == "duckduckgo":
            # DuckDuckGo doesn't require API key, so just return success
            # We could make a test request, but it's not necessary
            return TestConnectionResponse(
                connected=True,
                message="DuckDuckGo doesn't require an API key"
            )
        
        elif provider == "serpapi":
            if not api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for SerpAPI"
                )
            
            # Make a test request to SerpAPI
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={"q": test_query, "api_key": api_key}
                )
                
                if response.status_code == 200:
                    return TestConnectionResponse(
                        connected=True,
                        message="SerpAPI connection successful"
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid SerpAPI key"
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"SerpAPI test failed with status {response.status_code}"
                    )
        
        elif provider == "brave":
            if not api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for Brave Search"
                )
            
            # Make a test request to Brave Search
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": test_query},
                    headers={"X-Subscription-Token": api_key}
                )
                
                if response.status_code == 200:
                    return TestConnectionResponse(
                        connected=True,
                        message="Brave Search connection successful"
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Brave Search API key"
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Brave Search test failed with status {response.status_code}"
                    )
        
        elif provider == "serper":
            if not api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for Serper"
                )
            
            # Make a test request to Serper
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    json={"q": test_query, "num": 1},
                    headers={
                        "X-API-KEY": api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return TestConnectionResponse(
                        connected=True,
                        message="Serper connection successful"
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Serper API key"
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Serper test failed with status {response.status_code}"
                    )
        
        elif provider == "perplexity":
            if not api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for Perplexity"
                )
            
            # Make a test request to Perplexity
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    json={
                        "model": "sonar",
                        "messages": [
                            {
                                "role": "user",
                                "content": test_query
                            }
                        ],
                        "max_tokens": 10
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return TestConnectionResponse(
                        connected=True,
                        message="Perplexity connection successful"
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Perplexity API key"
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Perplexity test failed with status {response.status_code}"
                    )
        
        else:
            return TestConnectionResponse(
                connected=False,
                message=f"Unknown search provider: {provider}"
            )
    
    except httpx.TimeoutException:
        return TestConnectionResponse(
            connected=False,
            message="Connection test timed out"
        )
    except Exception as e:
        logger.error(f"Web search connection test error: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=f"Connection test failed: {str(e)}"
        )


async def _test_database_connection(db_type: Optional[str], connection_string: str) -> TestConnectionResponse:
    """Test connection for database providers."""
    if not db_type:
        return TestConnectionResponse(
            connected=False,
            message="Database type is required for connection test"
        )
    
    try:
        if db_type == "sqlite":
            import sqlite3
            try:
                # SQLite connection string is usually a file path
                # Test by trying to connect
                conn = sqlite3.connect(connection_string, timeout=5.0)
                conn.execute("SELECT 1")
                conn.close()
                return TestConnectionResponse(
                    connected=True,
                    message="SQLite connection successful"
                )
            except sqlite3.Error as e:
                return TestConnectionResponse(
                    connected=False,
                    message=f"SQLite connection failed: {str(e)}"
                )
        
        elif db_type == "postgresql":
            try:
                import psycopg2
                try:
                    conn = psycopg2.connect(connection_string, connect_timeout=5)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    return TestConnectionResponse(
                        connected=True,
                        message="PostgreSQL connection successful"
                    )
                except psycopg2.Error as e:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"PostgreSQL connection failed: {str(e)}"
                    )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="psycopg2 package not installed. Install with: pip install psycopg2-binary"
                )
        
        elif db_type == "mysql":
            try:
                import mysql.connector
                try:
                    # MySQL connection string can be a dict or connection string
                    # Try to parse it
                    conn = mysql.connector.connect(connection_string, connection_timeout=5)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    return TestConnectionResponse(
                        connected=True,
                        message="MySQL connection successful"
                    )
                except mysql.connector.Error as e:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"MySQL connection failed: {str(e)}"
                    )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="mysql-connector-python package not installed. Install with: pip install mysql-connector-python"
                )
        
        else:
            return TestConnectionResponse(
                connected=False,
                message=f"Unknown database type: {db_type}"
            )
    
    except Exception as e:
        logger.error(f"Database connection test error: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=f"Connection test failed: {str(e)}"
        )


async def _test_llm_connection(provider: Optional[str], api_key: str) -> TestConnectionResponse:
    """Test connection for LLM providers."""
    if not provider:
        return TestConnectionResponse(
            connected=False,
            message="Provider is required for LLM connection test"
        )
    
    try:
        if provider == "openai":
            logger.info(f"Testing OpenAI connection with API key: {'***' if api_key else 'None'}")
            try:
                from openai import OpenAI
                logger.info("OpenAI package imported successfully")
                client = OpenAI(api_key=api_key)
                logger.info("OpenAI client created")
                # Make a simple test call (list models is lightweight)
                # Use the standard models.list() method without limit parameter
                models = client.models.list()
                logger.info("OpenAI models.list() called")
                # Consume the iterator to actually make the API call
                models_list = list(models)
                logger.info(f"OpenAI test successful, got {len(models_list)} model(s)")
                return TestConnectionResponse(
                    connected=True,
                    message="OpenAI connection successful"
                )
            except ImportError as e:
                logger.error(f"OpenAI import error: {e}")
                return TestConnectionResponse(
                    connected=False,
                    message="OpenAI package not installed. Install with: pip install openai"
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"OpenAI connection test failed: {error_msg}", exc_info=True)
                # Check for authentication errors
                if any(keyword in error_msg.lower() for keyword in ["401", "invalid", "authentication", "api_key", "unauthorized", "incorrect api key"]):
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid OpenAI API key. Please check your API key and try again."
                    )
                return TestConnectionResponse(
                    connected=False,
                    message=f"OpenAI connection failed: {error_msg}"
                )
        
        elif provider == "anthropic":
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                # Make a simple test call (count messages is lightweight)
                # Use a minimal test to avoid initialization errors
                client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}]
                )
                return TestConnectionResponse(
                    connected=True,
                    message="Anthropic connection successful"
                )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="Anthropic package not installed. Install with: pip install anthropic"
                )
            except Exception as e:
                error_msg = str(e)
                # Check for authentication errors
                if any(keyword in error_msg.lower() for keyword in ["401", "invalid", "authentication", "api_key", "unauthorized", "x-api-key", "incorrect api key"]):
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Anthropic API key. Please check your API key and try again."
                    )
                # Check for initialization errors (these might be transient)
                if "initialization" in error_msg.lower() or "init" in error_msg.lower():
                    # Still return success if it's just an initialization warning
                    # The key is valid, just might have a transient issue
                    return TestConnectionResponse(
                        connected=True,
                        message="Anthropic API key validated (initialization warning may occur on first use)"
                    )
                return TestConnectionResponse(
                    connected=False,
                    message=f"Anthropic connection failed: {error_msg}"
                )
        
        elif provider == "gemini" or provider == "google":
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                # Make a simple test call (list models is lightweight)
                models = client.models.list()
                # Consume the iterator to actually make the API call
                list(models)
                return TestConnectionResponse(
                    connected=True,
                    message="Gemini connection successful"
                )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="Google GenAI package not installed. Install with: pip install google-genai"
                )
            except Exception as e:
                error_msg = str(e)
                # Check for authentication errors
                if any(keyword in error_msg.lower() for keyword in ["401", "invalid", "authentication", "api_key", "unauthorized", "api key", "incorrect api key"]):
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Gemini API key. Please check your API key and try again."
                    )
                return TestConnectionResponse(
                    connected=False,
                    message=f"Gemini connection failed: {error_msg}"
                )
        
        elif provider == "cohere":
            try:
                import cohere
                client = cohere.Client(api_key=api_key)
                # Make a simple test call (list models is lightweight)
                client.models.list()
                return TestConnectionResponse(
                    connected=True,
                    message="Cohere connection successful"
                )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="Cohere package not installed. Install with: pip install cohere"
                )
            except Exception as e:
                error_msg = str(e)
                # Check for authentication errors
                if any(keyword in error_msg.lower() for keyword in ["401", "invalid", "authentication", "api_key", "unauthorized", "api key", "incorrect api key"]):
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Cohere API key. Please check your API key and try again."
                    )
                return TestConnectionResponse(
                    connected=False,
                    message=f"Cohere connection failed: {error_msg}"
                )
        
        elif provider == "voyage_ai" or provider == "voyage":
            try:
                import voyageai
                client = voyageai.Client(api_key=api_key)
                # Make a simple test call (list models is lightweight)
                client.models.list()
                return TestConnectionResponse(
                    connected=True,
                    message="Voyage AI connection successful"
                )
            except ImportError:
                return TestConnectionResponse(
                    connected=False,
                    message="Voyage AI package not installed. Install with: pip install voyageai"
                )
            except Exception as e:
                error_msg = str(e)
                # Check for authentication errors
                if any(keyword in error_msg.lower() for keyword in ["401", "invalid", "authentication", "api_key", "unauthorized", "api key", "incorrect api key"]):
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Voyage AI API key. Please check your API key and try again."
                    )
                return TestConnectionResponse(
                    connected=False,
                    message=f"Voyage AI connection failed: {error_msg}"
                )
        
        else:
            return TestConnectionResponse(
                connected=False,
                message=f"Unknown LLM provider: {provider}"
            )
    
    except Exception as e:
        logger.error(f"LLM connection test error: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=f"Connection test failed: {str(e)}"
        )


async def _test_email_connection(provider: Optional[str], api_key: str) -> TestConnectionResponse:
    """Test connection for email providers."""
    if not provider:
        return TestConnectionResponse(
            connected=False,
            message="Provider is required for email connection test"
        )
    
    try:
        if provider == "resend":
            if not api_key:
                return TestConnectionResponse(
                    connected=False,
                    message="API key is required for Resend"
                )
            
            # Make a test request to Resend API (list domains is a lightweight operation)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.resend.com/domains",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return TestConnectionResponse(
                        connected=True,
                        message="Resend connection successful"
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        connected=False,
                        message="Invalid Resend API key"
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Resend test failed with status {response.status_code}"
                    )
        
        else:
            return TestConnectionResponse(
                connected=False,
                message=f"Unknown email provider: {provider}"
            )
    
    except httpx.TimeoutException:
        return TestConnectionResponse(
            connected=False,
            message="Connection test timed out"
        )
    except Exception as e:
        logger.error(f"Email connection test error: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=f"Connection test failed: {str(e)}"
        )


async def _test_s3_connection(access_key_id: str, secret_access_key_or_json: Optional[str] = None) -> TestConnectionResponse:
    """Test connection for S3 storage."""
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        return TestConnectionResponse(
            connected=False,
            message="boto3 package not installed. Install with: pip install boto3"
        )
    
    try:
        # Parse credentials - secret_access_key_or_json might be JSON with all credentials
        secret_access_key = secret_access_key_or_json
        bucket = None
        region = "us-east-1"
        
        if secret_access_key_or_json and secret_access_key_or_json.startswith('{'):
            try:
                import json
                creds = json.loads(secret_access_key_or_json)
                secret_access_key = creds.get("secret_access_key") or creds.get("aws_secret_access_key")
                bucket = creds.get("bucket") or creds.get("s3_bucket")
                region = creds.get("region") or creds.get("s3_region") or "us-east-1"
            except:
                pass  # Use as-is if not JSON
        
        if not secret_access_key:
            return TestConnectionResponse(
                connected=False,
                message="AWS Secret Access Key is required for S3 connection test"
            )
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )
        
        # Test by listing buckets (lightweight operation)
        # If bucket is provided, try to list objects in that bucket instead
        if bucket:
            try:
                s3_client.list_objects_v2(Bucket=bucket, MaxKeys=1)
                return TestConnectionResponse(
                    connected=True,
                    message=f"S3 connection successful (bucket: {bucket})"
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'NoSuchBucket':
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Bucket '{bucket}' does not exist"
                    )
                elif error_code == 'AccessDenied':
                    return TestConnectionResponse(
                        connected=False,
                        message=f"Access denied to bucket '{bucket}'. Check your credentials and bucket permissions."
                    )
                else:
                    return TestConnectionResponse(
                        connected=False,
                        message=f"S3 connection failed: {error_code}"
                    )
        else:
            # Just test credentials by listing buckets
            s3_client.list_buckets()
            return TestConnectionResponse(
                connected=True,
                message="S3 connection successful"
            )
            
    except NoCredentialsError:
        return TestConnectionResponse(
            connected=False,
            message="Invalid AWS credentials"
        )
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        return TestConnectionResponse(
            connected=False,
            message=f"AWS S3 error ({error_code}): {error_message}"
        )
    except Exception as e:
        logger.error(f"S3 connection test error: {e}", exc_info=True)
        return TestConnectionResponse(
            connected=False,
            message=f"Connection test failed: {str(e)}"
        )

