"""
Video Frame Extractor Node for NodeAI.

This node extracts frames from video files for processing.
"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VideoFramesNode(BaseNode):
    """
    Video Frame Extractor Node.
    
    Extracts frames from video files for analysis.
    Supports frame extraction by FPS, count, or time intervals.
    """

    node_type = "video_frames"
    name = "Video Frames"
    description = "Extract frames from video files for processing or analysis."
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the video frame extractor node.
        
        Extracts frames from video files.
        """
        node_id = config.get("_node_id", "video_frames")
        
        await self.stream_progress(node_id, 0.1, "Preparing frame extraction...")
        
        # Get video path from inputs (from File Upload node)
        video_path = inputs.get("video_path") or inputs.get("text")  # Fallback to text if path passed as text
        
        if not video_path:
            raise ValueError("video_path is required. Connect a Video file from File Upload node.")
        
        # Validate path exists
        if isinstance(video_path, str):
            video_path = Path(video_path)
        
        if not video_path.exists():
            raise ValueError(f"Video file not found: {video_path}")
        
        await self.stream_progress(node_id, 0.3, f"Processing video: {video_path.name}")
        
        # Get extraction settings
        extraction_mode = config.get("extraction_mode", "fps")  # fps, count, interval
        fps = config.get("fps", 1.0)  # Frames per second to extract
        frame_count = config.get("frame_count", 10)  # Total number of frames to extract
        interval_seconds = config.get("interval_seconds", 5.0)  # Extract frame every N seconds
        include_base64 = config.get("include_base64", False)  # Include base64 encoded frames
        output_dir = config.get("output_dir", None)  # Optional: save frames to directory
        
        await self.stream_progress(node_id, 0.5, f"Extracting frames using {extraction_mode} mode...")
        
        # Extract frames
        frames, timestamps = await self._extract_frames(
            video_path, extraction_mode, fps, frame_count, interval_seconds, include_base64, output_dir, node_id
        )
        
        await self.stream_progress(node_id, 0.9, f"Extracted {len(frames)} frames")
        
        result = {
            "frames": frames,
            "timestamps": timestamps,
            "frame_count": len(frames),
            "metadata": {
                "source": "video_frames",
                "video_path": str(video_path),
                "extraction_mode": extraction_mode,
                "fps": fps if extraction_mode == "fps" else None,
                "frame_count": frame_count if extraction_mode == "count" else None,
                "interval_seconds": interval_seconds if extraction_mode == "interval" else None,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Frame extraction completed: {len(frames)} frames")
        
        return result
    
    async def _extract_frames(
        self,
        video_path: Path,
        extraction_mode: str,
        fps: float,
        frame_count: int,
        interval_seconds: float,
        include_base64: bool,
        output_dir: Optional[str],
        node_id: str,
    ) -> tuple[List[Dict[str, Any]], List[float]]:
        """Extract frames from video."""
        try:
            import cv2
        except ImportError:
            raise ImportError(
                "Video processing requires opencv-python. "
                "Install with: pip install opencv-python"
            )
        
        try:
            await self.stream_progress(node_id, 0.6, "Opening video file...")
            
            # Open video
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise ValueError(f"Failed to open video file: {video_path}")
            
            # Get video properties
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / video_fps if video_fps > 0 else 0
            
            await self.stream_progress(node_id, 0.65, f"Video: {duration:.1f}s, {total_frames} frames @ {video_fps:.2f} FPS")
            
            frames = []
            timestamps = []
            
            # Determine frame indices to extract
            if extraction_mode == "fps":
                # Extract frames at specified FPS
                frame_interval = int(video_fps / fps) if fps > 0 else 1
                frame_indices = list(range(0, total_frames, frame_interval))
            elif extraction_mode == "count":
                # Extract N evenly spaced frames
                if frame_count >= total_frames:
                    frame_indices = list(range(total_frames))
                else:
                    step = total_frames / frame_count
                    frame_indices = [int(i * step) for i in range(frame_count)]
            elif extraction_mode == "interval":
                # Extract frame every N seconds
                frame_interval = int(video_fps * interval_seconds)
                frame_indices = list(range(0, total_frames, frame_interval))
            else:
                raise ValueError(f"Unsupported extraction mode: {extraction_mode}")
            
            # Limit to reasonable number of frames
            if len(frame_indices) > 100:
                logger.warning(f"Limiting frame extraction to 100 frames (requested {len(frame_indices)})")
                frame_indices = frame_indices[:100]
            
            await self.stream_progress(node_id, 0.7, f"Extracting {len(frame_indices)} frames...")
            
            # Extract frames
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                timestamp = frame_idx / video_fps if video_fps > 0 else 0
                timestamps.append(timestamp)
                
                frame_data = {
                    "frame_number": frame_idx,
                    "timestamp": timestamp,
                }
                
                # Optionally save frame to file
                if output_dir:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    frame_file = output_path / f"frame_{frame_idx:06d}.jpg"
                    cv2.imwrite(str(frame_file), frame)
                    frame_data["file_path"] = str(frame_file)
                
                # Optionally include base64
                if include_base64:
                    await self.stream_progress(
                        node_id, 0.7 + (i / len(frame_indices)) * 0.2,
                        f"Encoding frame {i+1}/{len(frame_indices)}..."
                    )
                    # Encode frame as JPEG
                    import numpy as np
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    frame_data["base64"] = frame_base64
                    frame_data["data_url"] = f"data:image/jpeg;base64,{frame_base64}"
                
                frames.append(frame_data)
            
            cap.release()
            
            return frames, timestamps
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            raise ValueError(f"Frame extraction failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for video frame extractor configuration."""
        return {
            "type": "object",
            "properties": {
                "extraction_mode": {
                    "type": "string",
                    "title": "Extraction Mode",
                    "description": "How to extract frames",
                    "enum": ["fps", "count", "interval"],
                    "default": "fps",
                },
                "fps": {
                    "type": "number",
                    "title": "FPS (for fps mode)",
                    "description": "Frames per second to extract",
                    "default": 1.0,
                    "minimum": 0.1,
                    "maximum": 30.0,
                },
                "frame_count": {
                    "type": "integer",
                    "title": "Frame Count (for count mode)",
                    "description": "Total number of frames to extract",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                },
                "interval_seconds": {
                    "type": "number",
                    "title": "Interval (for interval mode)",
                    "description": "Extract frame every N seconds",
                    "default": 5.0,
                    "minimum": 0.1,
                },
                "include_base64": {
                    "type": "boolean",
                    "title": "Include Base64",
                    "description": "Include base64-encoded frames in output",
                    "default": False,
                },
                "output_dir": {
                    "type": "string",
                    "title": "Output Directory (Optional)",
                    "description": "Directory to save extracted frames (leave empty to skip saving)",
                    "default": "",
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "frames": {
                "type": "array",
                "description": "Extracted frames with metadata",
            },
            "timestamps": {
                "type": "array",
                "description": "Timestamps for each frame (in seconds)",
            },
            "frame_count": {
                "type": "integer",
                "description": "Number of frames extracted",
            },
            "metadata": {
                "type": "object",
                "description": "Extraction metadata",
            },
        }


# Register the node
NodeRegistry.register(
    VideoFramesNode.node_type,
    VideoFramesNode,
    VideoFramesNode().get_metadata(),
)

