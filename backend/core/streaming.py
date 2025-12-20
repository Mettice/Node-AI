"""
Streaming infrastructure for real-time execution updates.

This module provides a base streaming interface that all nodes can use
to send real-time updates during execution.
"""

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class StreamEventType(str, Enum):
    """Types of streaming events."""
    
    # Node-level events
    NODE_STARTED = "node_started"
    NODE_PROGRESS = "node_progress"
    NODE_OUTPUT = "node_output"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    
    # Agent-specific events (for CrewAI, LangChain agents)
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALLED = "agent_tool_called"
    AGENT_OUTPUT = "agent_output"
    AGENT_COMPLETED = "agent_completed"
    
    # Task-specific events (for CrewAI)
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    
    # Generic events
    LOG = "log"
    ERROR = "error"


class StreamEvent:
    """A single streaming event."""
    
    def __init__(
        self,
        event_type: StreamEventType,
        node_id: str,
        data: Dict[str, Any],
        execution_id: Optional[str] = None,
        agent: Optional[str] = None,
        task: Optional[str] = None,
    ):
        self.event_type = event_type
        self.node_id = node_id
        self.execution_id = execution_id
        self.agent = agent
        self.task = task
        self.data = data
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result = {
            "event_type": self.event_type.value,
            "node_id": self.node_id,
            "execution_id": self.execution_id,
            "agent": self.agent,
            "task": self.task,
            "timestamp": self.timestamp,
        }
        
        # For node_progress events, flatten progress and message to top level
        # This matches frontend expectations
        if self.event_type == StreamEventType.NODE_PROGRESS and isinstance(self.data, dict):
            if "progress" in self.data:
                result["progress"] = self.data["progress"]
            if "message" in self.data:
                result["message"] = self.data["message"]
            # Keep data field for backward compatibility
            result["data"] = self.data
        else:
            result["data"] = self.data
            # Also add message if present in data for other event types
            if isinstance(self.data, dict) and "message" in self.data:
                result["message"] = self.data["message"]
        
        return result
    
    def to_sse(self) -> str:
        """Convert event to Server-Sent Events format."""
        data = json.dumps(self.to_dict())
        return f"data: {data}\n\n"


class StreamManager:
    """
    Manages streaming events for executions.
    
    This is a singleton that tracks all active streams and allows
    nodes to publish events that will be sent to connected clients.
    """
    
    _instance: Optional["StreamManager"] = None
    _streams: Dict[str, asyncio.Queue] = {}
    _stream_timestamps: Dict[str, datetime] = {}  # Track creation time for cleanup
    _lock = asyncio.Lock()
    _cleanup_interval = 300  # 5 minutes in seconds
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def create_stream(self, execution_id: str) -> None:
        """Create a new stream for an execution."""
        async with self._lock:
            if execution_id not in self._streams:
                self._streams[execution_id] = asyncio.Queue()
                self._stream_timestamps[execution_id] = datetime.now()
                logger.info(f"Created stream for execution: {execution_id}")
                
                # Schedule automatic cleanup for old streams
                asyncio.create_task(self._schedule_cleanup())
    
    async def remove_stream(self, execution_id: str) -> None:
        """Remove a stream for an execution."""
        async with self._lock:
            if execution_id in self._streams:
                del self._streams[execution_id]
                if execution_id in self._stream_timestamps:
                    del self._stream_timestamps[execution_id]
                logger.info(f"Removed stream for execution: {execution_id}")
    
    async def publish(self, event: StreamEvent) -> None:
        """Publish an event to the appropriate stream."""
        if not event.execution_id:
            logger.warning(f"Event {event.event_type} has no execution_id, skipping")
            return
        
        async with self._lock:
            if event.execution_id in self._streams:
                await self._streams[event.execution_id].put(event)
            else:
                logger.debug(f"No stream found for execution: {event.execution_id}")
    
    async def subscribe(self, execution_id: str) -> AsyncIterator[StreamEvent]:
        """Subscribe to events for an execution."""
        await self.create_stream(execution_id)
        
        while True:
            try:
                # Wait for event with timeout to allow checking if stream still exists
                # Use a longer timeout to avoid premature closure
                event = await asyncio.wait_for(
                    self._streams[execution_id].get(),
                    timeout=30.0  # 30 second timeout - execution might take time
                )
                yield event
            except asyncio.TimeoutError:
                # Check if stream still exists - if it does, continue waiting
                async with self._lock:
                    if execution_id not in self._streams:
                        logger.info(f"Stream {execution_id} was removed, ending subscription")
                        break
                # Stream still exists, continue waiting for events
                logger.debug(f"Stream {execution_id} timeout, but stream still exists, continuing...")
                continue
            except Exception as e:
                logger.error(f"Error in stream subscription: {e}", exc_info=True)
                break
    
    async def _schedule_cleanup(self) -> None:
        """Schedule automatic cleanup of old streams."""
        try:
            await asyncio.sleep(self._cleanup_interval)
            await self._cleanup_old_streams()
        except Exception as e:
            logger.warning(f"Error in scheduled stream cleanup: {e}")
    
    async def _cleanup_old_streams(self) -> None:
        """Clean up streams that are older than the cleanup interval."""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(seconds=self._cleanup_interval)
        streams_to_remove = []
        
        async with self._lock:
            for execution_id, created_at in self._stream_timestamps.items():
                if created_at < cutoff_time:
                    streams_to_remove.append(execution_id)
            
            for execution_id in streams_to_remove:
                if execution_id in self._streams:
                    del self._streams[execution_id]
                if execution_id in self._stream_timestamps:
                    del self._stream_timestamps[execution_id]
                logger.info(f"Auto-cleaned up old stream: {execution_id}")
        
        if streams_to_remove:
            logger.info(f"Cleaned up {len(streams_to_remove)} old streams")


# Global stream manager instance
stream_manager = StreamManager()


class StreamableNode:
    """
    Mixin class for nodes that support streaming.
    
    Nodes can inherit from this or use it as a mixin to get
    streaming capabilities.
    """
    
    def __init__(self, execution_id: Optional[str] = None):
        self.execution_id = execution_id
    
    async def stream_event(
        self,
        event_type: StreamEventType,
        node_id: str,
        data: Dict[str, Any],
        agent: Optional[str] = None,
        task: Optional[str] = None,
    ) -> None:
        """Publish a streaming event."""
        if not self.execution_id:
            return
        
        event = StreamEvent(
            event_type=event_type,
            node_id=node_id,
            execution_id=self.execution_id,
            agent=agent,
            task=task,
            data=data,
        )
        await stream_manager.publish(event)
    
    async def stream_progress(
        self,
        node_id: str,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """Stream progress update (0.0 to 1.0)."""
        await self.stream_event(
            StreamEventType.NODE_PROGRESS,
            node_id,
            {"progress": progress, "message": message},
        )
    
    async def stream_output(
        self,
        node_id: str,
        output: Any,
        partial: bool = False,
    ) -> None:
        """Stream output update."""
        await self.stream_event(
            StreamEventType.NODE_OUTPUT,
            node_id,
            {"output": output, "partial": partial},
        )
    
    async def stream_log(
        self,
        node_id: str,
        message: str,
        level: str = "info",
    ) -> None:
        """Stream a log message."""
        await self.stream_event(
            StreamEventType.LOG,
            node_id,
            {"message": message, "level": level},
        )

