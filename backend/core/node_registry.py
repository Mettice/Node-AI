"""
Node registry for NodeAI backend.

This module manages all available node types in the system.
It provides a registry pattern for discovering and accessing node implementations.
"""

from typing import Dict, List, Optional, Type

from backend.core.exceptions import NodeNotFoundError
from backend.core.models import NodeMetadata
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NodeRegistry:
    """
    Registry for all available node types.
    
    This class maintains a mapping of node type identifiers to their
    implementation classes. Nodes can be registered and retrieved by type.
    """

    _nodes: Dict[str, Type] = {}
    _metadata: Dict[str, NodeMetadata] = {}

    @classmethod
    def register(
        cls,
        node_type: str,
        node_class: Type,
        metadata: Optional[NodeMetadata] = None,
    ) -> None:
        """
        Register a node type in the registry.
        
        Args:
            node_type: Unique identifier for the node type (e.g., 'text_input')
            node_class: The node class that implements BaseNode
            metadata: Optional metadata about the node type
            
        Example:
            ```python
            NodeRegistry.register("text_input", TextInputNode, metadata)
            ```
        """
        if node_type in cls._nodes:
            logger.warning(f"Node type '{node_type}' is already registered. Overwriting...")

        cls._nodes[node_type] = node_class

        if metadata:
            cls._metadata[node_type] = metadata
            logger.debug(f"Registered node type '{node_type}' with metadata")
        else:
            logger.debug(f"Registered node type '{node_type}' without metadata")

    @classmethod
    def get(cls, node_type: str) -> Type:
        """
        Get a node class by type identifier.
        
        Args:
            node_type: The node type identifier
            
        Returns:
            The node class
            
        Raises:
            NodeNotFoundError: If the node type is not registered
            
        Example:
            ```python
            node_class = NodeRegistry.get("text_input")
            node = node_class()
            ```
        """
        if node_type not in cls._nodes:
            available = ", ".join(cls._nodes.keys())
            raise NodeNotFoundError(
                f"Node type '{node_type}' not found. Available types: {available}"
            )

        return cls._nodes[node_type]

    @classmethod
    def get_metadata(cls, node_type: str) -> Optional[NodeMetadata]:
        """
        Get metadata for a node type.
        
        Args:
            node_type: The node type identifier
            
        Returns:
            NodeMetadata if available, None otherwise
        """
        return cls._metadata.get(node_type)

    @classmethod
    def list_all(cls) -> List[str]:
        """
        List all registered node types.
        
        Returns:
            List of node type identifiers
        """
        return list(cls._nodes.keys())

    @classmethod
    def list_all_metadata(cls) -> List[NodeMetadata]:
        """
        List metadata for all registered nodes.
        
        Returns:
            List of NodeMetadata objects
        """
        result = []
        for node_type in cls._nodes.keys():
            # Get metadata if available, otherwise generate it
            metadata = cls._metadata.get(node_type)
            if not metadata:
                try:
                    node_class = cls._nodes[node_type]
                    node_instance = node_class()
                    metadata = node_instance.get_metadata()
                    # Cache it for next time
                    cls._metadata[node_type] = metadata
                except Exception as e:
                    logger.warning(f"Failed to generate metadata for node '{node_type}': {e}")
                    continue
            
            if metadata:
                result.append(metadata)
        
        return result

    @classmethod
    def is_registered(cls, node_type: str) -> bool:
        """
        Check if a node type is registered.
        
        Args:
            node_type: The node type identifier
            
        Returns:
            True if registered, False otherwise
        """
        return node_type in cls._nodes

    @classmethod
    def get_count(cls) -> int:
        """
        Get the total number of registered nodes.
        
        Returns:
            Number of registered node types
        """
        return len(cls._nodes)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered nodes.
        
        This is mainly useful for testing.
        """
        cls._nodes.clear()
        cls._metadata.clear()
        logger.debug("Node registry cleared")

    @classmethod
    def get_by_category(cls, category: str) -> List[str]:
        """
        Get all node types in a specific category.
        
        Args:
            category: Category name (e.g., 'input', 'processing', 'llm')
            
        Returns:
            List of node type identifiers in that category
        """
        result = []
        for node_type, metadata in cls._metadata.items():
            if metadata.category == category:
                result.append(node_type)
        return result

    @classmethod
    def get_categories(cls) -> List[str]:
        """
        Get all available node categories.
        
        Returns:
            List of unique category names
        """
        categories = set()
        for metadata in cls._metadata.values():
            categories.add(metadata.category)
        return sorted(list(categories))


# Convenience function for easy access
def get_node_class(node_type: str) -> Type:
    """
    Get a node class by type identifier.
    
    This is a convenience function that wraps NodeRegistry.get().
    
    Args:
        node_type: The node type identifier
        
    Returns:
        The node class
    """
    return NodeRegistry.get(node_type)


def register_node(node_type: str, metadata: Optional[NodeMetadata] = None):
    """
    Decorator to register a node class.
    
    This decorator can be used to automatically register a node class
    when it's defined.
    
    Args:
        node_type: The node type identifier
        metadata: Optional metadata about the node
        
    Example:
        ```python
        @register_node("text_input", metadata)
        class TextInputNode(BaseNode):
            ...
        ```
    """

    def decorator(node_class: Type):
        NodeRegistry.register(node_type, node_class, metadata)
        return node_class

    return decorator

