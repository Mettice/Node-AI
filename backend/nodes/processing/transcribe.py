"""
Transcription Node for NodeAI.

This node transcribes audio files using Whisper API (OpenAI or local).
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TranscribeNode(BaseNode):
    """
    Transcription Node.
    
    Transcribes audio files to text using Whisper API.
    Supports OpenAI Whisper API or local Whisper model.
    """

    node_type = "transcribe"
    name = "Transcribe"
    description = "Transcribe audio files to text using Whisper API (OpenAI or local)."
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the transcription node.
        
        Transcribes audio files to text.
        """
        node_id = config.get("_node_id", "transcribe")
        
        await self.stream_progress(node_id, 0.1, "Preparing transcription...")
        
        # Get audio path from inputs (from File Upload node)
        audio_path = inputs.get("audio_path") or inputs.get("text")  # Fallback to text if path passed as text
        
        if not audio_path:
            raise ValueError("audio_path is required. Connect an Audio file from File Upload node.")
        
        # Validate path exists
        if isinstance(audio_path, str):
            audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise ValueError(f"Audio file not found: {audio_path}")
        
        await self.stream_progress(node_id, 0.3, f"Processing audio: {audio_path.name}")
        
        # Get transcription settings
        provider = config.get("provider", "openai")  # openai or local
        model = config.get("model", "whisper-1")  # For OpenAI: whisper-1, For local: tiny/base/small/medium/large
        language = config.get("language", None)  # Optional: auto-detect if None
        response_format = config.get("response_format", "text")  # text, json, verbose_json, srt, vtt
        
        await self.stream_progress(node_id, 0.5, f"Transcribing with {provider}...")
        
        # Perform transcription
        if provider == "openai":
            transcript, segments = await self._transcribe_openai(audio_path, model, language, response_format, node_id)
        elif provider == "local":
            transcript, segments = await self._transcribe_local(audio_path, model, language, node_id)
        else:
            raise ValueError(f"Unsupported transcription provider: {provider}")
        
        await self.stream_progress(node_id, 0.9, f"Transcription complete: {len(transcript)} characters")
        
        result = {
            "text": transcript,
            "transcript": transcript,  # Alias for consistency
            "segments": segments,
            "metadata": {
                "source": "transcription",
                "audio_path": str(audio_path),
                "provider": provider,
                "model": model,
                "language": language,
                "text_length": len(transcript),
                "segment_count": len(segments) if segments else 0,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Transcription completed: {len(transcript)} characters")
        
        return result
    
    async def _transcribe_openai(
        self, audio_path: Path, model: str, language: Optional[str], response_format: str, node_id: str
    ) -> tuple[str, Optional[list]]:
        """Transcribe using OpenAI Whisper API."""
        try:
            from openai import AsyncOpenAI
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            client = AsyncOpenAI(api_key=api_key)
            
            await self.stream_progress(node_id, 0.6, "Uploading audio to OpenAI...")
            
            with open(audio_path, "rb") as audio_file:
                await self.stream_progress(node_id, 0.7, "Transcribing audio...")
                
                transcript_params = {
                    "model": model,
                    "file": audio_file,
                    "response_format": response_format,
                }
                
                if language:
                    transcript_params["language"] = language
                
                response = await client.audio.transcriptions.create(**transcript_params)
                
                await self.stream_progress(node_id, 0.8, "Processing transcription...")
                
                # Extract transcript and segments based on response format
                if response_format == "verbose_json":
                    transcript = response.text
                    segments = [
                        {
                            "id": seg.get("id"),
                            "start": seg.get("start"),
                            "end": seg.get("end"),
                            "text": seg.get("text"),
                        }
                        for seg in response.segments
                    ] if hasattr(response, "segments") else None
                elif response_format == "json":
                    transcript = response.text
                    segments = None
                else:
                    # text, srt, vtt formats
                    transcript = str(response)
                    segments = None
                
                return transcript, segments
                
        except ImportError:
            raise ImportError("OpenAI SDK is required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise ValueError(f"Transcription failed: {str(e)}")
    
    async def _transcribe_local(
        self, audio_path: Path, model: str, language: Optional[str], node_id: str
    ) -> tuple[str, Optional[list]]:
        """Transcribe using local Whisper model."""
        try:
            import whisper
        except ImportError:
            raise ImportError(
                "Local Whisper requires openai-whisper. "
                "Install with: pip install openai-whisper"
            )
        
        try:
            await self.stream_progress(node_id, 0.6, f"Loading Whisper model: {model}...")
            
            # Load model (this might take time on first run)
            whisper_model = whisper.load_model(model)
            
            await self.stream_progress(node_id, 0.7, "Transcribing audio...")
            
            # Transcribe
            result = whisper_model.transcribe(
                str(audio_path),
                language=language,  # None = auto-detect
                verbose=False,
            )
            
            await self.stream_progress(node_id, 0.8, "Processing transcription...")
            
            transcript = result["text"]
            segments = [
                {
                    "id": i,
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                }
                for i, seg in enumerate(result.get("segments", []))
            ]
            
            return transcript, segments
            
        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            raise ValueError(f"Transcription failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for transcription configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Provider",
                    "description": "Transcription provider",
                    "enum": ["openai", "local"],
                    "default": "openai",
                },
                "model": {
                    "type": "string",
                    "title": "Model",
                    "description": "Model to use (OpenAI: 'whisper-1', Local: 'tiny'/'base'/'small'/'medium'/'large')",
                    "default": "whisper-1",
                },
                "language": {
                    "type": "string",
                    "title": "Language (Optional)",
                    "description": "Language code (e.g., 'en', 'es', 'fr'). Leave empty for auto-detect.",
                    "default": "",
                },
                "response_format": {
                    "type": "string",
                    "title": "Response Format (OpenAI only)",
                    "description": "Response format for OpenAI API",
                    "enum": ["text", "json", "verbose_json", "srt", "vtt"],
                    "default": "text",
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Transcribed text",
            },
            "transcript": {
                "type": "string",
                "description": "Transcribed text (alias for text)",
            },
            "segments": {
                "type": "array",
                "description": "Transcription segments with timestamps (if available)",
            },
            "metadata": {
                "type": "object",
                "description": "Transcription metadata",
            },
        }


# Register the node
NodeRegistry.register(
    TranscribeNode.node_type,
    TranscribeNode,
    TranscribeNode().get_metadata(),
)

