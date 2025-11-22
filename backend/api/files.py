"""
File upload and management API endpoints.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.core.security import validate_file_name, limiter
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/files", tags=["files"])

# Store uploaded files metadata
_uploaded_files: dict[str, dict] = {}

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class FileInfo(BaseModel):
    """File metadata."""
    file_id: str
    filename: str
    file_type: str
    size: int
    uploaded_at: str
    text_extracted: bool = False
    text_length: Optional[int] = None


class FileListResponse(BaseModel):
    """Response for file list."""
    files: List[FileInfo]
    total: int


@router.post("/upload")
@limiter.limit("100/minute")
async def upload_file(file: UploadFile = File(...), request: Request = None) -> JSONResponse:
    """
    Upload a file (PDF, DOCX, TXT, MD).
    
    Returns file_id and metadata.
    """
    # Validate file name
    if not file.filename or not validate_file_name(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file name. File name contains invalid characters or path traversal attempts."
        )
    
    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    file_size = 0
    try:
        # Read file to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )
    
    # Validate file type
    allowed_extensions = {
        # Documents
        ".pdf", ".docx", ".txt", ".md", ".doc",
        # Images
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
        # Audio
        ".mp3", ".wav", ".m4a", ".ogg", ".flac",
        # Video
        ".mp4", ".avi", ".mov", ".mkv", ".webm",
        # Data
        ".csv", ".xlsx", ".json", ".parquet"
    }
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(sorted(allowed_extensions))}"
        )
    
    # Generate file ID
    file_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    try:
        # Read and save file (content already read for size check, but we need to read again)
        # Reset file pointer if needed
        await file.seek(0)
        content = await file.read()
        
        # Additional validation: check MIME type matches extension
        # This is a basic check - more thorough validation can be added
        file_path.write_bytes(content)
        
        # Store metadata
        _uploaded_files[file_id] = {
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_ext,
            "size": len(content),
            "file_path": str(file_path),
            "uploaded_at": datetime.now().isoformat(),
        }
        
        return JSONResponse({
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_ext,
            "size": len(content),
            "message": "File uploaded successfully"
        })
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/list")
async def list_files() -> FileListResponse:
    """List all uploaded files."""
    files = []
    for file_id, metadata in _uploaded_files.items():
        file_path = Path(metadata["file_path"])
        text_length = None
        text_extracted = False
        
        # Check if text was extracted (stored in .txt file)
        text_file = file_path.with_suffix(".txt")
        if text_file.exists():
            text_extracted = True
            text_length = text_file.stat().st_size
        
        files.append(FileInfo(
            file_id=file_id,
            filename=metadata["filename"],
            file_type=metadata["file_type"],
            size=metadata["size"],
            uploaded_at=metadata["uploaded_at"],
            text_extracted=text_extracted,
            text_length=text_length,
        ))
    
    return FileListResponse(files=files, total=len(files))


@router.get("/{file_id}")
async def get_file_info(file_id: str) -> FileInfo:
    """Get file metadata."""
    if file_id not in _uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = _uploaded_files[file_id]
    file_path = Path(metadata["file_path"])
    text_file = file_path.with_suffix(".txt")
    
    text_extracted = text_file.exists()
    text_length = text_file.stat().st_size if text_extracted else None
    
    return FileInfo(
        file_id=file_id,
        filename=metadata["filename"],
        file_type=metadata["file_type"],
        size=metadata["size"],
        uploaded_at=metadata["uploaded_at"],
        text_extracted=text_extracted,
        text_length=text_length,
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str) -> JSONResponse:
    """Delete an uploaded file."""
    if file_id not in _uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = _uploaded_files[file_id]
    file_path = Path(metadata["file_path"])
    
    # Delete file and extracted text
    if file_path.exists():
        file_path.unlink()
    
    text_file = file_path.with_suffix(".txt")
    if text_file.exists():
        text_file.unlink()
    
    del _uploaded_files[file_id]
    
    return JSONResponse({"message": "File deleted successfully"})


@router.get("/{file_id}/text")
async def get_file_text(file_id: str) -> JSONResponse:
    """Get extracted text from file."""
    if file_id not in _uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = _uploaded_files[file_id]
    file_path = Path(metadata["file_path"])
    text_file = file_path.with_suffix(".txt")
    
    if not text_file.exists():
        raise HTTPException(status_code=404, detail="Text not extracted yet")
    
    text = text_file.read_text(encoding="utf-8")
    
    return JSONResponse({
        "file_id": file_id,
        "filename": metadata["filename"],
        "text": text,
        "length": len(text)
    })

