"""
Generic Chunk Node for NodeAI.

This node supports multiple text splitting strategies:
- Recursive (LangChain's RecursiveCharacterTextSplitter)
- Fixed Size (simple character-based splitting)
- Semantic (sentence-based splitting)
- (More strategies can be added later)
"""

from typing import Any, Dict, List

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ChunkNode(BaseNode):
    """
    Generic Chunk Node.
    
    Supports multiple text splitting strategies with a dropdown selector.
    Each strategy has its own configuration options.
    """

    node_type = "chunk"
    name = "Chunk"
    description = "Split text into chunks using various strategies (Recursive, Fixed Size, Semantic, etc.)"
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the chunk node.
        
        Supports multiple strategies based on config selection.
        """
        node_id = config.get("_node_id", "chunk")
        
        # OPTIMIZATION: Skip if vector store already exists (for deployed workflows)
        if config.get("_skip_if_store_exists"):
            await self.stream_log(node_id, "Skipping chunking (vector store already exists)")
            return {
                "chunks": [],
                "count": 0,
            }
        
        strategy = config.get("strategy", "recursive")
        text = inputs.get("text", "")
        
        if not text:
            raise ValueError("No text provided in inputs")
        
        await self.stream_progress(node_id, 0.1, f"Starting {strategy} chunking...")
        await self.stream_log(node_id, f"Text length: {len(text)} characters")
        
        # Route to appropriate strategy
        if strategy == "recursive":
            result = await self._chunk_recursive(text, config, node_id)
        elif strategy == "fixed_size":
            result = await self._chunk_fixed_size(text, config, node_id)
        elif strategy == "semantic":
            result = await self._chunk_semantic(text, config, node_id)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")
        
        await self.stream_progress(node_id, 1.0, f"Created {result['count']} chunks")
        
        return result

    async def _chunk_recursive(
        self,
        text: str,
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Chunk text using LangChain's RecursiveCharacterTextSplitter."""
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        except ImportError:
            raise ValueError(
                "langchain not installed. Install it with: pip install langchain"
            )
        
        # Get configuration
        chunk_size = config.get("chunk_size", 512)
        chunk_overlap = config.get("chunk_overlap", 50)
        separators = config.get("separators", [])  # Optional custom separators
        
        await self.stream_progress(node_id, 0.3, f"Configuring splitter (size: {chunk_size}, overlap: {chunk_overlap})")
        
        # Create splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators if separators else None,
            length_function=len,
        )
        
        await self.stream_progress(node_id, 0.5, "Splitting text...")
        
        # Split text
        chunks = splitter.split_text(text)
        
        # Calculate statistics
        avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
        
        return {
            "chunks": chunks,
            "strategy": "recursive",
            "count": len(chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "avg_chunk_size": int(avg_chunk_size),
            "metadata": {
                "total_chars": len(text),
                "total_chunks": len(chunks),
            },
        }

    async def _chunk_fixed_size(
        self,
        text: str,
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Chunk text using fixed-size splitting."""
        chunk_size = config.get("chunk_size", 512)
        chunk_overlap = config.get("chunk_overlap", 50)
        
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        await self.stream_progress(node_id, 0.3, f"Splitting into {chunk_size}-char chunks...")
        
        chunks = []
        start = 0
        text_length = len(text)
        estimated_chunks = (text_length // chunk_size) + 1
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Stream progress
            if len(chunks) % 10 == 0 or start + chunk_size >= text_length:
                progress = 0.3 + (start / text_length) * 0.6
                await self.stream_progress(node_id, progress, f"Created {len(chunks)} chunks...")
            
            # Move start position with overlap
            start = end - chunk_overlap
        
        # Calculate statistics
        avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
        
        return {
            "chunks": chunks,
            "strategy": "fixed_size",
            "count": len(chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "avg_chunk_size": int(avg_chunk_size),
            "metadata": {
                "total_chars": len(text),
                "total_chunks": len(chunks),
            },
        }

    async def _chunk_semantic(
        self,
        text: str,
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Chunk text using semantic/sentence-based splitting."""
        try:
            import nltk
            from nltk.tokenize import sent_tokenize
            
            # Download punkt if not available
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                await self.stream_progress(node_id, 0.2, "Downloading NLTK data...")
                nltk.download("punkt", quiet=True)
        except ImportError:
            raise ValueError(
                "nltk not installed. Install it with: pip install nltk"
            )
        
        # Get configuration
        min_chunk_size = config.get("min_chunk_size", 100)
        max_chunk_size = config.get("max_chunk_size", 512)
        overlap_sentences = config.get("overlap_sentences", 1)
        
        await self.stream_progress(node_id, 0.3, "Tokenizing sentences...")
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        await self.stream_progress(node_id, 0.4, f"Found {len(sentences)} sentences, grouping into chunks...")
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            if i % 50 == 0:
                progress = 0.4 + (i / len(sentences)) * 0.5
                await self.stream_progress(node_id, progress, f"Processing sentence {i+1}/{len(sentences)}...")
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed max size, save current chunk
            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= min_chunk_size:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                if overlap_sentences > 0:
                    current_chunk = current_chunk[-overlap_sentences:]
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= min_chunk_size:
                chunks.append(chunk_text)
        
        # Calculate statistics
        avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
        
        return {
            "chunks": chunks,
            "strategy": "semantic",
            "count": len(chunks),
            "min_chunk_size": min_chunk_size,
            "max_chunk_size": max_chunk_size,
            "overlap_sentences": overlap_sentences,
            "avg_chunk_size": int(avg_chunk_size),
            "metadata": {
                "total_chars": len(text),
                "total_chunks": len(chunks),
                "total_sentences": len(sentences),
            },
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema with strategy selection and dynamic config."""
        return {
            "type": "object",
            "properties": {
                "strategy": {
                    "type": "string",
                    "title": "Chunking Strategy",
                    "description": "Select the text splitting strategy",
                    "enum": ["recursive", "fixed_size", "semantic"],
                    "default": "recursive",
                },
                # Common config (used by recursive and fixed_size)
                "chunk_size": {
                    "type": "integer",
                    "title": "Chunk Size",
                    "description": "Number of characters per chunk",
                    "default": 512,
                    "minimum": 1,
                    "maximum": 10000,
                },
                "chunk_overlap": {
                    "type": "integer",
                    "title": "Chunk Overlap",
                    "description": "Number of overlapping characters between chunks",
                    "default": 50,
                    "minimum": 0,
                    "maximum": 1000,
                },
                # Recursive-specific config
                "separators": {
                    "type": "array",
                    "title": "Custom Separators (Optional)",
                    "description": "Custom separators for recursive splitting",
                    "items": {"type": "string"},
                    "default": [],
                },
                # Semantic-specific config
                "min_chunk_size": {
                    "type": "integer",
                    "title": "Min Chunk Size",
                    "description": "Minimum characters per chunk (semantic only)",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 5000,
                },
                "max_chunk_size": {
                    "type": "integer",
                    "title": "Max Chunk Size",
                    "description": "Maximum characters per chunk (semantic only)",
                    "default": 512,
                    "minimum": 1,
                    "maximum": 10000,
                },
                "overlap_sentences": {
                    "type": "integer",
                    "title": "Overlap Sentences",
                    "description": "Number of sentences to overlap (semantic only)",
                    "default": 1,
                    "minimum": 0,
                    "maximum": 10,
                },
            },
            "required": ["strategy"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "chunks": {
                "type": "array",
                "description": "List of text chunks",
                "items": {"type": "string"},
            },
            "strategy": {
                "type": "string",
                "description": "Strategy used",
            },
            "count": {
                "type": "integer",
                "description": "Number of chunks created",
            },
            "metadata": {
                "type": "object",
                "description": "Chunking metadata and statistics",
            },
        }


# Register the node
NodeRegistry.register(
    "chunk",
    ChunkNode,
    ChunkNode().get_metadata(),
)

