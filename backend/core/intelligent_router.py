"""
Intelligent Data Router for Nodeflow.

This module provides AI-powered data routing between nodes, eliminating
the need for manual data mapping. The router understands:
- What data each node needs (from schema)
- What data is available (from upstream nodes)
- Semantic relationships between fields
- Context-aware mapping decisions

This makes Nodeflow truly "agentic" - agents decide what to pass where.
"""

from typing import Any, Dict, List, Optional
from backend.utils.logger import get_logger
from backend.core.secret_resolver import resolve_api_key
from backend.config import settings

logger = get_logger(__name__)

# Note: We're using our OWN LLM infrastructure (same as clients!)
# This is "eating our own dog food" - using semantic understanding
# (like vector search) to build intelligent agents that make decisions.


class IntelligentRouter:
    """
    Intelligent data router that uses LLM understanding to automatically
    map data between nodes without manual configuration.
    """
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        """
        Initialize intelligent router.
        
        Args:
            provider: LLM provider to use (openai, anthropic, gemini, etc.)
            model: Model name (e.g., "gpt-4o-mini", "claude-3-5-sonnet-20241022")
        """
        self.provider = provider
        self.model = model
        self._cache: Dict[str, Dict[str, Any]] = {}  # Cache routing decisions
    
    async def route_data(
        self,
        target_node_type: str,
        target_node_schema: Dict[str, Any],
        available_data: Dict[str, Any],
        source_node_types: List[str],
        workflow_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Intelligently route available data to target node inputs.
        
        Args:
            target_node_type: Type of target node (e.g., "chat", "email")
            target_node_schema: JSON schema of target node inputs
            available_data: Data available from upstream nodes
            source_node_types: Types of source nodes
            workflow_context: Optional context about the workflow
            
        Returns:
            Mapped input dictionary for target node
        """
        # Check cache first
        cache_key = self._get_cache_key(
            target_node_type, 
            list(available_data.keys()),
            source_node_types
        )
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.debug(f"Using cached routing decision for {target_node_type}")
            return self._apply_cached_routing(cached, available_data)
        
        # Use intelligent routing
        try:
            routed_data = await self._intelligent_route(
                target_node_type,
                target_node_schema,
                available_data,
                source_node_types,
                workflow_context,
            )
            
            # Cache the routing decision
            self._cache[cache_key] = routed_data
            return routed_data
        except Exception as e:
            logger.warning(f"Intelligent routing failed, falling back to rule-based: {e}")
            return self._fallback_route(target_node_type, available_data)
    
    async def _intelligent_route(
        self,
        target_node_type: str,
        target_node_schema: Dict[str, Any],
        available_data: Dict[str, Any],
        source_node_types: List[str],
        workflow_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Use LLM to intelligently route data.
        """
        # Build prompt for LLM
        prompt = self._build_routing_prompt(
            target_node_type,
            target_node_schema,
            available_data,
            source_node_types,
            workflow_context,
        )
        
        # Call LLM (lightweight call - just for routing decision)
        routing_decision = await self._call_llm_for_routing(prompt)
        
        # Apply routing decision
        return self._apply_routing_decision(routing_decision, available_data)
    
    def _build_routing_prompt(
        self,
        target_node_type: str,
        target_node_schema: Dict[str, Any],
        available_data: Dict[str, Any],
        source_node_types: List[str],
        workflow_context: Optional[str] = None,
    ) -> str:
        """Build prompt for LLM routing decision."""
        
        # Extract required/expected fields from schema
        required_fields = []
        optional_fields = []
        
        properties = target_node_schema.get("properties", {})
        required = target_node_schema.get("required", [])
        
        for field_name, field_schema in properties.items():
            field_info = {
                "name": field_name,
                "type": field_schema.get("type", "string"),
                "description": field_schema.get("description", ""),
                "title": field_schema.get("title", field_name),
            }
            if field_name in required:
                required_fields.append(field_info)
            else:
                optional_fields.append(field_info)
        
        # Format available data
        available_fields = []
        for key, value in available_data.items():
            value_type = type(value).__name__
            value_preview = str(value)[:100] if value else "null"
            available_fields.append({
                "name": key,
                "type": value_type,
                "preview": value_preview,
            })
        
        prompt = f"""You are an intelligent data router for a workflow automation system.

TARGET NODE: {target_node_type}
Source Nodes: {', '.join(source_node_types)}
Workflow Context: {workflow_context or 'General workflow'}

TARGET NODE NEEDS:
Required Fields:
{self._format_fields(required_fields)}

Optional Fields:
{self._format_fields(optional_fields)}

AVAILABLE DATA FROM UPSTREAM:
{self._format_available_fields(available_fields)}

TASK: Map available data to target node inputs intelligently.
- Match fields by semantic meaning, not just name
- Handle synonyms (e.g., "reply_text" → "body", "message" → "text")
- Extract relevant data from nested structures
- Use context clues (e.g., email nodes need "to", "subject", "body")
- Return ONLY a JSON object with field mappings

Example:
{{
  "to": "{{sender}}",
  "subject": "Re: {{subject}}",
  "body": "{{reply_text}}"
}}

Return JSON mapping only:"""
        
        return prompt
    
    def _format_fields(self, fields: List[Dict[str, Any]]) -> str:
        """Format field list for prompt."""
        if not fields:
            return "  (none)"
        return "\n".join([
            f"  - {f['name']} ({f['type']}): {f.get('description', f.get('title', ''))}"
            for f in fields
        ])
    
    def _format_available_fields(self, fields: List[Dict[str, Any]]) -> str:
        """Format available fields for prompt."""
        if not fields:
            return "  (none)"
        return "\n".join([
            f"  - {f['name']} ({f['type']}): {f['preview']}"
            for f in fields
        ])
    
    async def _call_llm_for_routing(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM to get routing decision.
        
        Uses our unified LLM infrastructure - same as what we provide to clients!
        This means we're "eating our own dog food" - using our own features.
        Supports all providers: OpenAI, Anthropic, Gemini, etc.
        """
        try:
            import json
            from backend.core.secret_resolver import resolve_api_key
            from backend.config import settings
            
            # Use our unified LLM infrastructure (same as chat nodes!)
            provider = self.provider.lower()
            model = self.model
            
            # Route to appropriate provider (same pattern as ChatNode)
            if provider == "openai":
                return await self._call_openai(prompt, model)
            elif provider == "anthropic":
                return await self._call_anthropic(prompt, model)
            elif provider == "gemini" or provider == "google":
                return await self._call_gemini(prompt, model)
            else:
                # Fallback to OpenAI if provider not supported
                logger.warning(f"Provider {provider} not supported for routing, falling back to OpenAI")
                return await self._call_openai(prompt, "gpt-4o-mini")
            
        except Exception as e:
            logger.error(f"LLM routing call failed: {e}")
            raise
    
    async def _call_openai(self, prompt: str, model: str) -> Dict[str, Any]:
        """Call OpenAI for routing decision."""
        import openai
        from backend.core.secret_resolver import resolve_api_key
        from backend.config import settings
        
        api_key = resolve_api_key({}, "openai_api_key") or settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a data routing assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent routing
            max_tokens=500,  # Routing decisions are small
        )
        
        result_text = response.choices[0].message.content.strip()
        return self._parse_json_response(result_text)
    
    async def _call_anthropic(self, prompt: str, model: str) -> Dict[str, Any]:
        """Call Anthropic Claude for routing decision."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ValueError(
                "anthropic not installed. Install it with: pip install anthropic"
            )
        
        from backend.core.secret_resolver import resolve_api_key
        from backend.config import settings
        
        api_key = resolve_api_key({}, "anthropic_api_key") or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not found")
        
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model=model,
            max_tokens=500,
            temperature=0.1,
            system="You are a data routing assistant. Return only valid JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        result_text = response.content[0].text.strip()
        return self._parse_json_response(result_text)
    
    async def _call_gemini(self, prompt: str, model: str) -> Dict[str, Any]:
        """Call Google Gemini for routing decision."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ValueError(
                "google-generativeai not installed. Install it with: pip install google-generativeai"
            )
        
        from backend.core.secret_resolver import resolve_api_key
        from backend.config import settings
        
        api_key = resolve_api_key({}, "google_api_key") or settings.google_api_key
        if not api_key:
            raise ValueError("Google API key not found")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini Pro for routing
        gemini_model = genai.GenerativeModel(model)
        
        full_prompt = f"You are a data routing assistant. Return only valid JSON.\n\n{prompt}"
        
        response = gemini_model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 500,
            }
        )
        
        result_text = response.text.strip()
        return self._parse_json_response(result_text)
    
    def _parse_json_response(self, result_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling markdown code blocks."""
        import json
        
        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        routing_decision = json.loads(result_text)
        return routing_decision
    
    def _apply_routing_decision(
        self,
        routing_decision: Dict[str, Any],
        available_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply routing decision to available data.
        Supports template syntax like {{field_name}}.
        """
        routed_data = {}
        
        for target_field, mapping_expression in routing_decision.items():
            try:
                # Handle simple field references: "{{field_name}}"
                if isinstance(mapping_expression, str) and mapping_expression.startswith("{{") and mapping_expression.endswith("}}"):
                    source_field = mapping_expression[2:-2].strip()
                    if source_field in available_data:
                        routed_data[target_field] = available_data[source_field]
                    else:
                        logger.warning(f"Source field '{source_field}' not found in available data")
                
                # Handle direct values
                elif mapping_expression not in available_data:
                    # Try to evaluate as template
                    routed_data[target_field] = self._evaluate_template(mapping_expression, available_data)
                
                # Handle direct field mapping
                else:
                    routed_data[target_field] = available_data[mapping_expression]
                    
            except Exception as e:
                logger.warning(f"Failed to apply routing for {target_field}: {e}")
        
        return routed_data
    
    def _evaluate_template(self, template: str, data: Dict[str, Any]) -> str:
        """Evaluate template string with available data."""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def _apply_cached_routing(
        self,
        cached_decision: Dict[str, Any],
        available_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply cached routing decision."""
        return self._apply_routing_decision(cached_decision, available_data)
    
    def _fallback_route(
        self,
        target_node_type: str,
        available_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fallback to rule-based routing if intelligent routing fails.
        This is the current behavior.
        """
        # Use existing rule-based logic
        routed = {}
        
        # Common mappings
        if "text" in available_data:
            routed["text"] = available_data["text"]
            routed["query"] = available_data["text"]
            routed["input"] = available_data["text"]
        
        if "output" in available_data:
            routed["text"] = available_data["output"]
        
        # Node-type specific fallbacks
        if target_node_type == "email" or "send_email" in target_node_type:
            if "sender" in available_data:
                routed["to"] = available_data["sender"]
            if "reply_text" in available_data:
                routed["body"] = available_data["reply_text"]
            elif "text" in available_data:
                routed["body"] = available_data["text"]
        
        # Pass through all available data as fallback
        for key, value in available_data.items():
            if key not in routed:
                routed[key] = value
        
        return routed
    
    def _get_cache_key(
        self,
        target_node_type: str,
        available_keys: List[str],
        source_node_types: List[str],
    ) -> str:
        """Generate cache key for routing decision."""
        return f"{target_node_type}:{','.join(sorted(available_keys))}:{','.join(sorted(source_node_types))}"


# Global router instance
_intelligent_router: Optional[IntelligentRouter] = None


def get_intelligent_router() -> IntelligentRouter:
    """
    Get or create global intelligent router instance.
    
    Uses configuration from settings to determine provider/model.
    This means we're using the SAME LLM infrastructure as our clients!
    """
    global _intelligent_router
    if _intelligent_router is None:
        # Read provider/model from settings (can be overridden via env vars)
        # Default: OpenAI gpt-4o-mini (fast and cheap for routing)
        provider = getattr(settings, 'intelligent_router_provider', 'openai')
        model = getattr(settings, 'intelligent_router_model', 'gpt-4o-mini')
        
        _intelligent_router = IntelligentRouter(provider=provider, model=model)
        logger.info(f"Initialized intelligent router with {provider}/{model}")
    return _intelligent_router


def enable_intelligent_routing(enabled: bool = True, provider: Optional[str] = None, model: Optional[str] = None):
    """
    Enable/disable intelligent routing globally.
    
    Args:
        enabled: Enable or disable intelligent routing
        provider: Optional LLM provider (openai, anthropic, gemini)
        model: Optional model name (e.g., "gpt-4o-mini", "claude-3-5-sonnet-20241022")
    """
    global _intelligent_router
    if enabled:
        if provider and model:
            _intelligent_router = IntelligentRouter(provider=provider, model=model)
        else:
            _intelligent_router = get_intelligent_router()  # Use default from settings
    else:
        _intelligent_router = None


async def route_data_intelligently(
    target_node_type: str,
    target_node_schema: Dict[str, Any],
    available_data: Dict[str, Any],
    source_node_types: List[str],
    workflow_context: Optional[str] = None,
    use_intelligent: bool = True,
) -> Dict[str, Any]:
    """
    Route data intelligently between nodes.
    
    If intelligent routing is enabled and available, uses LLM to understand
    context and map data semantically. Falls back to rule-based routing.
    """
    if use_intelligent and _intelligent_router is not None:
        try:
            return await get_intelligent_router().route_data(
                target_node_type,
                target_node_schema,
                available_data,
                source_node_types,
                workflow_context,
            )
        except Exception as e:
            logger.warning(f"Intelligent routing failed, using fallback: {e}")
    
    # Fallback to rule-based
    router = IntelligentRouter()
    return router._fallback_route(target_node_type, available_data)

