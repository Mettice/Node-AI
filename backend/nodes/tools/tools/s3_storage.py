"""
S3 Storage tool implementation.
Upload, download, list, and manage files in AWS S3 buckets.
"""

import httpx
import asyncio
import json
from typing import Dict, Any, Callable
from urllib.parse import urlparse

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def get_s3_storage_schema() -> Dict[str, Any]:
    """Get schema fields for S3 storage tool."""
    return {
        "s3_access_key_id": {
            "type": "string",
            "title": "AWS Access Key ID",
            "description": "AWS access key ID for authentication",
        },
        "s3_secret_access_key": {
            "type": "string",
            "title": "AWS Secret Access Key",
            "description": "AWS secret access key for authentication",
        },
        "s3_region": {
            "type": "string",
            "default": "us-east-1",
            "title": "AWS Region",
            "description": "AWS region where the bucket is located",
        },
        "s3_bucket": {
            "type": "string",
            "title": "S3 Bucket Name",
            "description": "Name of the S3 bucket",
        },
        "s3_action": {
            "type": "string",
            "enum": ["list", "upload", "download", "delete", "get_url"],
            "default": "list",
            "title": "Action",
            "description": "Action to perform on S3",
        },
    }


def _create_s3_client(config: Dict[str, Any]):
    """Create and return an S3 client."""
    if not BOTO3_AVAILABLE:
        raise ImportError("boto3 package not installed. Install with: pip install boto3")
    
    access_key = config.get("s3_access_key_id", "")
    secret_key = config.get("s3_secret_access_key", "")
    region = config.get("s3_region", "us-east-1")
    
    if not access_key or not secret_key:
        raise ValueError("AWS Access Key ID and Secret Access Key are required")
    
    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )


def create_s3_storage_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create S3 storage tool function."""
    bucket = config.get("s3_bucket", "")
    action = config.get("s3_action", "list")
    
    async def s3_storage_func_async(input_str: str) -> str:
        """Perform S3 operations."""
        if not BOTO3_AVAILABLE:
            return "Error: boto3 package not installed. Install with: pip install boto3"
        
        if not bucket:
            return "Error: S3 bucket name is required"
        
        try:
            s3_client = _create_s3_client(config)
            
            if action == "list":
                # List objects in bucket
                # Input: optional prefix (e.g., "folder/")
                prefix = input_str.strip() if input_str.strip() else ""
                max_keys = 100
                
                try:
                    if prefix:
                        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)
                    else:
                        response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=max_keys)
                    
                    if 'Contents' not in response:
                        return f"No objects found in bucket '{bucket}'" + (f" with prefix '{prefix}'" if prefix else "")
                    
                    objects = response['Contents']
                    result = f"Found {len(objects)} object(s) in bucket '{bucket}':\n\n"
                    
                    for obj in objects:
                        key = obj['Key']
                        size = obj['Size']
                        modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                        result += f"  {key}\n"
                        result += f"    Size: {size} bytes\n"
                        result += f"    Modified: {modified}\n\n"
                    
                    if response.get('IsTruncated'):
                        result += f"\n... (more objects available, showing first {max_keys})"
                    
                    return result
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchBucket':
                        return f"Error: Bucket '{bucket}' does not exist"
                    elif error_code == 'AccessDenied':
                        return f"Error: Access denied to bucket '{bucket}'. Check your credentials and permissions."
                    return f"Error: {str(e)}"
            
            elif action == "download":
                # Download object from S3
                # Input: object key (e.g., "path/to/file.txt")
                key = input_str.strip()
                if not key:
                    return "Error: Object key is required for download. Input: object key (e.g., 'path/to/file.txt')"
                
                try:
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    content = response['Body'].read()
                    
                    # Try to decode as text
                    try:
                        text_content = content.decode('utf-8')
                        return f"Content of '{key}':\n\n{text_content}"
                    except UnicodeDecodeError:
                        # Binary file
                        return f"Downloaded binary file '{key}' ({len(content)} bytes). Content cannot be displayed as text."
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchKey':
                        return f"Error: Object '{key}' not found in bucket '{bucket}'"
                    return f"Error: {str(e)}"
            
            elif action == "upload":
                # Upload content to S3
                # Input: JSON string with "key" and "content" (e.g., '{"key": "path/to/file.txt", "content": "file content"}')
                try:
                    upload_data = json.loads(input_str) if input_str.strip() else {}
                    key = upload_data.get("key", "")
                    content = upload_data.get("content", "")
                    
                    if not key:
                        return "Error: Object key is required. Input format: {\"key\": \"path/to/file.txt\", \"content\": \"file content\"}"
                    
                    # Upload to S3
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=content.encode('utf-8') if isinstance(content, str) else content
                    )
                    
                    return f"Successfully uploaded '{key}' to bucket '{bucket}'"
                    
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format. Expected: {\"key\": \"path/to/file.txt\", \"content\": \"file content\"}"
                except ClientError as e:
                    return f"Error: {str(e)}"
            
            elif action == "delete":
                # Delete object from S3
                # Input: object key (e.g., "path/to/file.txt")
                key = input_str.strip()
                if not key:
                    return "Error: Object key is required for deletion. Input: object key (e.g., 'path/to/file.txt')"
                
                try:
                    s3_client.delete_object(Bucket=bucket, Key=key)
                    return f"Successfully deleted '{key}' from bucket '{bucket}'"
                    
                except ClientError as e:
                    return f"Error: {str(e)}"
            
            elif action == "get_url":
                # Get presigned URL for object
                # Input: object key (e.g., "path/to/file.txt")
                key = input_str.strip()
                if not key:
                    return "Error: Object key is required. Input: object key (e.g., 'path/to/file.txt')"
                
                try:
                    # Generate presigned URL (valid for 1 hour)
                    url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': key},
                        ExpiresIn=3600
                    )
                    return f"Presigned URL for '{key}' (valid for 1 hour):\n{url}"
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchKey':
                        return f"Error: Object '{key}' not found in bucket '{bucket}'"
                    return f"Error: {str(e)}"
            
            else:
                return f"Error: Unknown action '{action}'"
                
        except NoCredentialsError:
            return "Error: AWS credentials not found. Please provide Access Key ID and Secret Access Key."
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Wrapper to make async function work with LangChain Tool
    def s3_storage_func(input_str: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(s3_storage_func_async(input_str))
        except RuntimeError:
            return asyncio.run(s3_storage_func_async(input_str))
    
    return s3_storage_func

