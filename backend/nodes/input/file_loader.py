"""
File Loader Node for NodeAI.

This node loads and processes uploaded files of various types:
- Documents: PDF, DOCX, TXT, MD
- Images: JPG, PNG, GIF, WEBP, BMP
- Audio: MP3, WAV, M4A, OGG, FLAC
- Video: MP4, AVI, MOV, MKV, WEBM
- Data: CSV, XLSX, JSON, Parquet
"""

import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Upload directory - use config if available, otherwise fallback to relative path
from backend.config import settings
UPLOAD_DIR = settings.uploads_dir if hasattr(settings, 'uploads_dir') else Path("uploads")


class FileLoaderNode(BaseNode):
    """
    File Loader Node.
    
    Universal file loader that handles multiple file types.
    Auto-detects file type and processes accordingly.
    """

    node_type = "file_loader"
    name = "File Upload"
    description = "Load and process uploaded files (Documents, Images, Audio, Video, Data)."
    category = "input"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the file loader node.
        
        Loads and processes files based on their type.
        """
        node_id = config.get("_node_id", "file_loader")
        
        # OPTIMIZATION: Skip if vector store already exists (for deployed workflows)
        if config.get("_skip_if_store_exists"):
            await self.stream_log(node_id, "Skipping file loading (vector store already exists)")
            # Return empty result - downstream nodes will also skip
            return {
                "text": "",
                "file_id": config.get("file_id", ""),
                "filename": "",
                "file_type": "",
                "file_category": "document",
                "length": 0,
            }
        
        await self.stream_progress(node_id, 0.1, "Locating file...")
        
        file_id = config.get("file_id")
        
        if not file_id:
            raise ValueError("file_id is required")
        
        # Find file - check all supported extensions
        all_extensions = [
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
        ]
        
        file_path = None
        for ext in all_extensions:
            candidate = UPLOAD_DIR / f"{file_id}{ext}"
            if candidate.exists():
                file_path = candidate
                break
        
        if not file_path or not file_path.exists():
            raise ValueError(f"File with ID {file_id} not found")
        
        await self.stream_progress(node_id, 0.3, f"Found file: {file_path.name}")
        
        # Determine file category
        ext = file_path.suffix.lower()
        file_category = self._get_file_category(ext)
        
        # Process based on file category
        if file_category == "document":
            return await self._process_document(file_path, file_id, node_id, config)
        elif file_category == "image":
            return await self._process_image(file_path, file_id, node_id, config)
        elif file_category == "audio":
            return await self._process_audio(file_path, file_id, node_id, config)
        elif file_category == "video":
            return await self._process_video(file_path, file_id, node_id, config)
        elif file_category == "data":
            return await self._process_data(file_path, file_id, node_id, config)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _get_file_category(self, ext: str) -> str:
        """Determine file category from extension."""
        document_exts = {".pdf", ".docx", ".txt", ".md", ".doc"}
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        audio_exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        data_exts = {".csv", ".xlsx", ".json", ".parquet"}
        
        if ext in document_exts:
            return "document"
        elif ext in image_exts:
            return "image"
        elif ext in audio_exts:
            return "audio"
        elif ext in video_exts:
            return "video"
        elif ext in data_exts:
            return "data"
        else:
            return "unknown"
    
    async def _process_document(
        self, file_path: Path, file_id: str, node_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document files (PDF, DOCX, TXT, MD)."""
        # Check if text already extracted
        text_file = file_path.with_suffix(".txt")
        if text_file.exists():
            logger.info(f"Loading cached text from {text_file}")
            await self.stream_log(node_id, f"Loading cached text from {text_file.name}")
            text = text_file.read_text(encoding="utf-8")
            await self.stream_progress(node_id, 0.8, "Text loaded from cache")
        else:
            # Extract text based on file type
            ext = file_path.suffix.lower()
            await self.stream_progress(node_id, 0.4, f"Extracting text from {ext} file...")
            
            if ext == ".pdf":
                text = await self._extract_pdf(file_path, node_id)
            elif ext in [".docx", ".doc"]:
                text = await self._extract_docx(file_path, node_id)
            elif ext in [".txt", ".md"]:
                text = file_path.read_text(encoding="utf-8")
            else:
                raise ValueError(f"Unsupported document type: {ext}")
            
            await self.stream_progress(node_id, 0.7, "Caching extracted text...")
            
            # Cache extracted text
            text_file.write_text(text, encoding="utf-8")
            logger.info(f"Cached extracted text to {text_file}")
        
        result = {
            "text": text,
            "metadata": {
                "source": "file_upload",
                "file_id": file_id,
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "file_category": "document",
                "length": len(text),
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Document loaded: {len(text)} characters")
        return result
    
    async def _process_image(
        self, file_path: Path, file_id: str, node_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process image files."""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Image processing requires Pillow. Install with: pip install Pillow")
        
        await self.stream_progress(node_id, 0.5, "Loading image...")
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format or "UNKNOWN"
            mode = img.mode
            file_size = file_path.stat().st_size
            
            await self.stream_progress(node_id, 0.7, f"Image loaded: {width}x{height} {format_name}")
            
            # Optionally encode to base64
            base64_encoded = None
            if config.get("include_base64", False):
                await self.stream_progress(node_id, 0.8, "Encoding image to base64...")
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                    base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
            
            result = {
                "image_path": str(file_path),
                "file_id": file_id,
                "metadata": {
                    "source": "file_upload",
                    "filename": file_path.name,
                    "file_type": file_path.suffix,
                    "file_category": "image",
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "mode": mode,
                    "size": file_size,
                },
            }
            
            if base64_encoded:
                result["base64"] = base64_encoded
                result["data_url"] = f"data:image/{format_name.lower()};base64,{base64_encoded}"
            
            await self.stream_progress(node_id, 1.0, f"Image loaded: {width}x{height}")
            return result
    
    async def _process_audio(
        self, file_path: Path, file_id: str, node_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process audio files."""
        await self.stream_progress(node_id, 0.5, "Loading audio file...")
        
        file_size = file_path.stat().st_size
        
        # For now, just return metadata - transcription will be handled by separate node
        result = {
            "audio_path": str(file_path),
            "file_id": file_id,
            "metadata": {
                "source": "file_upload",
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "file_category": "audio",
                "size": file_size,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Audio file loaded: {file_path.name}")
        return result
    
    async def _process_video(
        self, file_path: Path, file_id: str, node_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process video files."""
        await self.stream_progress(node_id, 0.5, "Loading video file...")
        
        file_size = file_path.stat().st_size
        
        # For now, just return metadata - frame extraction will be handled by separate node
        result = {
            "video_path": str(file_path),
            "file_id": file_id,
            "metadata": {
                "source": "file_upload",
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "file_category": "video",
                "size": file_size,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Video file loaded: {file_path.name}")
        return result
    
    async def _process_data(
        self, file_path: Path, file_id: str, node_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process data files (CSV, XLSX, JSON)."""
        await self.stream_progress(node_id, 0.5, "Loading data file...")
        
        ext = file_path.suffix.lower()
        file_size = file_path.stat().st_size
        
        # For now, just return metadata - data processing will be handled by separate node
        result = {
            "data_path": str(file_path),
            "file_id": file_id,
            "metadata": {
                "source": "file_upload",
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "file_category": "data",
                "size": file_size,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Data file loaded: {file_path.name}")
        return result

    async def _extract_pdf(self, file_path: Path, node_id: str) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
        except ImportError:
            try:
                import pdfplumber
            except ImportError:
                raise ImportError(
                    "PDF extraction requires either PyPDF2 or pdfplumber. "
                    "Install with: pip install PyPDF2 or pip install pdfplumber"
                )
            else:
                # Use pdfplumber
                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    total_pages = len(pdf.pages)
                    for i, page in enumerate(pdf.pages):
                        progress = 0.4 + (i / total_pages) * 0.3
                        await self.stream_progress(node_id, progress, f"Extracting page {i+1}/{total_pages}")
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                return "\n\n".join(text_parts)
        else:
            # Use PyPDF2
            text_parts = []
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                for i, page in enumerate(pdf_reader.pages):
                    progress = 0.4 + (i / total_pages) * 0.3
                    await self.stream_progress(node_id, progress, f"Extracting page {i+1}/{total_pages}")
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)

    async def _extract_docx(self, file_path: Path, node_id: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "DOCX extraction requires python-docx. "
                "Install with: pip install python-docx"
            )
        
        await self.stream_progress(node_id, 0.5, "Reading DOCX file...")
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        await self.stream_progress(node_id, 0.6, f"Extracted {len(paragraphs)} paragraphs")
        return "\n\n".join(paragraphs)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for file loader configuration."""
        return {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "title": "File ID",
                    "description": "ID of the uploaded file (from file upload)",
                    "default": "",
                },
                "include_base64": {
                    "type": "boolean",
                    "title": "Include Base64 (Images)",
                    "description": "Include base64-encoded image in output (for images only)",
                    "default": False,
                },
            },
            "required": ["file_id"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Extracted text (for documents)",
            },
            "image_path": {
                "type": "string",
                "description": "Path to image file (for images)",
            },
            "audio_path": {
                "type": "string",
                "description": "Path to audio file (for audio)",
            },
            "video_path": {
                "type": "string",
                "description": "Path to video file (for video)",
            },
            "data_path": {
                "type": "string",
                "description": "Path to data file (for data files)",
            },
            "base64": {
                "type": "string",
                "description": "Base64-encoded image (for images, if include_base64 is true)",
            },
            "data_url": {
                "type": "string",
                "description": "Data URL for image (for images, if include_base64 is true)",
            },
            "metadata": {
                "type": "object",
                "description": "File metadata (includes file_category: document/image/audio/video/data)",
            },
        }


# Register the node
NodeRegistry.register(
    FileLoaderNode.node_type,
    FileLoaderNode,
    FileLoaderNode().get_metadata(),
)

