"""
Generic Chat Node for NodeAI.

This node supports multiple LLM providers:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- (More can be added later)

Also supports built-in conversation memory.
"""

import re
from typing import Any, Dict, List
from datetime import datetime
import uuid

from openai import OpenAI

from backend.config import settings
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger
from backend.utils.model_pricing import (
    calculate_llm_cost,
    get_available_models,
    ModelType,
)

logger = get_logger(__name__)

# In-memory storage for chat conversations
# Key: session_id, Value: List of messages
_chat_memory: Dict[str, List[Dict[str, Any]]] = {}


class ChatNode(BaseNode):
    """
    Generic Chat Node.
    
    Supports multiple LLM providers with a dropdown selector.
    Each provider has its own configuration options.
    """

    node_type = "chat"
    name = "Chat"
    description = "Generate responses using various LLM providers (OpenAI, Anthropic, etc.)"
    category = "llm"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the chat node.
        
        Supports multiple providers based on config selection.
        """
        provider = config.get("provider", "openai")
        
        # Route to appropriate provider
        if provider == "openai":
            return await self._chat_openai(inputs, config)
        elif provider == "azure_openai" or provider == "azure":
            return await self._chat_azure_openai(inputs, config)
        elif provider == "anthropic":
            return await self._chat_anthropic(inputs, config)
        elif provider == "gemini" or provider == "google":
            return await self._chat_gemini(inputs, config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _render_template(
        self,
        template: str,
        inputs: Dict[str, Any],
    ) -> str:
        """
        Render template with variable substitution.
        
        Supports {variable} syntax, e.g., {context}, {query}
        """
        # Find all variables in template
        variables = re.findall(r"\{(\w+)\}", template)
        
        # Replace variables with values from inputs
        rendered = template
        for var in variables:
            value = inputs.get(var, "")
            
            # Handle special cases
            if var == "context" and not value:
                # Try to get from results (from search node)
                results = inputs.get("results", [])
                if results:
                    # Format search results as context
                    formatted_context = "\n\n".join([
                        f"[{i+1}] {item.get('text', '')}" 
                        for i, item in enumerate(results)
                    ])
                    value = formatted_context
            
            if isinstance(value, list):
                # If it's a list (like search results), format it
                if var == "context" or var == "results":
                    # Format search results as context
                    formatted_context = "\n\n".join([
                        f"[{i+1}] {item.get('text', '') if isinstance(item, dict) else str(item)}" 
                        for i, item in enumerate(value)
                    ])
                    value = formatted_context
                else:
                    value = "\n".join(str(v) for v in value)
            
            rendered = rendered.replace(f"{{{var}}}", str(value))
        
        return rendered

    async def _chat_openai(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate response using OpenAI with streaming support."""
        # Debug: Log what we received
        logger.info(f"Chat Node - Config keys: {list(config.keys())}, Inputs keys: {list(inputs.keys())}")
        logger.info(f"Chat Node - Query from config: {config.get('query')}, Query from inputs: {inputs.get('query')}")
        logger.info(f"Chat Node - Results from inputs: {inputs.get('results')}, Results count: {len(inputs.get('results', []))}")
        
        # Check if using fine-tuned model
        use_finetuned = config.get("use_finetuned_model", False)
        finetuned_model_id = config.get("finetuned_model_id")
        
        if use_finetuned and finetuned_model_id:
            # Get fine-tuned model from registry
            model_data = await self._get_finetuned_model(finetuned_model_id, "openai")
            if not model_data:
                raise ValueError(f"Fine-tuned model not found: {finetuned_model_id}")
            # Use the provider model ID (e.g., ft:gpt-3.5-turbo:org:model:id)
            model = model_data["model_id"]
            # Track usage
            await self._record_model_usage(finetuned_model_id, "chat", config.get("_execution_id"))
        else:
            model = config.get("openai_model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 500)
        system_prompt = config.get("system_prompt", "")
        user_prompt_template = config.get("user_prompt_template", "{context}\n\nQuestion: {query}\n\nAnswer:")
        
        # Get node ID for streaming
        node_id = config.get("_node_id", "chat")
        
        # Stream chat started
        await self.stream_event(
            "node_started",
            node_id,
            {"provider": "openai", "model": model},
        )
        await self.stream_progress(node_id, 0.1, "Preparing chat request...")
        
        # Memory support
        use_memory = config.get("use_memory", False)
        session_id = config.get("session_id", "default")
        memory_limit = config.get("memory_limit", 10)  # Number of past messages to include
        
        # Prepare inputs for template rendering
        template_inputs = inputs.copy()
        # Add query from config if not in inputs
        if "query" not in template_inputs:
            template_inputs["query"] = config.get("query", "")
        
        # Render template
        user_prompt = self._render_template(user_prompt_template, template_inputs)
        
        # Use API key from config if provided, otherwise fall back to settings
        api_key = config.get("openai_api_key") or settings.openai_api_key
        client = OpenAI(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if memory is enabled
        if use_memory:
            conversation_history = _chat_memory.get(session_id, [])
            # Get recent messages (limit to memory_limit)
            recent_history = conversation_history[-memory_limit:] if memory_limit > 0 else conversation_history
            messages.extend(recent_history)
            logger.info(f"Using memory: {len(recent_history)} past messages for session {session_id}")
        
        messages.append({"role": "user", "content": user_prompt})
        
        await self.stream_progress(node_id, 0.3, "Sending request to OpenAI...")
        
        try:
            # Use streaming for real-time updates
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,  # Enable streaming
            )
            
            # Collect streaming response
            result_chunks = []
            result = ""
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            await self.stream_progress(node_id, 0.5, "Receiving response...")
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    result_chunks.append(content)
                    result += content
                    
                    # Stream partial output (every 50 chars to avoid too many events)
                    if len(result_chunks) % 10 == 0:
                        await self.stream_output(node_id, result, partial=True)
                
                # Update usage if available
                if chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens or 0,
                        "completion_tokens": chunk.usage.completion_tokens or 0,
                        "total_tokens": chunk.usage.total_tokens or 0,
                    }
            
            # Final output
            await self.stream_output(node_id, result, partial=False)
            await self.stream_progress(node_id, 0.9, "Response complete")
            
            # If no usage from stream, estimate
            if not any(usage.values()):
                usage = {
                    "prompt_tokens": len(user_prompt) // 4,
                    "completion_tokens": len(result) // 4,
                    "total_tokens": (len(user_prompt) + len(result)) // 4,
                }
            
            # Calculate cost based on model using centralized pricing
            cost = calculate_llm_cost("openai", model, usage["prompt_tokens"], usage["completion_tokens"])
            
            # Store in memory if enabled
            if use_memory:
                if session_id not in _chat_memory:
                    _chat_memory[session_id] = []
                
                # Store user message
                _chat_memory[session_id].append({
                    "role": "user",
                    "content": user_prompt,
                })
                
                # Store assistant response
                _chat_memory[session_id].append({
                    "role": "assistant",
                    "content": result,
                })
                
                logger.info(f"Stored conversation in memory (session: {session_id}, total: {len(_chat_memory[session_id])} messages)")
            
            await self.stream_progress(node_id, 1.0, "Chat completed")
            
            result_data = {
                "response": result,
                "provider": "openai",
                "model": model,
                "tokens_used": {
                    "input": usage["prompt_tokens"],
                    "output": usage["completion_tokens"],
                    "total": usage["total_tokens"],
                },
                "cost": cost,
                "memory_used": use_memory,
                "session_id": session_id if use_memory else None,
            }
            
            # Add fine-tuned model info if used
            if use_finetuned and finetuned_model_id:
                result_data["finetuned_model_id"] = finetuned_model_id
                result_data["is_finetuned"] = True
            
            return result_data
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    async def _chat_azure_openai(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate response using Azure OpenAI Service."""
        # Get Azure OpenAI configuration
        api_key = config.get("azure_openai_api_key") or config.get("azure_api_key")
        endpoint = config.get("azure_openai_endpoint") or config.get("azure_endpoint")
        api_version = config.get("azure_openai_api_version", "2024-02-15-preview")
        deployment_name = config.get("azure_openai_deployment") or config.get("azure_deployment")
        
        if not api_key or not endpoint or not deployment_name:
            raise ValueError(
                "Azure OpenAI requires: api_key, endpoint, and deployment_name. "
                "Set azure_openai_api_key, azure_openai_endpoint, and azure_openai_deployment in config."
            )
        
        model = config.get("azure_openai_model") or deployment_name  # Use deployment name as model
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 500)
        system_prompt = config.get("system_prompt", "")
        user_prompt_template = config.get("user_prompt_template", "{context}\n\nQuestion: {query}\n\nAnswer:")
        
        # Get node ID for streaming
        node_id = config.get("_node_id", "chat")
        
        # Stream chat started
        await self.stream_event(
            "node_started",
            node_id,
            {"provider": "azure_openai", "model": model, "deployment": deployment_name},
        )
        await self.stream_progress(node_id, 0.1, "Preparing Azure OpenAI request...")
        
        # Memory support
        use_memory = config.get("use_memory", False)
        session_id = config.get("session_id", "default")
        memory_limit = config.get("memory_limit", 10)
        
        # Prepare inputs for template rendering
        template_inputs = inputs.copy()
        if "query" not in template_inputs:
            template_inputs["query"] = config.get("query", "")
        
        # Render template
        user_prompt = self._render_template(user_prompt_template, template_inputs)
        
        # Create Azure OpenAI client
        # Azure OpenAI uses the same OpenAI SDK but with different base URL and API key
        # The base_url should be the endpoint, and deployment name is used as the model parameter
        client = OpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/deployments",
            default_headers={"api-key": api_key},
            default_query={"api-version": api_version},
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if memory is enabled
        if use_memory:
            conversation_history = _chat_memory.get(session_id, [])
            recent_history = conversation_history[-memory_limit:] if memory_limit > 0 else conversation_history
            messages.extend(recent_history)
            logger.info(f"Using memory: {len(recent_history)} past messages for session {session_id}")
        
        messages.append({"role": "user", "content": user_prompt})
        
        await self.stream_progress(node_id, 0.3, "Sending request to Azure OpenAI...")
        
        try:
            # Use streaming for real-time updates
            # For Azure OpenAI, the model parameter should be the deployment name
            # The base_url already includes the deployment path, but model is still required
            stream = client.chat.completions.create(
                model=deployment_name,  # Azure OpenAI uses deployment name as model
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            # Collect streaming response
            result_chunks = []
            result = ""
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            await self.stream_progress(node_id, 0.5, "Receiving response...")
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        result_chunks.append(content)
                        result += content
                        
                        # Stream the chunk
                        await self.stream_event(
                            "node_output",
                            node_id,
                            {"chunk": content, "accumulated": result},
                        )
                
                # Update usage if available
                if chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens or 0,
                        "completion_tokens": chunk.usage.completion_tokens or 0,
                        "total_tokens": chunk.usage.total_tokens or 0,
                    }
            
            # Save to memory if enabled
            if use_memory:
                if session_id not in _chat_memory:
                    _chat_memory[session_id] = []
                _chat_memory[session_id].append({"role": "user", "content": user_prompt})
                _chat_memory[session_id].append({"role": "assistant", "content": result})
                # Limit memory size
                if len(_chat_memory[session_id]) > memory_limit * 2:
                    _chat_memory[session_id] = _chat_memory[session_id][-memory_limit * 2:]
            
            # Calculate cost (use OpenAI pricing as Azure OpenAI is similar)
            cost = calculate_llm_cost("openai", model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
            
            await self.stream_progress(node_id, 1.0, "Response complete!")
            
            return {
                "output": result,
                "response": result,
                "text": result,
                "provider": "azure_openai",
                "model": model,
                "deployment": deployment_name,
                "usage": usage,
                "cost": cost,
            }
        except Exception as e:
            logger.error(f"Azure OpenAI chat error: {e}")
            raise

    async def _chat_anthropic(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate response using Anthropic Claude with streaming support."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ValueError(
                "anthropic not installed. Install it with: pip install anthropic"
            )
        
        # Use API key from config if provided, otherwise fall back to settings
        api_key = config.get("anthropic_api_key") or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        model = config.get("anthropic_model", "claude-3-5-sonnet-20241022")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 500)
        system_prompt = config.get("system_prompt", "")
        user_prompt_template = config.get("user_prompt_template", "{context}\n\nQuestion: {query}\n\nAnswer:")
        
        # Get node ID for streaming
        node_id = config.get("_node_id", "chat")
        
        # Stream chat started
        await self.stream_event(
            "node_started",
            node_id,
            {"provider": "anthropic", "model": model},
        )
        await self.stream_progress(node_id, 0.1, "Preparing chat request...")
        
        # Prepare inputs for template rendering
        template_inputs = inputs.copy()
        # Add query from config if not in inputs
        if "query" not in template_inputs:
            template_inputs["query"] = config.get("query", "")
        
        # Render template
        user_prompt = self._render_template(user_prompt_template, template_inputs)
        
        client = Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.3, "Sending request to Anthropic...")
        
        try:
            # Use streaming for real-time updates
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else None,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            ) as stream:
                result_chunks = []
                result = ""
                
                await self.stream_progress(node_id, 0.5, "Receiving response...")
                
                for text in stream.text_stream:
                    result_chunks.append(text)
                    result += text
                    
                    # Stream partial output (every 10 chunks to avoid too many events)
                    if len(result_chunks) % 10 == 0:
                        await self.stream_output(node_id, result, partial=True)
                
                # Get final message with usage
                message = stream.get_final_message()
                usage = message.usage
            
            # Final output
            await self.stream_output(node_id, result, partial=False)
            await self.stream_progress(node_id, 0.9, "Response complete")
            
            # Calculate cost using centralized pricing
            cost = calculate_llm_cost("anthropic", model, usage.input_tokens, usage.output_tokens)
            
            await self.stream_progress(node_id, 1.0, "Chat completed")
            
            return {
                "response": result,
                "provider": "anthropic",
                "model": model,
                "tokens_used": {
                    "input": usage.input_tokens,
                    "output": usage.output_tokens,
                    "total": usage.input_tokens + usage.output_tokens,
                },
                "cost": cost,
            }
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise
    
    async def _chat_gemini(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate response using Google Gemini."""
        try:
            from google import genai
        except ImportError:
            raise ValueError(
                "google-genai not installed. Install it with: pip install google-genai"
            )
        
        # Use API key from config if provided, otherwise fall back to settings
        api_key = config.get("gemini_api_key") or settings.gemini_api_key
        if not api_key:
            raise ValueError("Gemini API key not configured")
        
        model = config.get("gemini_model", "gemini-2.5-flash")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 500)
        system_prompt = config.get("system_prompt", "")
        user_prompt_template = config.get("user_prompt_template", "{context}\n\nQuestion: {query}\n\nAnswer:")
        
        # Get node ID for streaming
        node_id = config.get("_node_id", "chat")
        
        # Stream chat started
        await self.stream_event(
            "node_started",
            node_id,
            {"provider": "gemini", "model": model},
        )
        await self.stream_progress(node_id, 0.1, "Preparing chat request...")
        
        # Prepare inputs for template rendering
        template_inputs = inputs.copy()
        if "query" not in template_inputs:
            template_inputs["query"] = config.get("query", "")
        
        # Render template
        user_prompt = self._render_template(user_prompt_template, template_inputs)
        
        client = genai.Client(api_key=api_key)
        
        await self.stream_progress(node_id, 0.3, "Sending request to Gemini...")
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "user", "parts": [{"text": system_prompt}]})
            messages.append({"role": "user", "parts": [{"text": user_prompt}]})
            
            # Prepare config
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            # Add File Search tool if enabled
            use_file_search = config.get("gemini_use_file_search", False)
            file_search_stores = config.get("gemini_file_search_stores", [])
            metadata_filter = config.get("gemini_metadata_filter", "")
            
            if use_file_search and file_search_stores:
                await self.stream_progress(node_id, 0.4, f"Enabling File Search with {len(file_search_stores)} store(s)...")
                from google.genai import types
                
                file_search_config = types.FileSearch(
                    file_search_store_names=file_search_stores if isinstance(file_search_stores, list) else [file_search_stores],
                )
                
                if metadata_filter:
                    file_search_config.metadata_filter = metadata_filter
                
                gen_config["tools"] = [
                    types.Tool(file_search=file_search_config)
                ]
            
            # Generate response
            response = client.models.generate_content(
                model=model,
                contents=messages,
                config=gen_config,
            )
            
            result = response.text if hasattr(response, 'text') else str(response)
            
            # Extract citations if File Search was used
            citations = None
            file_search_used = False
            if use_file_search and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    file_search_used = True
                    grounding = candidate.grounding_metadata
                    if hasattr(grounding, 'grounding_chunks'):
                        citations = []
                        for chunk in grounding.grounding_chunks:
                            citation_info = {
                                "chunk_index": getattr(chunk, 'chunk_index', None),
                            }
                            if hasattr(chunk, 'retrieved_context'):
                                rc = chunk.retrieved_context
                                citation_info["file_name"] = getattr(rc, 'file_name', None)
                                citation_info["uri"] = getattr(rc, 'uri', None)
                            citations.append(citation_info)
            
            # Estimate token usage (Gemini API doesn't always return usage)
            estimated_input_tokens = len(user_prompt) // 4
            estimated_output_tokens = len(result) // 4
            
            # Calculate cost
            cost = calculate_llm_cost("gemini", model, estimated_input_tokens, estimated_output_tokens)
            
            await self.stream_progress(node_id, 1.0, "Chat completed")
            
            response_data = {
                "response": result,
                "provider": "gemini",
                "model": model,
                "tokens_used": {
                    "input": estimated_input_tokens,
                    "output": estimated_output_tokens,
                    "total": estimated_input_tokens + estimated_output_tokens,
                },
                "cost": cost,
            }
            
            if file_search_used:
                response_data["file_search_used"] = True
                if citations:
                    response_data["citations"] = citations
            
            return response_data
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    def _get_openai_model_list(self) -> List[str]:
        """Get list of available OpenAI LLM models from pricing system."""
        try:
            models = get_available_models(provider="openai", model_type=ModelType.LLM)
            # Filter out deprecated models for cleaner UI
            return [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
        except Exception as e:
            logger.warning(f"Failed to get OpenAI models from pricing system: {e}")
            # Fallback to basic list
            return [
                "gpt-5.1",
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-4.1",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
            ]
    
    def _get_anthropic_model_list(self) -> List[str]:
        """Get list of available Anthropic Claude LLM models from pricing system."""
        try:
            models = get_available_models(provider="anthropic", model_type=ModelType.LLM)
            # Filter out deprecated models and aliases for cleaner UI
            return [
                model.model_id for model in models 
                if not (model.metadata or {}).get("deprecated", False)
                and not (model.metadata or {}).get("is_alias", False)
            ]
        except Exception as e:
            logger.warning(f"Failed to get Anthropic models from pricing system: {e}")
            # Fallback to basic list
            return [
                "claude-sonnet-4-5-20250929",
                "claude-haiku-4-5-20251001",
                "claude-opus-4-1-20250805",
                "claude-3-5-sonnet-20241022",
            ]
    
    def _get_gemini_model_list(self) -> List[str]:
        """Get list of available Gemini LLM models from pricing system."""
        try:
            models = get_available_models(provider="gemini", model_type=ModelType.LLM)
            return [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
        except Exception as e:
            logger.warning(f"Failed to get Gemini models from pricing system: {e}")
            # Fallback to basic list
            return [
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.0-flash",
            ]
    
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


    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema with provider selection and dynamic config."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "LLM Provider",
                    "description": "Select the LLM provider",
                    "enum": ["openai", "azure_openai", "anthropic", "gemini"],
                    "default": "openai",
                },
                # Common config
                "temperature": {
                    "type": "number",
                    "title": "Temperature",
                    "description": "Sampling temperature (0.0 to 2.0)",
                    "default": 0.7,
                    "minimum": 0.0,
                    "maximum": 2.0,
                },
                "max_tokens": {
                    "type": "integer",
                    "title": "Max Tokens",
                    "description": "Maximum tokens in response",
                    "default": 500,
                    "minimum": 1,
                    "maximum": 4000,
                },
                "system_prompt": {
                    "type": "string",
                    "title": "System Prompt",
                    "description": "System prompt (optional)",
                    "default": "",
                },
                "user_prompt_template": {
                    "type": "string",
                    "title": "User Prompt Template",
                    "description": "Template with {variables} like {context} and {query}",
                    "default": "Context: {context}\n\nQuestion: {query}\n\nAnswer:",
                },
                # Memory settings
                "use_memory": {
                    "type": "boolean",
                    "title": "Enable Memory",
                    "description": "Remember conversation history for context",
                    "default": False,
                },
                "session_id": {
                    "type": "string",
                    "title": "Session ID",
                    "description": "Unique identifier for conversation session",
                    "default": "default",
                },
                "memory_limit": {
                    "type": "integer",
                    "title": "Memory Limit",
                    "description": "Number of past messages to include in context",
                    "default": 10,
                    "minimum": 0,
                    "maximum": 50,
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
                    "description": "OpenAI model to use (ignored if fine-tuned model is selected)",
                    "enum": self._get_openai_model_list(),
                    "default": "gpt-4o-mini",
                },
                # Anthropic config
                "anthropic_model": {
                    "type": "string",
                    "title": "Anthropic Model",
                    "description": "Anthropic Claude model to use",
                    "enum": self._get_anthropic_model_list(),
                    "default": "claude-sonnet-4-5-20250929",
                },
                # Gemini config
                "gemini_model": {
                    "type": "string",
                    "title": "Gemini Model",
                    "description": "Google Gemini model to use",
                    "enum": self._get_gemini_model_list(),
                    "default": "gemini-2.5-flash",
                },
                # Gemini File Search config
                "gemini_use_file_search": {
                    "type": "boolean",
                    "title": "Use File Search",
                    "description": "Enable Gemini File Search tool for RAG (requires File Search stores)",
                    "default": False,
                },
                "gemini_file_search_stores": {
                    "type": "array",
                    "title": "File Search Stores",
                    "description": "List of File Search store names to search (e.g., ['fileSearchStores/my-store-123'])",
                    "items": {
                        "type": "string",
                    },
                    "default": [],
                },
                "gemini_metadata_filter": {
                    "type": "string",
                    "title": "Metadata Filter (Optional)",
                    "description": "Filter documents by metadata (e.g., 'author=Robert Graves')",
                    "default": "",
                },
                # API Keys (optional - will use environment variables if not provided)
                "openai_api_key": {
                    "type": "string",
                    "title": "OpenAI API Key",
                    "description": "Optional: OpenAI API key (uses OPENAI_API_KEY env var if not provided)",
                    "default": "",
                },
                "anthropic_api_key": {
                    "type": "string",
                    "title": "Anthropic API Key",
                    "description": "Optional: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)",
                    "default": "",
                },
                "gemini_api_key": {
                    "type": "string",
                    "title": "Gemini API Key",
                    "description": "Optional: Google Gemini API key (uses GEMINI_API_KEY env var if not provided)",
                    "default": "",
                },
                # Azure OpenAI config
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
                    "description": "Azure OpenAI deployment name (e.g., gpt-4, gpt-35-turbo)",
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

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost based on provider and input size."""
        provider = config.get("provider", "openai")
        
        # Rough estimation based on input text length
        context = inputs.get("context", "")
        query = inputs.get("query", "")
        
        if isinstance(context, list):
            context_text = "\n".join([item.get("text", "") for item in context])
        else:
            context_text = str(context)
        
        total_text = context_text + "\n" + str(query)
        estimated_tokens = len(total_text) / 4  # Rough: 1 token ≈ 4 chars
        
        if provider == "openai":
            model = config.get("openai_model", "gpt-4o-mini")
            return calculate_llm_cost("openai", model, int(estimated_tokens), 500)  # Assume 500 output tokens
        elif provider == "anthropic":
            model = config.get("anthropic_model", "claude-3-5-sonnet-20241022")
            return calculate_llm_cost("anthropic", model, int(estimated_tokens), 500)
        elif provider == "gemini" or provider == "google":
            model = config.get("gemini_model", "gemini-2.5-flash")
            return calculate_llm_cost("gemini", model, int(estimated_tokens), 500)
        
        return 0.0

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "response": {
                "type": "string",
                "description": "Generated response text",
            },
            "provider": {
                "type": "string",
                "description": "Provider used",
            },
            "model": {
                "type": "string",
                "description": "Model used",
            },
            "tokens_used": {
                "type": "object",
                "description": "Token usage statistics",
            },
            "cost": {
                "type": "number",
                "description": "Cost in USD",
            },
        }


# Register the node
NodeRegistry.register(
    "chat",
    ChatNode,
    ChatNode().get_metadata(),
)

