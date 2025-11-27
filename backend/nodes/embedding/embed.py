"""
Generic Embedding Node for NodeAI.

This node supports multiple embedding providers:
- OpenAI
- HuggingFace
- Cohere
- (More can be added later)
"""

from typing import Any, Dict, List

from openai import OpenAI

from backend.config import settings
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger
from backend.utils.model_pricing import (
    calculate_embedding_cost_from_texts,
    get_model_pricing,
    ModelType,
)

logger = get_logger(__name__)


class EmbedNode(BaseNode):
    """
    Generic Embedding Node.
    
    Supports multiple embedding providers with a dropdown selector.
    Each provider has its own configuration options.
    """

    node_type = "embed"
    name = "Embed"
    description = "Create embeddings from text using various providers (OpenAI, HuggingFace, Cohere, etc.)"
    category = "embedding"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the embedding node.
        
        Supports multiple providers based on config selection.
        """
        node_id = config.get("_node_id", "embed")
        
        # OPTIMIZATION: Skip if vector store already exists (for deployed workflows)
        if config.get("_skip_if_store_exists"):
            await self.stream_log(node_id, "Skipping embedding (vector store already exists)")
            return {
                "embeddings": [],
                "count": 0,
                "model": config.get("provider", "openai"),
                "dimension": 0,
            }
        
        provider = config.get("provider", "openai")
        text_input = inputs.get("text") or inputs.get("chunks")
        
        if not text_input:
            raise ValueError("No text or chunks provided in inputs")
        
        # Convert single text to list for consistent processing
        if isinstance(text_input, str):
            texts = [text_input]
        elif isinstance(text_input, list):
            texts = text_input
        else:
            raise ValueError(f"Invalid input type: {type(text_input)}")
        
        await self.stream_progress(node_id, 0.1, f"Preparing to embed {len(texts)} text(s) using {provider}...")
        
        # Route to appropriate provider
        if provider == "openai":
            return await self._embed_openai(texts, inputs, config, node_id)
        elif provider == "azure_openai" or provider == "azure":
            return await self._embed_azure_openai(texts, inputs, config, node_id)
        elif provider == "huggingface":
            return await self._embed_huggingface(texts, inputs, config, node_id)
        elif provider == "cohere":
            return await self._embed_cohere(texts, inputs, config, node_id)
        elif provider == "voyage_ai" or provider == "voyageai":
            return await self._embed_voyage_ai(texts, inputs, config, node_id)
        elif provider == "gemini" or provider == "google":
            return await self._embed_gemini(texts, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    async def _embed_openai(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using OpenAI."""
        # Check if using fine-tuned model
        use_finetuned = config.get("use_finetuned_model", False)
        finetuned_model_id = config.get("finetuned_model_id")
        
        if use_finetuned and finetuned_model_id:
            # Get fine-tuned model from registry
            model_data = await self._get_finetuned_model(finetuned_model_id, "openai")
            if not model_data:
                raise ValueError(f"Fine-tuned model not found: {finetuned_model_id}")
            # Use the provider model ID
            model = model_data["model_id"]
            # Track usage
            await self._record_model_usage(finetuned_model_id, "embed", config.get("_execution_id"))
        else:
            model = config.get("openai_model", "text-embedding-3-small")
        batch_size = config.get("batch_size", 100)
        
        # Resolve API key from vault, config, or settings
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id)
        if not api_key:
            raise ValueError("OpenAI API key not found. Please configure it in the node settings or environment variables.")
        client = OpenAI(api_key=api_key)
        
        # Process in batches
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        use_batch_pricing = total_batches > 1  # Use batch pricing if multiple batches
        
        for batch_num, i in enumerate(range(0, len(texts), batch_size)):
            batch = texts[i : i + batch_size]
            progress = 0.2 + (batch_num / total_batches) * 0.7
            
            await self.stream_progress(
                node_id, 
                progress, 
                f"Embedding batch {batch_num + 1}/{total_batches} ({len(batch)} texts)..."
            )
            
            try:
                response = client.embeddings.create(
                    model=model,
                    input=batch,
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                raise
        
        # Calculate cost using centralized pricing
        cost = calculate_embedding_cost_from_texts("openai", model, texts, use_batch_pricing)
        
        # Preserve chunks if they were in inputs (for downstream nodes)
        result = {
            "embeddings": all_embeddings,
            "provider": "openai",
            "model": model,
            "count": len(all_embeddings),
            "dimension": len(all_embeddings[0]) if all_embeddings else 0,
            "cost": cost,
        }
        
        # Add fine-tuned model info if used
        if use_finetuned and finetuned_model_id:
            result["finetuned_model_id"] = finetuned_model_id
            result["is_finetuned"] = True
        
        # Pass through chunks if available (for vector store)
        if "chunks" in inputs:
            result["chunks"] = inputs["chunks"]
        
        await self.stream_progress(node_id, 1.0, f"Created {len(all_embeddings)} embeddings (cost: ${cost:.6f})")
        
        return result

    async def _embed_huggingface(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using HuggingFace."""
        model_name = config.get("hf_model", "sentence-transformers/all-MiniLM-L6-v2")
        endpoint = config.get("hf_endpoint")  # Optional custom endpoint
        
        await self.stream_progress(node_id, 0.2, f"Loading HuggingFace model: {model_name}...")
        
        # For now, we'll use sentence-transformers library
        # In production, you might want to use HuggingFace Inference API
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer(model_name)
            await self.stream_progress(node_id, 0.4, f"Encoding {len(texts)} texts...")
            embeddings = model.encode(texts, show_progress_bar=False)
            
            result = {
                "embeddings": embeddings.tolist(),
                "provider": "huggingface",
                "model": model_name,
                "count": len(embeddings),
                "dimension": embeddings.shape[1] if len(embeddings) > 0 else 0,
            }
            
            # Pass through chunks if available
            if "chunks" in inputs:
                result["chunks"] = inputs["chunks"]
            
            await self.stream_progress(node_id, 1.0, f"Created {len(embeddings)} embeddings")
            
            return result
        except ImportError:
            raise ValueError(
                "sentence-transformers not installed. "
                "Install it with: pip install sentence-transformers"
            )

    async def _embed_azure_openai(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using Azure OpenAI Service."""
        # Resolve Azure OpenAI API key from vault, config, or settings
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "azure_openai_api_key", user_id=user_id) or config.get("azure_api_key")
        endpoint = config.get("azure_openai_endpoint") or config.get("azure_endpoint")
        api_version = config.get("azure_openai_api_version", "2024-02-15-preview")
        deployment_name = config.get("azure_openai_deployment") or config.get("azure_deployment")
        
        if not api_key or not endpoint or not deployment_name:
            raise ValueError(
                "Azure OpenAI requires: api_key, endpoint, and deployment_name. "
                "Set azure_openai_api_key, azure_openai_endpoint, and azure_openai_deployment in config."
            )
        
        # Check if using fine-tuned model
        use_finetuned = config.get("use_finetuned_model", False)
        finetuned_model_id = config.get("finetuned_model_id")
        
        if use_finetuned and finetuned_model_id:
            # Get fine-tuned model from registry
            model_data = await self._get_finetuned_model(finetuned_model_id, "azure_openai")
            if not model_data:
                raise ValueError(f"Fine-tuned model not found: {finetuned_model_id}")
            model = model_data["model_id"]
            await self._record_model_usage(finetuned_model_id, "embed", config.get("_execution_id"))
        else:
            model = config.get("azure_openai_model") or deployment_name
        
        batch_size = config.get("batch_size", 100)
        
        # Create Azure OpenAI client
        # Azure OpenAI uses the same OpenAI SDK but with different base URL
        # The base_url should be the endpoint, and deployment name is used as the model parameter
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/deployments",
            default_headers={"api-key": api_key},
            default_query={"api-version": api_version},
        )
        
        # Process in batches
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        use_batch_pricing = total_batches > 1
        
        for batch_num, i in enumerate(range(0, len(texts), batch_size)):
            batch = texts[i : i + batch_size]
            progress = 0.2 + (batch_num / total_batches) * 0.7
            
            await self.stream_progress(
                node_id, 
                progress, 
                f"Embedding batch {batch_num + 1}/{total_batches} ({len(batch)} texts) with Azure OpenAI..."
            )
            
            try:
                response = client.embeddings.create(
                    model=deployment_name,  # Azure OpenAI uses deployment name
                    input=batch,
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Azure OpenAI embedding error: {e}")
                raise
        
        # Get model info for dimension
        dimension = len(all_embeddings[0]) if all_embeddings else 0
        
        # Calculate cost
        total_tokens = sum(len(text.split()) * 1.3 for text in texts)  # Rough token estimation
        cost = calculate_embedding_cost_from_texts("openai", model, texts, use_batch_pricing)
        
        result = {
            "embeddings": all_embeddings,
            "provider": "azure_openai",
            "model": model,
            "deployment": deployment_name,
            "count": len(all_embeddings),
            "dimension": dimension,
            "cost": cost,
        }
        
        # Pass through chunks if they were in inputs
        if "chunks" in inputs:
            result["chunks"] = inputs["chunks"]
        
        await self.stream_progress(node_id, 1.0, f"Created {len(all_embeddings)} embeddings with Azure OpenAI")
        
        return result

    async def _embed_cohere(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using Cohere."""
        model = config.get("cohere_model", "embed-english-v3.0")
        input_type = config.get("cohere_input_type", "search_document")
        
        await self.stream_progress(node_id, 0.2, f"Creating embeddings with Cohere ({model})...")
        
        try:
            import cohere
            
            # Resolve API key from vault, config, or settings
            user_id = config.get("_user_id")
            api_key = resolve_api_key(config, "cohere_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("Cohere API key not configured")
            
            client = cohere.Client(api_key=api_key)
            await self.stream_progress(node_id, 0.5, f"Sending {len(texts)} texts to Cohere...")
            response = client.embed(
                texts=texts,
                model=model,
                input_type=input_type,
            )
            
            # Get model info for dimension
            model_info = get_model_pricing("cohere", model)
            dimension = model_info.dimension if model_info else (len(response.embeddings[0]) if response.embeddings else 0)
            
            result = {
                "embeddings": response.embeddings,
                "provider": "cohere",
                "model": model,
                "count": len(response.embeddings),
                "dimension": dimension,
            }
            
            # Pass through chunks if available
            if "chunks" in inputs:
                result["chunks"] = inputs["chunks"]
            
            await self.stream_progress(node_id, 1.0, f"Created {len(response.embeddings)} embeddings")
            
            return result
        except ImportError:
            raise ValueError(
                "cohere not installed. Install it with: pip install cohere"
            )

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema with provider selection and dynamic config."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Embedding Provider",
                    "description": "Select the embedding provider",
                    "enum": ["openai", "azure_openai", "huggingface", "cohere", "voyage_ai", "gemini"],
                    "default": "openai",
                },
                # Fine-tuned model support
                "use_finetuned_model": {
                    "type": "boolean",
                    "title": "Use Fine-Tuned Model",
                    "description": "Use a custom fine-tuned model from the registry",
                    "default": False,
                },
                "finetuned_model_id": {
                    "type": "string",
                    "title": "Fine-Tuned Model",
                    "description": "Select a fine-tuned model (only for OpenAI provider)",
                    "default": "",
                },
                # OpenAI config
                "openai_model": {
                    "type": "string",
                    "title": "OpenAI Model",
                    "description": "OpenAI embedding model (ignored if fine-tuned model is selected)",
                    "enum": [
                        "text-embedding-3-small",
                        "text-embedding-3-large",
                        "text-embedding-ada-002",
                    ],
                    "default": "text-embedding-3-small",
                },
                "batch_size": {
                    "type": "integer",
                    "title": "Batch Size",
                    "description": "Number of texts to process in each batch",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                },
                # HuggingFace config
                "hf_model": {
                    "type": "string",
                    "title": "HuggingFace Model",
                    "description": "HuggingFace model name",
                    "default": "sentence-transformers/all-MiniLM-L6-v2",
                },
                "hf_endpoint": {
                    "type": "string",
                    "title": "Custom Endpoint (Optional)",
                    "description": "Custom HuggingFace endpoint URL",
                    "default": "",
                },
                # Cohere config
                "cohere_model": {
                    "type": "string",
                    "title": "Cohere Model",
                    "description": "Cohere embedding model",
                    "enum": [
                        "embed-v4.0",
                        "embed-english-v3.0",
                        "embed-english-light-v3.0",
                        "embed-multilingual-v3.0",
                        "embed-multilingual-light-v3.0",
                    ],
                    "default": "embed-english-v3.0",
                },
                "cohere_input_type": {
                    "type": "string",
                    "title": "Input Type",
                    "description": "Type of input for Cohere",
                    "enum": ["search_document", "search_query"],
                    "default": "search_document",
                },
                # Voyage AI config
                "voyage_model": {
                    "type": "string",
                    "title": "Voyage AI Model",
                    "description": "Voyage AI embedding model",
                    "enum": [
                        "voyage-3-large",
                        "voyage-context-3",
                        "voyage-code-3",
                        "voyage-3.5",
                        "voyage-3.5-lite",
                        "voyage-multimodal-3",
                        "voyage-2",
                        "voyage-1",
                    ],
                    "default": "voyage-3.5",
                },
                "voyage_input_type": {
                    "type": "string",
                    "title": "Input Type",
                    "description": "Type of input for Voyage AI",
                    "enum": ["document", "query"],
                    "default": "document",
                },
                # Gemini config
                "gemini_model": {
                    "type": "string",
                    "title": "Gemini Model",
                    "description": "Gemini embedding model",
                    "enum": ["gemini-embedding-001"],
                    "default": "gemini-embedding-001",
                },
                "gemini_task_type": {
                    "type": "string",
                    "title": "Task Type",
                    "description": "Task type to optimize embeddings for",
                    "enum": [
                        "SEMANTIC_SIMILARITY",
                        "CLASSIFICATION",
                        "CLUSTERING",
                        "RETRIEVAL_DOCUMENT",
                        "RETRIEVAL_QUERY",
                        "CODE_RETRIEVAL_QUERY",
                        "QUESTION_ANSWERING",
                        "FACT_VERIFICATION",
                    ],
                    "default": "RETRIEVAL_DOCUMENT",
                },
                "gemini_output_dimensionality": {
                    "type": "integer",
                    "title": "Output Dimensionality",
                    "description": "Output embedding dimension (128-3072, recommended: 768, 1536, 3072)",
                    "default": 768,
                    "minimum": 128,
                    "maximum": 3072,
                },
                # API Keys (optional - will use environment variables if not provided)
                "openai_api_key": {
                    "type": "string",
                    "title": "OpenAI API Key",
                    "description": "Optional: OpenAI API key (uses OPENAI_API_KEY env var if not provided)",
                    "default": "",
                },
                "cohere_api_key": {
                    "type": "string",
                    "title": "Cohere API Key",
                    "description": "Optional: Cohere API key (uses COHERE_API_KEY env var if not provided)",
                    "default": "",
                },
                "voyage_api_key": {
                    "type": "string",
                    "title": "Voyage AI API Key",
                    "description": "Optional: Voyage AI API key (uses VOYAGE_API_KEY env var if not provided)",
                    "default": "",
                },
                "gemini_api_key": {
                    "type": "string",
                    "title": "Gemini API Key",
                    "description": "Optional: Google Gemini API key (uses GEMINI_API_KEY env var if not provided)",
                    "default": "",
                },
                # Azure OpenAI config (for embeddings)
                "azure_openai_api_key": {
                    "type": "string",
                    "title": "Azure OpenAI API Key",
                    "description": "Azure OpenAI API key (required for Azure OpenAI provider)",
                    "default": "",
                },
                "azure_openai_endpoint": {
                    "type": "string",
                    "title": "Azure OpenAI Endpoint",
                    "description": "Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com)",
                    "default": "",
                },
                "azure_openai_deployment": {
                    "type": "string",
                    "title": "Deployment Name",
                    "description": "Azure OpenAI deployment name for embeddings (e.g., text-embedding-ada-002)",
                    "default": "",
                },
                "azure_openai_api_version": {
                    "type": "string",
                    "title": "API Version",
                    "description": "Azure OpenAI API version",
                    "default": "2024-02-15-preview",
                },
                "azure_openai_model": {
                    "type": "string",
                    "title": "Model Name (Optional)",
                    "description": "Model name for cost calculation (defaults to deployment name)",
                    "default": "",
                },
            },
            "required": ["provider"],
        }

    async def _embed_voyage_ai(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using Voyage AI."""
        model = config.get("voyage_model", "voyage-3.5")
        input_type = config.get("voyage_input_type", "document")  # "document" or "query"
        batch_size = config.get("batch_size", 128)  # Voyage AI supports up to 128
        
        await self.stream_progress(node_id, 0.2, f"Creating embeddings with Voyage AI ({model})...")
        
        try:
            import voyageai
        except ImportError:
            raise ImportError(
                "Voyage AI requires the voyageai package. Install with: pip install voyageai"
            )
        
        # Resolve API key from vault, config, or settings
        import os
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "voyage_api_key", user_id=user_id) or os.getenv("VOYAGE_API_KEY") or getattr(settings, "voyage_api_key", None)
        if not api_key:
            raise ValueError(
                "Voyage AI API key not configured. "
                "Get your API key from https://www.voyageai.com/"
            )
        
        client = voyageai.Client(api_key=api_key)
        
        # Process in batches
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for batch_num, i in enumerate(range(0, len(texts), batch_size)):
            batch = texts[i : i + batch_size]
            progress = 0.3 + (batch_num / total_batches) * 0.6
            
            await self.stream_progress(
                node_id,
                progress,
                f"Embedding batch {batch_num + 1}/{total_batches} ({len(batch)} texts)..."
            )
            
            try:
                response = client.embed(
                    texts=batch,
                    model=model,
                    input_type=input_type,
                )
                
                all_embeddings.extend(response.embeddings)
                
            except Exception as e:
                logger.error(f"Voyage AI embedding error: {e}")
                raise
        
        # Get model info for dimension
        model_info = get_model_pricing("voyage_ai", model)
        dimension = model_info.dimension if model_info else 1024  # Default to 1024
        
        result = {
            "embeddings": all_embeddings,
            "provider": "voyage_ai",
            "model": model,
            "count": len(all_embeddings),
            "dimension": dimension,
        }
        
        # Pass through chunks if available
        if "chunks" in inputs:
            result["chunks"] = inputs["chunks"]
        
        await self.stream_progress(node_id, 1.0, f"Created {len(all_embeddings)} embeddings")
        
        return result
    
    async def _embed_gemini(
        self,
        texts: List[str],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create embeddings using Google Gemini."""
        model = config.get("gemini_model", "gemini-embedding-001")
        task_type = config.get("gemini_task_type", "RETRIEVAL_DOCUMENT")
        output_dimensionality = config.get("gemini_output_dimensionality", 768)
        batch_size = config.get("batch_size", 100)
        
        await self.stream_progress(node_id, 0.2, f"Creating embeddings with Gemini ({model})...")
        
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ValueError(
                "Gemini requires the google-genai package. Install with: pip install google-genai"
            )
        
        import os
        # Resolve API key from vault, config, or settings
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "gemini_api_key", user_id=user_id) or os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
        if not api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Get your API key from https://aistudio.google.com/app/apikey"
            )
        
        client = genai.Client(api_key=api_key)
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for batch_num, i in enumerate(range(0, len(texts), batch_size)):
            batch = texts[i : i + batch_size]
            await self.stream_progress(
                node_id,
                0.3 + (batch_num / total_batches) * 0.6,
                f"Processing batch {batch_num + 1}/{total_batches}...",
            )
            
            try:
                result = client.models.embed_content(
                    model=model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=output_dimensionality,
                    ),
                )
                # Extract embedding values
                batch_embeddings = [list(emb.values) for emb in result.embeddings]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Gemini embedding error: {e}")
                raise
        
        model_info = get_model_pricing("gemini", model)
        dimension = output_dimensionality if model_info else 768
        
        result = {
            "embeddings": all_embeddings,
            "provider": "gemini",
            "model": model,
            "count": len(all_embeddings),
            "dimension": dimension,
            "task_type": task_type,
        }
        
        # Pass through chunks if available
        if "chunks" in inputs:
            result["chunks"] = inputs["chunks"]
        
        await self.stream_progress(node_id, 0.95, "Embeddings complete")
        await self.stream_output(node_id, result, partial=False)
        
        return result

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost based on provider and input size using centralized pricing."""
        provider = config.get("provider", "openai")
        text_input = inputs.get("text") or inputs.get("chunks", [])
        
        if isinstance(text_input, str):
            texts = [text_input]
        else:
            texts = text_input
        
        # Use centralized pricing system
        if provider == "voyage_ai" or provider == "voyageai":
            model = config.get("voyage_model", "voyage-3.5")
            return calculate_embedding_cost_from_texts("voyage_ai", model, texts)
        elif provider == "openai":
            # Use centralized pricing for OpenAI
            model = config.get("openai_model", "text-embedding-3-small")
            # Check if we should use batch pricing (if batch_size > 1 and multiple texts)
            batch_size = config.get("batch_size", 100)
            use_batch = len(texts) > 1 and batch_size > 1
            return calculate_embedding_cost_from_texts("openai", model, texts, use_batch_pricing=use_batch)
        elif provider == "cohere":
            # Use centralized pricing for Cohere
            model = config.get("cohere_model", "embed-english-v3.0")
            return calculate_embedding_cost_from_texts("cohere", model, texts)
        elif provider == "gemini" or provider == "google":
            model = config.get("gemini_model", "gemini-embedding-001")
            batch_size = config.get("batch_size", 100)
            use_batch = len(texts) > 1 and batch_size > 1
            return calculate_embedding_cost_from_texts("gemini", model, texts, use_batch_pricing=use_batch)
        
        # HuggingFace is free or has different pricing
        return 0.0
    
    async def _get_finetuned_model(self, model_id: str, provider: str) -> Dict[str, Any]:
        """Get fine-tuned model from registry."""
        try:
            import httpx
            import os
            
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            url = f"{api_base}/api/v1/models/{model_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    model_data = response.json()
                    # Verify provider matches
                    if model_data.get("provider") == provider and model_data.get("status") == "ready":
                        return model_data
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch fine-tuned model: {e}")
            return None
    
    async def _record_model_usage(
        self,
        model_id: str,
        node_type: str,
        execution_id: str = None,
        tokens: int = None,
        cost: float = None,
    ) -> None:
        """Record model usage in registry."""
        try:
            import httpx
            import os
            
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            url = f"{api_base}/api/v1/models/{model_id}/usage"
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    url,
                    json={
                        "node_type": node_type,
                        "execution_id": execution_id,
                        "tokens_used": tokens,
                        "cost": cost,
                    },
                    timeout=5.0,
                )
        except Exception as e:
            # Non-critical, just log
            logger.debug(f"Could not record model usage: {e}")

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "embeddings": {
                "type": "array",
                "description": "List of embedding vectors",
                "items": {
                    "type": "array",
                    "items": {"type": "number"},
                },
            },
            "provider": {
                "type": "string",
                "description": "Provider used",
            },
            "model": {
                "type": "string",
                "description": "Model used",
            },
            "count": {
                "type": "integer",
                "description": "Number of embeddings created",
            },
            "dimension": {
                "type": "integer",
                "description": "Embedding dimension",
            },
        }


# Register the node
NodeRegistry.register(
    "embed",
    EmbedNode,
    EmbedNode().get_metadata(),
)

