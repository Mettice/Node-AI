"""
Azure Blob Storage Integration

Provides file storage functionality using Azure Blob Storage.
Supports upload, download, list, delete, and URL generation operations.
"""

from typing import Any, Dict, List, Optional
from io import BytesIO

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import AzureError, ResourceNotFoundError

from backend.core.provider_registry import StorageProvider
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AzureBlobStorageProvider(StorageProvider):
    """
    Azure Blob Storage provider.
    
    Supports:
    - File upload
    - File download
    - List files
    - Delete files
    - Generate SAS URLs
    """

    def __init__(self, connection_string: str, container_name: str):
        """
        Initialize Azure Blob Storage provider.
        
        Args:
            connection_string: Azure Storage connection string
            container_name: Name of the blob container
        """
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client: Optional[ContainerClient] = None

    async def _ensure_container_exists(self) -> None:
        """Ensure the container exists, create if it doesn't."""
        if not self.container_client:
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
        try:
            # Check if container exists
            self.container_client.get_container_properties()
            logger.info(f"Container '{self.container_name}' already exists")
        except ResourceNotFoundError:
            # Container doesn't exist, create it
            logger.info(f"Creating container '{self.container_name}'")
            self.blob_service_client.create_container(self.container_name)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)

    async def upload(
        self, file_path: str, destination: str, config: Dict[str, Any]
    ) -> str:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Local file path to upload
            destination: Destination blob path in container
            config: Configuration dictionary
            
        Returns:
            Blob URL
        """
        await self._ensure_container_exists()
        
        blob_client = self.container_client.get_blob_client(destination)
        
        # Read file content
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=config.get("overwrite", True))
        
        blob_url = blob_client.url
        logger.info(f"Uploaded '{file_path}' to '{destination}' in container '{self.container_name}'")
        
        return blob_url

    async def download(
        self, source: str, destination: str, config: Dict[str, Any]
    ) -> str:
        """
        Download a file from Azure Blob Storage.
        
        Args:
            source: Blob path in container
            destination: Local file path to save
            config: Configuration dictionary
            
        Returns:
            Local file path
        """
        await self._ensure_container_exists()
        
        blob_client = self.container_client.get_blob_client(source)
        
        # Download blob content
        with open(destination, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        logger.info(f"Downloaded '{source}' to '{destination}'")
        
        return destination

    async def delete(self, path: str, config: Dict[str, Any]) -> bool:
        """
        Delete a file from Azure Blob Storage.
        
        Args:
            path: Blob path in container
            config: Configuration dictionary
            
        Returns:
            True if successful
        """
        await self._ensure_container_exists()
        
        blob_client = self.container_client.get_blob_client(path)
        
        try:
            blob_client.delete_blob()
            logger.info(f"Deleted blob '{path}' from container '{self.container_name}'")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob '{path}' not found")
            return False

    async def list(self, prefix: str, config: Dict[str, Any]) -> List[str]:
        """
        List files with prefix in Azure Blob Storage.
        
        Args:
            prefix: Prefix to filter blobs
            config: Configuration dictionary
            
        Returns:
            List of blob paths
        """
        await self._ensure_container_exists()
        
        max_results = config.get("max_results", 100)
        blobs = []
        
        blob_list = self.container_client.list_blobs(name_starts_with=prefix, max_results=max_results)
        
        for blob in blob_list:
            blobs.append(blob.name)
        
        logger.info(f"Listed {len(blobs)} blobs with prefix '{prefix}'")
        
        return blobs

    async def get_url(self, path: str, config: Dict[str, Any]) -> str:
        """
        Generate a SAS (Shared Access Signature) URL for a blob.
        
        Args:
            path: Blob path in container
            config: Configuration dictionary (can include expires_in_seconds)
            
        Returns:
            SAS URL
        """
        await self._ensure_container_exists()
        
        from azure.storage.blob import generate_container_sas, ContainerSasPermissions
        from datetime import datetime, timedelta
        from azure.storage.blob import BlobServiceClient
        
        blob_client = self.container_client.get_blob_client(path)
        
        # Check if blob exists
        try:
            blob_client.get_blob_properties()
        except ResourceNotFoundError:
            raise ValueError(f"Blob '{path}' not found")
        
        # Generate SAS token
        expires_in = config.get("expires_in_seconds", 3600)  # Default 1 hour
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Get account key from connection string
        account_name = self.blob_service_client.account_name
        account_key = self.blob_service_client.credential.account_key
        
        sas_token = generate_container_sas(
            account_name=account_name,
            container_name=self.container_name,
            account_key=account_key,
            permission=ContainerSasPermissions(read=True),
            expiry=expiry_time,
        )
        
        sas_url = f"{blob_client.url}?{sas_token}"
        
        logger.info(f"Generated SAS URL for '{path}' (expires in {expires_in} seconds)")
        
        return sas_url

    async def upload_from_bytes(
        self, content: bytes, destination: str, config: Dict[str, Any]
    ) -> str:
        """
        Upload content from bytes to Azure Blob Storage.
        
        Args:
            content: File content as bytes
            destination: Destination blob path in container
            config: Configuration dictionary
            
        Returns:
            Blob URL
        """
        await self._ensure_container_exists()
        
        blob_client = self.container_client.get_blob_client(destination)
        
        blob_client.upload_blob(content, overwrite=config.get("overwrite", True))
        
        blob_url = blob_client.url
        logger.info(f"Uploaded {len(content)} bytes to '{destination}' in container '{self.container_name}'")
        
        return blob_url

    async def download_to_bytes(self, source: str, config: Dict[str, Any]) -> bytes:
        """
        Download a file from Azure Blob Storage as bytes.
        
        Args:
            source: Blob path in container
            config: Configuration dictionary
            
        Returns:
            File content as bytes
        """
        await self._ensure_container_exists()
        
        blob_client = self.container_client.get_blob_client(source)
        
        content = blob_client.download_blob().readall()
        
        logger.info(f"Downloaded '{source}' ({len(content)} bytes)")
        
        return content

