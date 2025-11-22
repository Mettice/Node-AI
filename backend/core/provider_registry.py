"""
Provider Registry System

Centralized provider management for extensible integrations.
Supports vector stores, LLMs, NLP tasks, and other services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from backend.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ProviderRegistry:
    """
    Centralized registry for all providers.
    
    Supports:
    - Vector stores (FAISS, Pinecone, Azure Cognitive Search, etc.)
    - LLM providers (OpenAI, Anthropic, Azure OpenAI, etc.)
    - NLP tasks (Summarization, NER, Classification, etc.)
    - Storage providers (S3, Azure Blob, etc.)
    """

    _instance: Optional["ProviderRegistry"] = None
    _vector_stores: Dict[str, Type] = {}
    _llm_providers: Dict[str, Type] = {}
    _nlp_tasks: Dict[str, Type] = {}
    _storage_providers: Dict[str, Type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_vector_store(cls, name: str, provider_class: Type) -> None:
        """Register a vector store provider."""
        cls._vector_stores[name.lower()] = provider_class
        logger.info(f"Registered vector store provider: {name}")

    @classmethod
    def register_llm(cls, name: str, provider_class: Type) -> None:
        """Register an LLM provider."""
        cls._llm_providers[name.lower()] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def register_nlp_task(cls, name: str, provider_class: Type) -> None:
        """Register an NLP task provider."""
        cls._nlp_tasks[name.lower()] = provider_class
        logger.info(f"Registered NLP task provider: {name}")

    @classmethod
    def register_storage(cls, name: str, provider_class: Type) -> None:
        """Register a storage provider."""
        cls._storage_providers[name.lower()] = provider_class
        logger.info(f"Registered storage provider: {name}")

    @classmethod
    def get_vector_store(cls, name: str) -> Optional[Type]:
        """Get a vector store provider class."""
        return cls._vector_stores.get(name.lower())

    @classmethod
    def get_llm(cls, name: str) -> Optional[Type]:
        """Get an LLM provider class."""
        return cls._llm_providers.get(name.lower())

    @classmethod
    def get_nlp_task(cls, name: str) -> Optional[Type]:
        """Get an NLP task provider class."""
        return cls._nlp_tasks.get(name.lower())

    @classmethod
    def get_storage(cls, name: str) -> Optional[Type]:
        """Get a storage provider class."""
        return cls._storage_providers.get(name.lower())

    @classmethod
    def list_vector_stores(cls) -> List[str]:
        """List all registered vector store providers."""
        return list(cls._vector_stores.keys())

    @classmethod
    def list_llms(cls) -> List[str]:
        """List all registered LLM providers."""
        return list(cls._llm_providers.keys())

    @classmethod
    def list_nlp_tasks(cls) -> List[str]:
        """List all registered NLP task providers."""
        return list(cls._nlp_tasks.keys())

    @classmethod
    def list_storage_providers(cls) -> List[str]:
        """List all registered storage providers."""
        return list(cls._storage_providers.keys())

    @classmethod
    def is_registered(cls, provider_type: str, name: str) -> bool:
        """Check if a provider is registered."""
        registries = {
            "vector_store": cls._vector_stores,
            "llm": cls._llm_providers,
            "nlp_task": cls._nlp_tasks,
            "storage": cls._storage_providers,
        }
        registry = registries.get(provider_type.lower())
        if not registry:
            return False
        return name.lower() in registry


# Base classes for providers
class VectorStoreProvider(ABC):
    """Base class for vector store providers."""

    @abstractmethod
    async def store(
        self, embeddings: List[List[float]], metadata: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store vectors with metadata."""
        pass

    @abstractmethod
    async def search(
        self, query_embedding: List[float], top_k: int, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete(self, ids: List[str], config: Dict[str, Any]) -> bool:
        """Delete vectors by IDs."""
        pass


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def generate(
        self, prompt: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate text from prompt."""
        pass


class NLPTaskProvider(ABC):
    """Base class for NLP task providers."""

    @abstractmethod
    async def process(
        self, text: str, task_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process text with the NLP task."""
        pass


class StorageProvider(ABC):
    """Base class for storage providers."""

    @abstractmethod
    async def upload(self, file_path: str, destination: str, config: Dict[str, Any]) -> str:
        """Upload a file."""
        pass

    @abstractmethod
    async def download(self, source: str, destination: str, config: Dict[str, Any]) -> str:
        """Download a file."""
        pass

    @abstractmethod
    async def delete(self, path: str, config: Dict[str, Any]) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    async def list(self, prefix: str, config: Dict[str, Any]) -> List[str]:
        """List files with prefix."""
        pass

