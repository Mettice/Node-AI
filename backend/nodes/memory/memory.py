"""
Memory Node for NodeAI.

This node stores and retrieves conversation history and context.
Supports:
- Short-term memory (current conversation)
- Long-term memory (persistent across sessions)
- Semantic search for relevant past conversations
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory storage for conversations
# In production, this would be a database
_memory_stores: Dict[str, List[Dict[str, Any]]] = {}


class MemoryNode(BaseNode):
    """
    Memory Node for storing and retrieving conversation history.
    
    Supports:
    - Store: Save messages to memory
    - Retrieve: Get relevant past conversations
    - Clear: Clear memory for a session
    """

    node_type = "memory"
    name = "Memory"
    description = "Store and retrieve conversation history and context"
    category = "memory"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the memory node.
        
        Operations:
        - store: Save messages to memory
        - retrieve: Get relevant past conversations
        - clear: Clear memory for a session
        """
        node_id = config.get("_node_id", "memory")
        operation = config.get("operation", "retrieve")
        session_id = config.get("session_id", "default")
        
        await self.stream_progress(node_id, 0.1, f"Memory operation: {operation} (session: {session_id})")
        
        # Initialize session if it doesn't exist
        if session_id not in _memory_stores:
            _memory_stores[session_id] = []
        
        if operation == "store":
            return await self._store_memory(inputs, config, session_id, node_id)
        elif operation == "retrieve":
            return await self._retrieve_memory(inputs, config, session_id, node_id)
        elif operation == "clear":
            return await self._clear_memory(session_id, node_id)
        else:
            raise ValueError(f"Unknown memory operation: {operation}")

    async def _store_memory(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        session_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """Store messages in memory."""
        await self.stream_progress(node_id, 0.3, "Storing message in memory...")
        
        # Get message from inputs
        message = inputs.get("message") or config.get("message")
        role = inputs.get("role") or config.get("role", "user")
        
        if not message:
            raise ValueError("Message is required for store operation")
        
        # Create memory entry
        memory_entry = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": inputs.get("metadata", {}),
        }
        
        # Store in memory
        _memory_stores[session_id].append(memory_entry)
        
        logger.info(f"Stored message in memory (session: {session_id}, total: {len(_memory_stores[session_id])})")
        
        await self.stream_progress(node_id, 0.8, f"Message stored (total: {len(_memory_stores[session_id])} messages)")
        
        result = {
            "stored": True,
            "session_id": session_id,
            "message_id": memory_entry["id"],
            "total_messages": len(_memory_stores[session_id]),
        }
        
        await self.stream_progress(node_id, 1.0, "Memory operation completed")
        
        return result

    async def _retrieve_memory(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        session_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """Retrieve relevant messages from memory."""
        retrieval_type = config.get("retrieval_type", "recent")
        limit = config.get("limit", 10)
        query = inputs.get("query") or config.get("query")
        
        await self.stream_progress(node_id, 0.3, f"Retrieving memory (type: {retrieval_type})...")
        
        memory = _memory_stores.get(session_id, [])
        
        if retrieval_type == "recent":
            # Get most recent messages
            recent_messages = memory[-limit:] if limit > 0 else memory
            await self.stream_progress(node_id, 0.8, f"Retrieved {len(recent_messages)} recent messages")
            result = {
                "messages": recent_messages,
                "count": len(recent_messages),
                "session_id": session_id,
                "retrieval_type": "recent",
            }
        elif retrieval_type == "all":
            # Get all messages
            await self.stream_progress(node_id, 0.8, f"Retrieved {len(memory)} messages")
            result = {
                "messages": memory,
                "count": len(memory),
                "session_id": session_id,
                "retrieval_type": "all",
            }
        elif retrieval_type == "semantic":
            # Semantic search (simple keyword matching for now)
            # In production, this would use embeddings
            if not query:
                # Fallback to recent if no query
                recent_messages = memory[-limit:] if limit > 0 else memory
                await self.stream_progress(node_id, 0.8, f"Retrieved {len(recent_messages)} recent messages (no query)")
                result = {
                    "messages": recent_messages,
                    "count": len(recent_messages),
                    "session_id": session_id,
                    "retrieval_type": "recent",
                }
            else:
                await self.stream_progress(node_id, 0.5, f"Searching memory for: {query[:50]}...")
                # Simple keyword matching
                query_lower = query.lower()
                relevant_messages = [
                    msg for msg in memory
                    if query_lower in msg["content"].lower()
                ][-limit:] if limit > 0 else [
                    msg for msg in memory
                    if query_lower in msg["content"].lower()
                ]
                await self.stream_progress(node_id, 0.8, f"Found {len(relevant_messages)} relevant messages")
                result = {
                    "messages": relevant_messages,
                    "count": len(relevant_messages),
                    "session_id": session_id,
                    "retrieval_type": "semantic",
                    "query": query,
                }
        else:
            raise ValueError(f"Unknown retrieval type: {retrieval_type}")
        
        await self.stream_progress(node_id, 1.0, "Memory retrieval completed")
        
        return result

    async def _clear_memory(self, session_id: str, node_id: str) -> Dict[str, Any]:
        """Clear memory for a session."""
        await self.stream_progress(node_id, 0.3, f"Clearing memory for session: {session_id}...")
        
        count = len(_memory_stores.get(session_id, []))
        _memory_stores[session_id] = []
        
        logger.info(f"Cleared memory for session: {session_id} ({count} messages)")
        
        await self.stream_progress(node_id, 0.8, f"Cleared {count} messages")
        
        result = {
            "cleared": True,
            "session_id": session_id,
            "messages_cleared": count,
        }
        
        await self.stream_progress(node_id, 1.0, "Memory cleared")
        
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this node."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["store", "retrieve", "clear"],
                    "default": "retrieve",
                    "title": "Operation",
                    "description": "Memory operation to perform",
                },
                "session_id": {
                    "type": "string",
                    "default": "default",
                    "title": "Session ID",
                    "description": "Unique identifier for the conversation session",
                },
                "retrieval_type": {
                    "type": "string",
                    "enum": ["recent", "all", "semantic"],
                    "default": "recent",
                    "title": "Retrieval Type",
                    "description": "How to retrieve messages (only used for retrieve operation)",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                    "title": "Limit",
                    "description": "Maximum number of messages to retrieve",
                },
                "query": {
                    "type": "string",
                    "title": "Query",
                    "description": "Search query for semantic retrieval",
                },
                "message": {
                    "type": "string",
                    "title": "Message",
                    "description": "Message to store (only used for store operation)",
                },
                "role": {
                    "type": "string",
                    "enum": ["user", "assistant", "system"],
                    "default": "user",
                    "title": "Role",
                    "description": "Message role (only used for store operation)",
                },
            },
            "required": ["operation"],
        }


# Register the node
NodeRegistry.register(
    MemoryNode.node_type,
    MemoryNode,
    MemoryNode().get_metadata(),
)

