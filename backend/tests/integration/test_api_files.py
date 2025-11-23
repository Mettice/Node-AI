"""
Integration tests for file upload API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from backend.main import app

client = TestClient(app)


class TestFileUploadAPI:
    """Test file upload API endpoints."""
    
    def test_list_files(self):
        """Test listing files."""
        response = client.get("/api/v1/files/list")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)
        assert "total" in data
    
    def test_upload_file_valid(self):
        """Test uploading a valid file."""
        # Create a test file
        test_file = BytesIO(b"Test file content")
        test_file.name = "test.txt"
        
        response = client.post(
            "/api/v1/files/upload",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.txt"
        assert data["file_type"] == ".txt"
    
    def test_upload_file_invalid_extension(self):
        """Test uploading file with invalid extension."""
        test_file = BytesIO(b"Test content")
        test_file.name = "test.exe"
        
        response = client.post(
            "/api/v1/files/upload",
            files={"file": ("test.exe", test_file, "application/x-msdownload")}
        )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_file_path_traversal(self):
        """Test uploading file with path traversal in name."""
        test_file = BytesIO(b"Test content")
        test_file.name = "../../../etc/passwd"
        
        response = client.post(
            "/api/v1/files/upload",
            files={"file": ("../../../etc/passwd", test_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_file_info_not_found(self):
        """Test getting file info for non-existent file."""
        response = client.get("/api/v1/files/nonexistent-id")
        assert response.status_code == 404

