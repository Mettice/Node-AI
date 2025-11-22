"""
Enhanced S3 Storage Node for NodeAI.

This node provides a dedicated interface for AWS S3 operations with better UX
than the generic tool node. Supports upload, download, list, delete, and more.
"""

import io
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    # Create dummy classes for type hints
    ClientError = Exception
    NoCredentialsError = Exception

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class S3Node(BaseNode):
    """
    Enhanced S3 Storage Node.
    
    Provides a dedicated interface for AWS S3 operations with better UX
    than the generic tool node.
    """

    node_type = "s3"
    name = "S3 Storage"
    description = "Upload, download, and manage files in AWS S3 with enhanced features"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute S3 operation.
        
        Supports: upload, download, list, delete, copy, move, get_url
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 package not installed. Install with: pip install boto3")
        
        node_id = config.get("_node_id", "s3")
        operation = config.get("s3_operation", "list")
        
        # Get AWS credentials
        access_key_id = config.get("s3_access_key_id") or config.get("aws_access_key_id")
        secret_access_key = config.get("s3_secret_access_key") or config.get("aws_secret_access_key")
        region = config.get("s3_region", "us-east-1")
        bucket = config.get("s3_bucket")
        
        if not access_key_id or not secret_access_key:
            raise ValueError("AWS Access Key ID and Secret Access Key are required")
        if not bucket:
            raise ValueError("S3 bucket name is required")
        
        await self.stream_progress(node_id, 0.1, f"Connecting to S3 bucket '{bucket}'...")
        
        try:
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
            
            await self.stream_progress(node_id, 0.3, f"Executing {operation} operation...")
            
            # Route to appropriate operation
            if operation == "upload":
                return await self._upload_file(s3_client, bucket, inputs, config, node_id)
            elif operation == "download":
                return await self._download_file(s3_client, bucket, inputs, config, node_id)
            elif operation == "list":
                return await self._list_files(s3_client, bucket, inputs, config, node_id)
            elif operation == "delete":
                return await self._delete_file(s3_client, bucket, inputs, config, node_id)
            elif operation == "copy":
                return await self._copy_file(s3_client, bucket, inputs, config, node_id)
            elif operation == "move":
                return await self._move_file(s3_client, bucket, inputs, config, node_id)
            elif operation == "get_url":
                return await self._get_presigned_url(s3_client, bucket, inputs, config, node_id)
            else:
                raise ValueError(f"Unsupported S3 operation: {operation}")
                
        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials provided")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            raise ValueError(f"AWS S3 error ({error_code}): {error_message}")
        except Exception as e:
            logger.error(f"S3 operation failed: {e}", exc_info=True)
            raise ValueError(f"S3 operation failed: {str(e)}")

    async def _upload_file(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Upload a file to S3."""
        # Get file data from inputs or config
        file_data = inputs.get("file_data") or inputs.get("data") or inputs.get("content")
        file_key = config.get("s3_key") or inputs.get("file_key") or inputs.get("key")
        
        if not file_data:
            raise ValueError("File data is required for upload operation")
        if not file_key:
            raise ValueError("S3 key (file path) is required for upload operation")
        
        # Handle different input formats
        if isinstance(file_data, str):
            # If it's a string, try to decode as base64 or use as text
            try:
                import base64
                file_bytes = base64.b64decode(file_data)
            except Exception:
                file_bytes = file_data.encode('utf-8')
        elif isinstance(file_data, dict):
            # If it's a dict, try to get the actual file content
            file_bytes = file_data.get("content") or file_data.get("data")
            if isinstance(file_bytes, str):
                file_bytes = file_bytes.encode('utf-8')
        else:
            file_bytes = file_data
        
        if not isinstance(file_bytes, bytes):
            file_bytes = str(file_bytes).encode('utf-8')
        
        await self.stream_progress(node_id, 0.5, f"Uploading file to s3://{bucket}/{file_key}...")
        
        # Get content type from config or infer from key
        content_type = config.get("s3_content_type") or self._infer_content_type(file_key)
        
        # Upload to S3
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        if config.get("s3_public", False):
            extra_args['ACL'] = 'public-read'
        
        s3_client.put_object(
            Bucket=bucket,
            Key=file_key,
            Body=file_bytes,
            **extra_args
        )
        
        await self.stream_progress(node_id, 0.9, "Upload complete!")
        
        # Generate URL
        url = f"https://{bucket}.s3.{s3_client.meta.region_name}.amazonaws.com/{file_key}"
        if config.get("s3_public", False):
            public_url = url
        else:
            public_url = None
        
        return {
            "output": {
                "status": "success",
                "operation": "upload",
                "bucket": bucket,
                "key": file_key,
                "url": url,
                "public_url": public_url,
                "size": len(file_bytes),
            },
            "file_url": url,
            "file_key": file_key,
            "bucket": bucket,
        }

    async def _download_file(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Download a file from S3."""
        file_key = config.get("s3_key") or inputs.get("file_key") or inputs.get("key")
        
        if not file_key:
            raise ValueError("S3 key (file path) is required for download operation")
        
        await self.stream_progress(node_id, 0.5, f"Downloading file from s3://{bucket}/{file_key}...")
        
        # Download from S3
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        file_content = response['Body'].read()
        
        await self.stream_progress(node_id, 0.9, "Download complete!")
        
        # Return file content as base64 for JSON serialization
        import base64
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        return {
            "output": {
                "status": "success",
                "operation": "download",
                "bucket": bucket,
                "key": file_key,
                "size": len(file_content),
                "content_type": response.get('ContentType'),
            },
            "file_data": file_content_b64,
            "file_content": file_content_b64,  # Alias for compatibility
            "file_key": file_key,
            "bucket": bucket,
        }

    async def _list_files(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """List files in S3 bucket."""
        prefix = config.get("s3_prefix") or inputs.get("prefix") or ""
        max_keys = config.get("s3_max_keys", 100)
        
        await self.stream_progress(node_id, 0.5, f"Listing files in s3://{bucket}/{prefix}...")
        
        # List objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        
        files = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "etag": obj['ETag'].strip('"'),
                    })
        
        await self.stream_progress(node_id, 0.9, f"Found {len(files)} files")
        
        return {
            "output": {
                "status": "success",
                "operation": "list",
                "bucket": bucket,
                "prefix": prefix,
                "count": len(files),
                "files": files,
            },
            "files": files,
            "file_list": files,  # Alias for compatibility
            "bucket": bucket,
        }

    async def _delete_file(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Delete a file from S3."""
        file_key = config.get("s3_key") or inputs.get("file_key") or inputs.get("key")
        
        if not file_key:
            raise ValueError("S3 key (file path) is required for delete operation")
        
        await self.stream_progress(node_id, 0.5, f"Deleting file s3://{bucket}/{file_key}...")
        
        # Delete from S3
        s3_client.delete_object(Bucket=bucket, Key=file_key)
        
        await self.stream_progress(node_id, 0.9, "Delete complete!")
        
        return {
            "output": {
                "status": "success",
                "operation": "delete",
                "bucket": bucket,
                "key": file_key,
            },
            "deleted_key": file_key,
            "bucket": bucket,
        }

    async def _copy_file(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Copy a file within S3."""
        source_key = config.get("s3_source_key") or inputs.get("source_key")
        dest_key = config.get("s3_dest_key") or inputs.get("dest_key")
        
        if not source_key or not dest_key:
            raise ValueError("Source key and destination key are required for copy operation")
        
        source_bucket = config.get("s3_source_bucket") or bucket
        
        await self.stream_progress(node_id, 0.5, f"Copying s3://{source_bucket}/{source_key} to s3://{bucket}/{dest_key}...")
        
        # Copy object
        copy_source = {'Bucket': source_bucket, 'Key': source_key}
        s3_client.copy_object(CopySource=copy_source, Bucket=bucket, Key=dest_key)
        
        await self.stream_progress(node_id, 0.9, "Copy complete!")
        
        return {
            "output": {
                "status": "success",
                "operation": "copy",
                "source_bucket": source_bucket,
                "source_key": source_key,
                "dest_bucket": bucket,
                "dest_key": dest_key,
            },
            "source_key": source_key,
            "dest_key": dest_key,
            "bucket": bucket,
        }

    async def _move_file(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Move (copy + delete) a file within S3."""
        source_key = config.get("s3_source_key") or inputs.get("source_key")
        dest_key = config.get("s3_dest_key") or inputs.get("dest_key")
        
        if not source_key or not dest_key:
            raise ValueError("Source key and destination key are required for move operation")
        
        # Copy first
        copy_result = await self._copy_file(s3_client, bucket, inputs, config, node_id)
        
        # Then delete source
        s3_client.delete_object(Bucket=bucket, Key=source_key)
        
        return {
            "output": {
                "status": "success",
                "operation": "move",
                "source_key": source_key,
                "dest_key": dest_key,
                "bucket": bucket,
            },
            "source_key": source_key,
            "dest_key": dest_key,
            "bucket": bucket,
        }

    async def _get_presigned_url(
        self,
        s3_client: Any,
        bucket: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Generate a presigned URL for S3 object."""
        file_key = config.get("s3_key") or inputs.get("file_key") or inputs.get("key")
        expiration = config.get("s3_url_expiration", 3600)  # Default 1 hour
        
        if not file_key:
            raise ValueError("S3 key (file path) is required for get_url operation")
        
        await self.stream_progress(node_id, 0.5, f"Generating presigned URL for s3://{bucket}/{file_key}...")
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': file_key},
            ExpiresIn=expiration,
        )
        
        await self.stream_progress(node_id, 0.9, "URL generated!")
        
        return {
            "output": {
                "status": "success",
                "operation": "get_url",
                "bucket": bucket,
                "key": file_key,
                "url": url,
                "expiration_seconds": expiration,
            },
            "url": url,
            "presigned_url": url,  # Alias
            "file_key": file_key,
            "bucket": bucket,
        }

    def _infer_content_type(self, file_key: str) -> Optional[str]:
        """Infer content type from file extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_key)
        return content_type

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for S3 node configuration."""
        return {
            "type": "object",
            "properties": {
                "s3_operation": {
                    "type": "string",
                    "enum": ["upload", "download", "list", "delete", "copy", "move", "get_url"],
                    "default": "list",
                    "title": "Operation",
                    "description": "S3 operation to perform",
                },
                "s3_access_key_id": {
                    "type": "string",
                    "title": "AWS Access Key ID",
                    "description": "AWS access key ID",
                },
                "s3_secret_access_key": {
                    "type": "string",
                    "title": "AWS Secret Access Key",
                    "description": "AWS secret access key",
                },
                "s3_bucket": {
                    "type": "string",
                    "title": "Bucket Name",
                    "description": "S3 bucket name",
                },
                "s3_region": {
                    "type": "string",
                    "default": "us-east-1",
                    "title": "Region",
                    "description": "AWS region",
                },
                "s3_key": {
                    "type": "string",
                    "title": "File Key/Path",
                    "description": "S3 object key (file path) - required for upload, download, delete, get_url",
                },
                "s3_prefix": {
                    "type": "string",
                    "title": "Prefix",
                    "description": "Prefix for listing files (optional)",
                },
                "s3_max_keys": {
                    "type": "integer",
                    "default": 100,
                    "title": "Max Keys",
                    "description": "Maximum number of files to list",
                },
                "s3_source_key": {
                    "type": "string",
                    "title": "Source Key",
                    "description": "Source file key for copy/move operations",
                },
                "s3_dest_key": {
                    "type": "string",
                    "title": "Destination Key",
                    "description": "Destination file key for copy/move operations",
                },
                "s3_source_bucket": {
                    "type": "string",
                    "title": "Source Bucket",
                    "description": "Source bucket for copy/move (defaults to same bucket)",
                },
                "s3_content_type": {
                    "type": "string",
                    "title": "Content Type",
                    "description": "Content type for upload (auto-detected if not provided)",
                },
                "s3_public": {
                    "type": "boolean",
                    "default": False,
                    "title": "Public Access",
                    "description": "Make uploaded file publicly accessible",
                },
                "s3_url_expiration": {
                    "type": "integer",
                    "default": 3600,
                    "title": "URL Expiration (seconds)",
                    "description": "Expiration time for presigned URLs (default: 1 hour)",
                },
            },
            "required": ["s3_operation", "s3_access_key_id", "s3_secret_access_key", "s3_bucket"],
        }


# Register the node
NodeRegistry.register(
    S3Node.node_type,
    S3Node,
    S3Node().get_metadata(),
)

