"""
Enhanced Google Drive Node for NodeAI.

This node provides a dedicated interface for Google Drive operations with OAuth support.
Supports uploading, downloading, listing, and sharing files.
"""

import base64
import json
from typing import Any, Dict, List, Optional

import httpx

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.oauth import OAuthManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleDriveNode(BaseNode):
    """
    Enhanced Google Drive Node.
    
    Provides a dedicated interface for Google Drive operations with OAuth support.
    """

    node_type = "google_drive"
    name = "Google Drive"
    description = "Upload, download, list, and share files in Google Drive using OAuth"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Google Drive operation.
        
        Supports: upload, download, list, share, create_folder
        """
        node_id = config.get("_node_id", "google_drive")
        operation = config.get("google_drive_operation", "list")
        
        # Get OAuth token
        token_id = config.get("google_drive_token_id")
        if not token_id:
            raise ValueError("Google Drive OAuth token ID is required. Please connect your Google account first.")
        
        token_data = OAuthManager.get_token(token_id)
        if not token_data:
            raise ValueError("Google Drive OAuth token not found. Please reconnect your Google account.")
        
        # Check if token is valid
        if not OAuthManager.is_token_valid(token_data):
            raise ValueError("Google Drive OAuth token has expired. Please reconnect your Google account.")
        
        access_token = token_data["access_token"]
        
        await self.stream_progress(node_id, 0.1, f"Executing Google Drive {operation}...")
        
        # Route to appropriate operation
        if operation == "upload":
            return await self._upload_file(access_token, inputs, config, node_id)
        elif operation == "download":
            return await self._download_file(access_token, inputs, config, node_id)
        elif operation == "list":
            return await self._list_files(access_token, inputs, config, node_id)
        elif operation == "share":
            return await self._share_file(access_token, inputs, config, node_id)
        elif operation == "create_folder":
            return await self._create_folder(access_token, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported Google Drive operation: {operation}")

    async def _upload_file(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        filename = config.get("google_drive_filename") or inputs.get("filename")
        file_content = config.get("google_drive_file_content") or inputs.get("file_content") or inputs.get("file_data")
        folder_id = config.get("google_drive_folder_id") or inputs.get("folder_id") or "root"
        mime_type = config.get("google_drive_mime_type") or "text/plain"
        
        if not filename:
            raise ValueError("Filename is required for upload")
        if not file_content:
            raise ValueError("File content is required for upload")
        
        await self.stream_progress(node_id, 0.3, f"Uploading {filename} to Google Drive...")
        
        # Handle file content - can be string or base64
        if isinstance(file_content, str):
            try:
                file_bytes = base64.b64decode(file_content)
            except:
                file_bytes = file_content.encode('utf-8')
        else:
            file_bytes = file_content
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First, create file metadata
            metadata = {
                "name": filename,
                "mimeType": mime_type,
            }
            if folder_id and folder_id != "root":
                metadata["parents"] = [folder_id]
            
            # Upload file using multipart upload
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body_parts = [
                f"--{boundary}",
                "Content-Type: application/json; charset=UTF-8",
                "",
                json.dumps(metadata),
                f"--{boundary}",
                f"Content-Type: {mime_type}",
                "",
                file_bytes.decode('utf-8', errors='ignore') if isinstance(file_bytes, bytes) else str(file_bytes),
                f"--{boundary}--",
            ]
            body = "\r\n".join(body_parts).encode('utf-8')
            
            response = await client.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": f"multipart/related; boundary={boundary}",
                },
                content=body,
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            file_data = response.json()
            
            await self.stream_progress(node_id, 1.0, f"File '{filename}' uploaded successfully!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "upload",
                    "file_id": file_data.get("id"),
                    "file_name": file_data.get("name"),
                    "file_url": f"https://drive.google.com/file/d/{file_data.get('id')}/view",
                },
                "file_id": file_data.get("id"),
                "file_url": f"https://drive.google.com/file/d/{file_data.get('id')}/view",
                "status": "uploaded",
            }

    async def _download_file(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Download a file from Google Drive."""
        file_id = config.get("google_drive_file_id") or inputs.get("file_id")
        
        if not file_id:
            raise ValueError("File ID is required for download")
        
        await self.stream_progress(node_id, 0.3, f"Downloading file {file_id}...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get file metadata first
            metadata_response = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                params={"fields": "id,name,mimeType"},
            )
            
            if metadata_response.status_code != 200:
                error_data = metadata_response.json() if metadata_response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {metadata_response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            file_metadata = metadata_response.json()
            
            # Download file content
            download_response = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            
            if download_response.status_code != 200:
                error_data = download_response.json() if download_response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {download_response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            file_content = download_response.content
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            await self.stream_progress(node_id, 1.0, "File downloaded successfully!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "download",
                    "file_id": file_id,
                    "file_name": file_metadata.get("name"),
                    "mime_type": file_metadata.get("mimeType"),
                    "size": len(file_content),
                },
                "file_data": file_content_b64,
                "file_content": file_content_b64,
                "file_name": file_metadata.get("name"),
                "file_id": file_id,
            }

    async def _list_files(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """List files in Google Drive."""
        folder_id = config.get("google_drive_folder_id") or inputs.get("folder_id") or "root"
        query = config.get("google_drive_query") or ""
        max_results = config.get("google_drive_max_results", 100)
        
        await self.stream_progress(node_id, 0.3, f"Listing files in folder {folder_id}...")
        
        # Build query
        query_parts = []
        if folder_id and folder_id != "root":
            query_parts.append(f"'{folder_id}' in parents")
        if query:
            query_parts.append(query)
        
        query_string = " and ".join(query_parts) if query_parts else ""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                params={
                    "q": query_string,
                    "pageSize": max_results,
                    "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink)",
                },
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            data = response.json()
            files = data.get("files", [])
            
            await self.stream_progress(node_id, 1.0, f"Found {len(files)} files")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "list",
                    "count": len(files),
                    "files": files,
                },
                "files": files,
                "file_list": files,
            }

    async def _share_file(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Share a file in Google Drive."""
        file_id = config.get("google_drive_file_id") or inputs.get("file_id")
        email = config.get("google_drive_share_email") or inputs.get("email")
        role = config.get("google_drive_share_role", "reader")  # reader, writer, commenter
        type_perm = config.get("google_drive_share_type", "user")  # user, group, domain, anyone
        
        if not file_id:
            raise ValueError("File ID is required for sharing")
        if not email and type_perm == "user":
            raise ValueError("Email is required for user sharing")
        
        await self.stream_progress(node_id, 0.3, f"Sharing file {file_id}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            permission = {
                "role": role,
                "type": type_perm,
            }
            if email:
                permission["emailAddress"] = email
            
            response = await client.post(
                f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=permission,
            )
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            permission_data = response.json()
            
            await self.stream_progress(node_id, 1.0, "File shared successfully!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "share",
                    "file_id": file_id,
                    "permission_id": permission_data.get("id"),
                },
                "permission_id": permission_data.get("id"),
                "status": "shared",
            }

    async def _create_folder(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create a folder in Google Drive."""
        folder_name = config.get("google_drive_folder_name") or inputs.get("folder_name")
        parent_folder_id = config.get("google_drive_parent_folder_id") or inputs.get("parent_folder_id") or "root"
        
        if not folder_name:
            raise ValueError("Folder name is required")
        
        await self.stream_progress(node_id, 0.3, f"Creating folder '{folder_name}'...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_folder_id and parent_folder_id != "root":
                metadata["parents"] = [parent_folder_id]
            
            response = await client.post(
                "https://www.googleapis.com/drive/v3/files",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=metadata,
            )
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Google Drive API error: {error_message}")
            
            folder_data = response.json()
            
            await self.stream_progress(node_id, 1.0, f"Folder '{folder_name}' created!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "create_folder",
                    "folder_id": folder_data.get("id"),
                    "folder_name": folder_data.get("name"),
                },
                "folder_id": folder_data.get("id"),
                "folder_name": folder_data.get("name"),
                "status": "created",
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Google Drive node configuration."""
        return {
            "type": "object",
            "properties": {
                "google_drive_operation": {
                    "type": "string",
                    "enum": ["upload", "download", "list", "share", "create_folder"],
                    "default": "list",
                    "title": "Operation",
                    "description": "Google Drive operation to perform",
                },
                "google_drive_token_id": {
                    "type": "string",
                    "title": "OAuth Token ID",
                    "description": "OAuth token ID from connected Google account",
                },
                "google_drive_file_id": {
                    "type": "string",
                    "title": "File ID",
                    "description": "Google Drive file ID (required for download, share)",
                },
                "google_drive_filename": {
                    "type": "string",
                    "title": "Filename",
                    "description": "Filename for upload",
                },
                "google_drive_file_content": {
                    "type": "string",
                    "title": "File Content",
                    "description": "File content (base64 or text) - required for upload",
                },
                "google_drive_folder_id": {
                    "type": "string",
                    "title": "Folder ID",
                    "description": "Google Drive folder ID (default: 'root')",
                },
                "google_drive_folder_name": {
                    "type": "string",
                    "title": "Folder Name",
                    "description": "Name for new folder (required for create_folder)",
                },
                "google_drive_parent_folder_id": {
                    "type": "string",
                    "title": "Parent Folder ID",
                    "description": "Parent folder ID for new folder (default: 'root')",
                },
                "google_drive_mime_type": {
                    "type": "string",
                    "title": "MIME Type",
                    "description": "MIME type for upload (default: 'text/plain')",
                },
                "google_drive_query": {
                    "type": "string",
                    "title": "Search Query",
                    "description": "Optional search query for listing files",
                },
                "google_drive_max_results": {
                    "type": "integer",
                    "default": 100,
                    "title": "Max Results",
                    "description": "Maximum number of files to list",
                },
                "google_drive_share_email": {
                    "type": "string",
                    "title": "Share Email",
                    "description": "Email address to share with (required for user sharing)",
                },
                "google_drive_share_role": {
                    "type": "string",
                    "enum": ["reader", "writer", "commenter"],
                    "default": "reader",
                    "title": "Share Role",
                    "description": "Permission role for sharing",
                },
                "google_drive_share_type": {
                    "type": "string",
                    "enum": ["user", "group", "domain", "anyone"],
                    "default": "user",
                    "title": "Share Type",
                    "description": "Type of sharing permission",
                },
            },
            "required": ["google_drive_operation", "google_drive_token_id"],
        }


# Register the node
NodeRegistry.register(
    GoogleDriveNode.node_type,
    GoogleDriveNode,
    GoogleDriveNode().get_metadata(),
)

