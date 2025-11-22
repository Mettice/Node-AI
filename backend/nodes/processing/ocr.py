"""
OCR Node for NodeAI.

This node extracts text from images using OCR (Optical Character Recognition).
Supports Tesseract OCR.
"""

import os
from pathlib import Path
from typing import Any, Dict

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OCRNode(BaseNode):
    """
    OCR Node.
    
    Extracts text from images using OCR.
    Supports Tesseract OCR engine.
    """

    node_type = "ocr"
    name = "OCR"
    description = "Extract text from images using Optical Character Recognition (OCR)."
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the OCR node.
        
        Extracts text from images using OCR.
        """
        node_id = config.get("_node_id", "ocr")
        
        await self.stream_progress(node_id, 0.1, "Preparing OCR...")
        
        # Get image path from inputs (from File Upload node)
        image_path = inputs.get("image_path") or inputs.get("text")  # Fallback to text if path passed as text
        
        if not image_path:
            raise ValueError("image_path is required. Connect an Image file from File Upload node.")
        
        # Validate path exists
        if isinstance(image_path, str):
            image_path = Path(image_path)
        
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")
        
        await self.stream_progress(node_id, 0.3, f"Processing image: {image_path.name}")
        
        # Get OCR engine (default: tesseract)
        engine = config.get("engine", "tesseract")
        language = config.get("language", "eng")
        
        await self.stream_progress(node_id, 0.5, f"Running OCR with {engine}...")
        
        # Perform OCR
        if engine == "tesseract":
            text, confidence = await self._ocr_tesseract(image_path, language, node_id)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")
        
        await self.stream_progress(node_id, 0.9, f"OCR complete: {len(text)} characters extracted")
        
        result = {
            "text": text,
            "confidence": confidence,
            "metadata": {
                "source": "ocr",
                "image_path": str(image_path),
                "engine": engine,
                "language": language,
                "text_length": len(text),
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"OCR completed: {len(text)} characters")
        
        return result
    
    async def _ocr_tesseract(self, image_path: Path, language: str, node_id: str) -> tuple[str, float]:
        """Extract text using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError(
                "Tesseract OCR requires pytesseract and Pillow. "
                "Install with: pip install pytesseract Pillow\n"
                "Also install Tesseract binary: https://github.com/tesseract-ocr/tesseract"
            )
        
        try:
            # Open image
            await self.stream_progress(node_id, 0.6, "Loading image...")
            with Image.open(image_path) as img:
                # Run OCR
                await self.stream_progress(node_id, 0.7, "Extracting text...")
                text = pytesseract.image_to_string(img, lang=language)
                
                # Get confidence scores
                await self.stream_progress(node_id, 0.8, "Calculating confidence...")
                data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return text.strip(), avg_confidence / 100.0  # Normalize to 0-1
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise ValueError(f"OCR extraction failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for OCR configuration."""
        return {
            "type": "object",
            "properties": {
                "engine": {
                    "type": "string",
                    "title": "OCR Engine",
                    "description": "OCR engine to use",
                    "enum": ["tesseract"],
                    "default": "tesseract",
                },
                "language": {
                    "type": "string",
                    "title": "Language",
                    "description": "Language code for OCR (e.g., 'eng', 'fra', 'spa')",
                    "default": "eng",
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Extracted text from image",
            },
            "confidence": {
                "type": "number",
                "description": "Average confidence score (0-1)",
            },
            "metadata": {
                "type": "object",
                "description": "OCR metadata",
            },
        }


# Register the node
NodeRegistry.register(
    OCRNode.node_type,
    OCRNode,
    OCRNode().get_metadata(),
)

