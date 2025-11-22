"""
Azure Blob Storage Node for NodeAI.

This node provides a dedicated interface for Azure Blob Storage operations.
Supports upload, download, list, delete, copy, move, and URL generation.
"""

import io
import json
import base64
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.core.exceptions import AzureError, ResourceNotFoundError
    AZURE_BLOB_AVAILABLE = True
except ImportError:
    AZURE_BLOB_AVAILABLE = False
    AzureError = Exception
    ResourceNotFoundError = Exception

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AzureBlobNode(BaseNode):
    """
    Azure Blob Storage Node.
    
    Provides a dedicated interface for Azure Blob Storage operations.
    """

    node_type = "azure_blob"
    name = "Azure Blob Storage"
    description = "Upload, download, and manage files in Azure Blob Storage"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Azure Blob Storage operation.
        
        Supports: upload, download, list, delete, copy, move, get_url
        """
        if not AZURE_BLOB_AVAILABLE:
            raise ImportError("azure-storage-blob package not installed. Install with: pip install azure-storage-blob")
        
        node_id = config.get("_node_id", "azure_blob")
        operation = config.get("azure_blob_operation", "list")
        
        # Get Azure credentials
        connection_string = config.get("azure_blob_connection_string")
        container_name = config.get("azure_blob_container")
        
        if not connection_string:
            raise ValueError("Azure Blob Storage connection string is required")
        if not container_name:
            raise ValueError("Azure Blob Storage container name is required")
        
        await self.stream_progress(node_id, 0.1, f"Connecting to Azure Blob Storage container '{container_name}'...")
        
        try:
            # Create blob service client
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)
            
            # Ensure container exists
            try:
                container_client.get_container_properties()
            except ResourceNotFoundError:
                await self.stream_progress(node_id, 0.15, f"Creating container '{container_name}'...")
                blob_service_client.create_container(container_name)
                container_client = blob_service_client.get_container_client(container_name)
            
            await self.stream_progress(node_id, 0.3, f"Executing {operation} operation...")
            
            # Route to appropriate operation
            if operation == "upload":
                return await self._upload_file(container_client, inputs, config, node_id)
            elif operation == "download":
                return await self._download_file(container_client, inputs, config, node_id)
            elif operation == "list":
                return await self._list_files(container_client, inputs, config, node_id)
            elif operation == "delete":
                return await self._delete_file(container_client, inputs, config, node_id)
            elif operation == "copy":
                return await self._copy_file(container_client, inputs, config, node_id)
            elif operation == "move":
                return await self._move_file(container_client, inputs, config, node_id)
            elif operation == "get_url":
                return await self._get_sas_url(container_client, connection_string, container_name, inputs, config, node_id)
            else:
                raise ValueError(f"Unsupported Azure Blob operation: {operation}")
                
        except AzureError as e:
            raise ValueError(f"Azure Blob Storage error: {str(e)}")
        except Exception as e:
            logger.error(f"Azure Blob operation failed: {e}", exc_info=True)
            raise ValueError(f"Azure Blob operation failed: {str(e)}")

    async def _upload_file(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Upload a file to Azure Blob Storage."""
        # Get file data from inputs or config
        file_data = inputs.get("file_data") or inputs.get("data") or inputs.get("content")
        blob_name = config.get("azure_blob_name") or inputs.get("blob_name") or inputs.get("key")
        
        if not file_data:
            raise ValueError("File data is required for upload operation")
        if not blob_name:
            raise ValueError("Blob name (file path) is required for upload operation")
        
        # Handle different input formats
        if isinstance(file_data, str):
            # If it's a string, try to decode as base64 or use as text
            try:
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
        
        await self.stream_progress(node_id, 0.5, f"Uploading file to blob '{blob_name}'...")
        
        # Get content type from config or infer from blob name
        content_type = config.get("azure_blob_content_type") or self._infer_content_type(blob_name)
        
        # Upload to Azure Blob Storage
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_bytes,
            overwrite=config.get("azure_blob_overwrite", True),
            content_settings={"content_type": content_type} if content_type else None,
        )
        
        await self.stream_progress(node_id, 0.9, "Upload complete!")
        
        # Generate URL
        blob_url = blob_client.url
        
        return {
            "output": {
                "status": "success",
                "operation": "upload",
                "container": container_client.container_name,
                "blob_name": blob_name,
                "url": blob_url,
                "size": len(file_bytes),
            },
            "file_url": blob_url,
            "blob_name": blob_name,
            "container": container_client.container_name,
        }

    async def _download_file(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Download a file from Azure Blob Storage."""
        blob_name = config.get("azure_blob_name") or inputs.get("blob_name") or inputs.get("key")
        
        if not blob_name:
            raise ValueError("Blob name (file path) is required for download operation")
        
        await self.stream_progress(node_id, 0.5, f"Downloading blob '{blob_name}'...")
        
        # Download from Azure Blob Storage
        blob_client = container_client.get_blob_client(blob_name)
        
        try:
            blob_properties = blob_client.get_blob_properties()
            file_content = blob_client.download_blob().readall()
        except ResourceNotFoundError:
            raise ValueError(f"Blob '{blob_name}' not found in container")
        
        await self.stream_progress(node_id, 0.9, "Download complete!")
        
        # Return file content as base64 for JSON serialization
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        return {
            "output": {
                "status": "success",
                "operation": "download",
                "container": container_client.container_name,
                "blob_name": blob_name,
                "size": len(file_content),
                "content_type": blob_properties.content_settings.content_type if blob_properties.content_settings else None,
            },
            "file_data": file_content_b64,
            "file_content": file_content_b64,  # Alias for compatibility
            "blob_name": blob_name,
            "container": container_client.container_name,
        }

    async def _list_files(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """List files in Azure Blob Storage container."""
        prefix = config.get("azure_blob_prefix") or inputs.get("prefix") or ""
        max_results = config.get("azure_blob_max_results", 100)
        
        await self.stream_progress(node_id, 0.5, f"Listing blobs with prefix '{prefix}'...")
        
        # List blobs
        blobs = []
        blob_list = container_client.list_blobs(name_starts_with=prefix, max_results=max_results)
        
        for blob in blob_list:
            blobs.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                "content_type": blob.content_settings.content_type if blob.content_settings else None,
                "etag": blob.etag,
            })
        
        await self.stream_progress(node_id, 0.9, f"Found {len(blobs)} blobs")
        
        return {
            "output": {
                "status": "success",
                "operation": "list",
                "container": container_client.container_name,
                "prefix": prefix,
                "count": len(blobs),
                "blobs": blobs,
            },
            "files": blobs,
            "blobs": blobs,  # Alias
            "container": container_client.container_name,
        }

    async def _delete_file(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Delete a file from Azure Blob Storage."""
        blob_name = config.get("azure_blob_name") or inputs.get("blob_name") or inputs.get("key")
        
        if not blob_name:
            raise ValueError("Blob name (file path) is required for delete operation")
        
        await self.stream_progress(node_id, 0.5, f"Deleting blob '{blob_name}'...")
        
        # Delete from Azure Blob Storage
        blob_client = container_client.get_blob_client(blob_name)
        
        try:
            blob_client.delete_blob()
        except ResourceNotFoundError:
            logger.warning(f"Blob '{blob_name}' not found, may have already been deleted")
        
        await self.stream_progress(node_id, 0.9, "Delete complete!")
        
        return {
            "output": {
                "status": "success",
                "operation": "delete",
                "container": container_client.container_name,
                "blob_name": blob_name,
            },
            "deleted_blob": blob_name,
            "container": container_client.container_name,
        }

    async def _copy_file(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Copy a file within Azure Blob Storage."""
        source_blob = config.get("azure_blob_source") or inputs.get("source_blob")
        dest_blob = config.get("azure_blob_dest") or inputs.get("dest_blob")
        
        if not source_blob or not dest_blob:
            raise ValueError("Source blob and destination blob are required for copy operation")
        
        source_container = config.get("azure_blob_source_container") or container_client.container_name
        
        await self.stream_progress(node_id, 0.5, f"Copying blob '{source_blob}' to '{dest_blob}'...")
        
        # Copy blob
        dest_blob_client = container_client.get_blob_client(dest_blob)
        
        # Get source blob URL
        if source_container == container_client.container_name:
            source_blob_client = container_client.get_blob_client(source_blob)
            source_url = source_blob_client.url
        else:
            # Cross-container copy - need full URL
            # This would require the connection string to construct the URL
            raise ValueError("Cross-container copy not yet supported. Use same container for source and destination.")
        
        dest_blob_client.start_copy_from_url(source_url)
        
        await self.stream_progress(node_id, 0.9, "Copy complete!")
        
        return {
            "output": {
                "status": "success",
                "operation": "copy",
                "source_container": source_container,
                "source_blob": source_blob,
                "dest_container": container_client.container_name,
                "dest_blob": dest_blob,
            },
            "source_blob": source_blob,
            "dest_blob": dest_blob,
            "container": container_client.container_name,
        }

    async def _move_file(
        self,
        container_client: ContainerClient,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Move (copy + delete) a file within Azure Blob Storage."""
        source_blob = config.get("azure_blob_source") or inputs.get("source_blob")
        dest_blob = config.get("azure_blob_dest") or inputs.get("dest_blob")
        
        if not source_blob or not dest_blob:
            raise ValueError("Source blob and destination blob are required for move operation")
        
        # Copy first
        copy_result = await self._copy_file(container_client, inputs, config, node_id)
        
        # Then delete source
        blob_client = container_client.get_blob_client(source_blob)
        try:
            blob_client.delete_blob()
        except ResourceNotFoundError:
            logger.warning(f"Source blob '{source_blob}' not found during move")
        
        return {
            "output": {
                "status": "success",
                "operation": "move",
                "source_blob": source_blob,
                "dest_blob": dest_blob,
                "container": container_client.container_name,
            },
            "source_blob": source_blob,
            "dest_blob": dest_blob,
            "container": container_client.container_name,
        }

    async def _get_sas_url(
        self,
        container_client: ContainerClient,
        connection_string: str,
        container_name: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Generate a SAS (Shared Access Signature) URL for a blob."""
        blob_name = config.get("azure_blob_name") or inputs.get("blob_name") or inputs.get("key")
        expiration = config.get("azure_blob_url_expiration", 3600)  # Default 1 hour
        
        if not blob_name:
            raise ValueError("Blob name (file path) is required for get_url operation")
        
        await self.stream_progress(node_id, 0.5, f"Generating SAS URL for blob '{blob_name}'...")
        
        # Check if blob exists
        blob_client = container_client.get_blob_client(blob_name)
        try:
            blob_client.get_blob_properties()
        except ResourceNotFoundError:
            raise ValueError(f"Blob '{blob_name}' not found in container")
        
        # Generate SAS token
        from azure.storage.blob import generate_container_sas, ContainerSasPermissions
        from azure.storage.blob import BlobServiceClient
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        account_name = blob_service_client.account_name
        account_key = blob_service_client.credential.account_key
        
        expiry_time = datetime.utcnow() + timedelta(seconds=expiration)
        
        sas_token = generate_container_sas(
            account_name=account_name,
            container_name=container_name,
            account_key=account_key,
            permission=ContainerSasPermissions(read=True),
            expiry=expiry_time,
        )
        
        sas_url = f"{blob_client.url}?{sas_token}"
        
        await self.stream_progress(node_id, 0.9, "URL generated!")
        
        return {
            "output": {
                "status": "success",
                "operation": "get_url",
                "container": container_name,
                "blob_name": blob_name,
                "url": sas_url,
                "expiration_seconds": expiration,
            },
            "url": sas_url,
            "sas_url": sas_url,  # Alias
            "blob_name": blob_name,
            "container": container_name,
        }

    def _infer_content_type(self, blob_name: str) -> Optional[str]:
        """Infer content type from blob name extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(blob_name)
        return content_type

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Azure Blob Storage node configuration."""
        return {
            "type": "object",
            "properties": {
                "azure_blob_operation": {
                    "type": "string",
                    "enum": ["upload", "download", "list", "delete", "copy", "move", "get_url"],
                    "default": "list",
                    "title": "Operation",
                    "description": "Azure Blob Storage operation to perform",
                },
                "azure_blob_connection_string": {
                    "type": "string",
                    "title": "Connection String",
                    "description": "Azure Storage connection string",
                },
                "azure_blob_container": {
                    "type": "string",
                    "title": "Container Name",
                    "description": "Azure Blob Storage container name",
                },
                "azure_blob_name": {
                    "type": "string",
                    "title": "Blob Name/Path",
                    "description": "Blob name (file path) - required for upload, download, delete, get_url",
                },
                "azure_blob_prefix": {
                    "type": "string",
                    "title": "Prefix",
                    "description": "Prefix for listing blobs (optional)",
                },
                "azure_blob_max_results": {
                    "type": "integer",
                    "default": 100,
                    "title": "Max Results",
                    "description": "Maximum number of blobs to list",
                },
                "azure_blob_source": {
                    "type": "string",
                    "title": "Source Blob",
                    "description": "Source blob name for copy/move operations",
                },
                "azure_blob_dest": {
                    "type": "string",
                    "title": "Destination Blob",
                    "description": "Destination blob name for copy/move operations",
                },
                "azure_blob_source_container": {
                    "type": "string",
                    "title": "Source Container",
                    "description": "Source container for copy/move (defaults to same container)",
                },
                "azure_blob_content_type": {
                    "type": "string",
                    "title": "Content Type",
                    "description": "Content type for upload (auto-detected if not provided)",
                },
                "azure_blob_overwrite": {
                    "type": "boolean",
                    "default": True,
                    "title": "Overwrite",
                    "description": "Overwrite existing blob on upload",
                },
                "azure_blob_url_expiration": {
                    "type": "integer",
                    "default": 3600,
                    "title": "URL Expiration (seconds)",
                    "description": "Expiration time for SAS URLs (default: 1 hour)",
                },
            },
            "required": ["azure_blob_operation", "azure_blob_connection_string", "azure_blob_container"],
        }


# Register the node
NodeRegistry.register(
    AzureBlobNode.node_type,
    AzureBlobNode,
    AzureBlobNode().get_metadata(),
)

