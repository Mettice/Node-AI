"""
Node implementations for NodeAI backend.

This package contains all node implementations organized by category:
- input: Input nodes (text, file upload, etc.)
- processing: Processing nodes (chunk, filter, etc.)
- embedding: Embedding nodes (OpenAI, HuggingFace, etc.)
- storage: Storage nodes (FAISS, Pinecone, etc.)
- retrieval: Retrieval nodes (vector search, etc.)
- llm: LLM nodes (OpenAI chat, Claude, etc.)

All nodes are automatically imported and registered when this package is loaded.
"""

# Import all nodes to trigger their registration
# This ensures all nodes are available in the NodeRegistry

# Input nodes
from backend.nodes.input.text_input import TextInputNode  # noqa: F401
from backend.nodes.input.file_loader import FileLoaderNode  # noqa: F401
try:
    from backend.nodes.input.webhook_input import WebhookInputNode  # noqa: F401
except ImportError as e:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"WebhookInput node import warning: {e}")
except Exception as e:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing WebhookInput node: {e}", exc_info=True)
try:
    from backend.nodes.input.data_loader import DataLoaderNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"DataLoader node import warning (may need pandas/openpyxl/pyarrow): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing DataLoader node: {e}", exc_info=True)

# Processing nodes
from backend.nodes.processing.chunk import ChunkNode  # noqa: F401
try:
    from backend.nodes.processing.ocr import OCRNode  # noqa: F401
except ImportError:
    # pytesseract/PIL not available - node will be skipped
    pass
try:
    from backend.nodes.processing.transcribe import TranscribeNode  # noqa: F401
except ImportError:
    # openai-whisper not available - node will be skipped
    pass
try:
    from backend.nodes.processing.video_frames import VideoFramesNode  # noqa: F401
except ImportError:
    # opencv-python not available - node will be skipped
    pass
try:
    from backend.nodes.processing.data_to_text import DataToTextNode  # noqa: F401
except ImportError:
    # No dependencies - should always work
    pass
try:
    from backend.nodes.processing.advanced_nlp import AdvancedNLPNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Advanced NLP node import warning (may need transformers/openai/anthropic): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Advanced NLP node: {e}", exc_info=True)

# Embedding nodes
from backend.nodes.embedding.embed import EmbedNode  # noqa: F401

# Storage nodes
from backend.nodes.storage.vector_store import VectorStoreNode  # noqa: F401
try:
    from backend.nodes.storage.knowledge_graph import KnowledgeGraphNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Knowledge Graph node import warning (may need neo4j): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Knowledge Graph node import error (will skip): {e}")
try:
    from backend.nodes.storage.s3 import S3Node  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"S3 node import warning (may need boto3): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing S3 node: {e}", exc_info=True)
try:
    from backend.nodes.storage.azure_blob import AzureBlobNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Azure Blob Storage node import warning (may need azure-storage-blob): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    # This includes NameError for type hints when package is not installed
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Azure Blob Storage node import error (will skip): {e}")
    # Don't raise - continue with other nodes

try:
    from backend.nodes.storage.database import DatabaseNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Database node import warning: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Database node: {e}", exc_info=True)

# Retrieval nodes
from backend.nodes.retrieval.search import VectorSearchNode  # noqa: F401
from backend.nodes.retrieval.hybrid_retrieval import HybridRetrievalNode  # noqa: F401
try:
    from backend.nodes.retrieval.rerank import RerankNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Rerank node import warning (may need cohere/sentence-transformers): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Rerank node: {e}", exc_info=True)

# LLM nodes
from backend.nodes.llm.chat import ChatNode  # noqa: F401
try:
    from backend.nodes.llm.vision import VisionNode  # noqa: F401
except ImportError:
    # OpenAI not available - node will be skipped
    pass

# Memory nodes
from backend.nodes.memory.memory import MemoryNode  # noqa: F401

# Communication nodes
try:
    from backend.nodes.communication.email import EmailNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Email node import warning: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Email node: {e}", exc_info=True)

try:
    from backend.nodes.communication.slack import SlackNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Slack node import warning: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Slack node: {e}", exc_info=True)

try:
    from backend.nodes.storage.google_drive import GoogleDriveNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Google Drive node import warning: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Google Drive node: {e}", exc_info=True)

# Integration nodes
try:
    from backend.nodes.integration.reddit import RedditNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"Reddit node import warning: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing Reddit node: {e}", exc_info=True)

# Agent nodes
try:
    from backend.nodes.agent.langchain_agent import LangChainAgentNode  # noqa: F401
except ImportError:
    # LangChain not available - node will be skipped
    pass

try:
    # Import the module to trigger registration (registration happens at module level)
    from backend.nodes.agent import crewai_agent  # noqa: F401
    from backend.nodes.agent.crewai_agent import CrewAINode  # noqa: F401
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("CrewAI agent node module imported successfully")
except ImportError as e:
    # CrewAI not installed - this is expected if package not installed
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"CrewAI not available: {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing CrewAI agent node: {e}", exc_info=True)

# Tool nodes
from backend.nodes.tools.tool_node import ToolNode  # noqa: F401

# Training nodes
try:
    from backend.nodes.training.finetune import FineTuneNode  # noqa: F401
except ImportError as e:
    # Log but don't fail - node will be available but may fail at runtime if dependencies missing
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning(f"FineTune node import warning (may need openai): {e}")
except Exception as e:
    # Other errors during import - log but don't fail
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"Error importing FineTune node: {e}", exc_info=True)

# Export the registry for easy access
from backend.core.node_registry import NodeRegistry, get_node_class, register_node

__all__ = [
    "NodeRegistry",
    "get_node_class",
    "register_node",
]
