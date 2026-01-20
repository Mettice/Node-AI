"""
AI Web Search Node for NodeAI.

This node provides intelligent web search that:
- Understands the intent behind queries
- Summarizes what matters
- Filters out noise
- Returns immediately usable, structured results

Supports multiple AI search providers:
- Perplexity AI (recommended for best results)
- Tavily (AI-powered search API)
- Serper (Google Search with AI enhancement)
"""

from typing import Dict, Any, List, Optional
import httpx
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.secret_resolver import resolve_api_key
from backend.core.exceptions import NodeExecutionError


class AIWebSearchNode(BaseNode, LLMConfigMixin):
    """
    AI Web Search Node - Intelligent web search with summarization and filtering.
    
    This node acts as a "thinking layer" in your automation, understanding intent
    and returning clean, immediately usable results instead of raw search data.
    """
    
    node_type = "ai_web_search"
    name = "AI Web Search"
    description = "Intelligent web search that understands intent, summarizes results, and filters noise. Returns immediately usable, structured output."
    category = "intelligence"
    
    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AI web search with intelligent summarization.
        
        Args:
            inputs: Input data containing 'query' or 'text'
            config: Configuration with provider, API keys, and options
            
        Returns:
            Structured search results with summary, key points, and sources
        """
        node_id = config.get("_node_id", "ai_web_search")
        
        try:
            # Get query from inputs or config
            query = inputs.get("query") or inputs.get("text") or config.get("query", "")
            if not query:
                raise ValueError("Query is required. Provide 'query' or 'text' in inputs or config.")
            
            await self.stream_progress(node_id, 0.1, f"Understanding query intent: {query[:50]}...")
            
            # Get provider and API keys
            # Handle provider conflict: if enhance_with_llm is enabled, search provider might be in search_provider
            provider = config.get("search_provider") or config.get("provider", "perplexity")
            user_id = config.get("_user_id")
            
            # Get API keys
            perplexity_api_key = resolve_api_key(
                config, "perplexity_api_key", user_id=user_id
            ) or config.get("perplexity_api_key", "")
            
            tavily_api_key = resolve_api_key(
                config, "tavily_api_key", user_id=user_id
            ) or config.get("tavily_api_key", "")
            
            serper_api_key = resolve_api_key(
                config, "serper_api_key", user_id=user_id
            ) or config.get("serper_api_key", "")
            
            # Perform AI-powered search
            await self.stream_progress(node_id, 0.3, f"Searching with {provider}...")
            
            if provider == "perplexity":
                if not perplexity_api_key:
                    raise ValueError("Perplexity API key is required. Get one at https://www.perplexity.ai/")
                search_result = await self._search_perplexity(query, perplexity_api_key, config)
            elif provider == "tavily":
                if not tavily_api_key:
                    raise ValueError("Tavily API key is required. Get one at https://tavily.com/")
                search_result = await self._search_tavily(query, tavily_api_key, config)
            elif provider == "serper":
                if not serper_api_key:
                    raise ValueError("Serper API key is required. Get one at https://serper.dev/")
                search_result = await self._search_serper_enhanced(query, serper_api_key, config)
            else:
                raise ValueError(f"Unknown provider: {provider}. Supported: perplexity, tavily, serper")
            
            await self.stream_progress(node_id, 0.8, "Processing and structuring results...")
            
            # Optionally enhance with LLM summarization if enabled
            enhance_with_llm = config.get("enhance_with_llm", False)
            if enhance_with_llm:
                llm_config = self._resolve_llm_config(config)
                if llm_config:
                    search_result = await self._enhance_with_llm(query, search_result, llm_config, config)
            
            await self.stream_progress(node_id, 1.0, "Search completed")
            
            return {
                "summary": search_result.get("summary", ""),
                "answer": search_result.get("answer", ""),
                "key_points": search_result.get("key_points", []),
                "sources": search_result.get("sources", []),
                "raw_results": search_result.get("raw_results", []),
                "provider": provider,
                "query": query,
                "display_type": "text",
                "primary_content": search_result.get("summary") or search_result.get("answer", ""),
            }
            
        except Exception as e:
            raise NodeExecutionError(f"AI web search failed: {str(e)}")
    
    async def _search_perplexity(
        self, query: str, api_key: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search using Perplexity AI (best for understanding intent)."""
        model = config.get("perplexity_model", "sonar")
        max_tokens = config.get("max_tokens", 1000)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that provides accurate, up-to-date information from the web. Summarize the most relevant information, filter out noise, and provide key points that are immediately actionable."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                    "return_citations": True,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                citations = data.get("citations", [])
                
                # Extract key points from answer
                key_points = self._extract_key_points(answer)
                
                return {
                    "summary": answer,
                    "answer": answer,
                    "key_points": key_points,
                    "sources": citations[:10] if citations else [],
                    "raw_results": [{"answer": answer, "citations": citations}],
                }
            else:
                raise NodeExecutionError(
                    f"Perplexity API error: {response.status_code} - {response.text[:200]}"
                )
    
    async def _search_tavily(
        self, query: str, api_key: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search using Tavily AI Search API."""
        max_results = config.get("max_results", 5)
        search_depth = config.get("search_depth", "basic")  # basic or advanced
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False,
                    "max_results": max_results,
                },
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                results = data.get("results", [])
                
                # Extract key points
                key_points = self._extract_key_points(answer) if answer else []
                
                # Format sources
                sources = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:200],
                    }
                    for r in results[:10]
                ]
                
                return {
                    "summary": answer or self._summarize_results(results),
                    "answer": answer,
                    "key_points": key_points,
                    "sources": sources,
                    "raw_results": results,
                }
            else:
                raise NodeExecutionError(
                    f"Tavily API error: {response.status_code} - {response.text[:200]}"
                )
    
    async def _search_serper_enhanced(
        self, query: str, api_key: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search using Serper (Google Search) with AI enhancement."""
        num_results = config.get("num_results", 10)
        
        async with httpx.AsyncClient() as client:
            # Get search results
            response = await client.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": num_results},
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                organic = data.get("organic", [])
                
                # Summarize results
                summary = self._summarize_results(organic)
                key_points = self._extract_key_points(summary)
                
                # Format sources
                sources = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                    }
                    for r in organic[:10]
                ]
                
                return {
                    "summary": summary,
                    "answer": summary,
                    "key_points": key_points,
                    "sources": sources,
                    "raw_results": organic,
                }
            else:
                raise NodeExecutionError(
                    f"Serper API error: {response.status_code} - {response.text[:200]}"
                )
    
    async def _enhance_with_llm(
        self,
        query: str,
        search_result: Dict[str, Any],
        llm_config: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enhance search results with LLM summarization and filtering."""
        
        # Build prompt for LLM enhancement
        raw_content = search_result.get("summary") or search_result.get("answer", "")
        sources = search_result.get("sources", [])
        
        enhancement_prompt = f"""You are an expert at filtering and summarizing web search results.

Query: {query}

Search Results:
{raw_content}

Sources:
{chr(10).join([f"- {s.get('title', s.get('url', ''))}: {s.get('snippet', s.get('content', ''))[:150]}" for s in sources[:5]])}

Please provide:
1. A concise summary that directly answers the query
2. 3-5 key actionable points
3. Filter out any irrelevant or low-quality information

Format your response as:
SUMMARY: [your summary]
KEY POINTS:
- [point 1]
- [point 2]
- [point 3]
"""
        
        try:
            # Use LLM to enhance (using mixin method)
            llm_response = await self._call_llm(
                prompt=enhancement_prompt,
                llm_config=llm_config,
                max_tokens=2000,
            )
            
            # Parse enhanced response
            enhanced_summary = self._parse_llm_enhancement(llm_response)
            
            return {
                **search_result,
                "summary": enhanced_summary.get("summary", raw_content),
                "key_points": enhanced_summary.get("key_points", search_result.get("key_points", [])),
                "enhanced": True,
            }
        except Exception as e:
            # Fallback to original results if LLM enhancement fails
            await self.stream_log(
                config.get("_node_id", "ai_web_search"),
                f"LLM enhancement failed, using original results: {e}",
                "warning"
            )
            return search_result
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text."""
        if not text:
            return []
        
        # Simple extraction: look for bullet points or numbered lists
        lines = text.split("\n")
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Match bullet points or numbered items
            if line.startswith(("-", "•", "*")) or (line and line[0].isdigit() and ". " in line[:5]):
                point = line.lstrip("-•*0123456789. ").strip()
                if point and len(point) > 10:  # Filter out very short points
                    key_points.append(point)
        
        # If no bullet points found, try to extract sentences
        if not key_points:
            sentences = [s.strip() for s in text.split(". ") if len(s.strip()) > 20]
            key_points = sentences[:5]  # Take first 5 sentences
        
        return key_points[:5]  # Limit to 5 key points
    
    def _summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """Summarize raw search results."""
        if not results:
            return "No results found."
        
        summaries = []
        for i, result in enumerate(results[:5], 1):
            title = result.get("title", result.get("name", ""))
            snippet = result.get("snippet", result.get("content", result.get("description", "")))
            
            if title or snippet:
                summaries.append(f"{i}. {title}: {snippet[:200]}")
        
        return "\n\n".join(summaries)
    
    def _parse_llm_enhancement(self, response: str) -> Dict[str, Any]:
        """Parse LLM enhancement response."""
        summary = ""
        key_points = []
        
        # Extract summary
        if "SUMMARY:" in response:
            summary_part = response.split("SUMMARY:")[1]
            if "KEY POINTS:" in summary_part:
                summary = summary_part.split("KEY POINTS:")[0].strip()
            else:
                summary = summary_part.strip()
        
        # Extract key points
        if "KEY POINTS:" in response:
            points_part = response.split("KEY POINTS:")[1]
            for line in points_part.split("\n"):
                line = line.strip()
                if line.startswith(("-", "•", "*")) or (line and line[0].isdigit()):
                    point = line.lstrip("-•*0123456789. ").strip()
                    if point:
                        key_points.append(point)
        
        return {
            "summary": summary or response[:500],
            "key_points": key_points[:5],
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get node configuration schema."""
        base_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "title": "Search Query",
                    "description": "The search query (can also be provided via inputs)",
                },
                "provider": {
                    "type": "string",
                    "enum": ["perplexity", "tavily", "serper"],
                    "default": "perplexity",
                    "title": "Search Provider",
                    "description": "AI search provider to use. Perplexity is recommended for best results.",
                },
                "perplexity_api_key": {
                    "type": "string",
                    "title": "Perplexity API Key",
                    "description": "API key for Perplexity AI (required if using Perplexity)",
                },
                "tavily_api_key": {
                    "type": "string",
                    "title": "Tavily API Key",
                    "description": "API key for Tavily AI Search (required if using Tavily)",
                },
                "serper_api_key": {
                    "type": "string",
                    "title": "Serper API Key",
                    "description": "API key for Serper (required if using Serper)",
                },
                "perplexity_model": {
                    "type": "string",
                    "enum": ["sonar", "sonar-pro", "sonar-online", "sonar-pro-online"],
                    "default": "sonar",
                    "title": "Perplexity Model",
                    "description": "Perplexity model to use",
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 1000,
                    "minimum": 100,
                    "maximum": 4000,
                    "title": "Max Tokens",
                    "description": "Maximum tokens for response",
                },
                "max_results": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                    "title": "Max Results",
                    "description": "Maximum number of results to return (for Tavily/Serper)",
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "default": "basic",
                    "title": "Search Depth",
                    "description": "Search depth for Tavily (basic = faster, advanced = more comprehensive)",
                },
                "enhance_with_llm": {
                    "type": "boolean",
                    "default": False,
                    "title": "Enhance with LLM",
                    "description": "Use an LLM to further refine and summarize results (requires LLM config)",
                },
            },
            "required": ["query"],
        }
        
        # Add LLM config fields if enhancement is enabled
        # Get LLM schema section from mixin
        llm_schema_section = self._get_llm_schema_section()
        if llm_schema_section:
            base_schema["properties"].update(llm_schema_section)
        
        return base_schema
    
    def get_metadata(self):
        """Return node metadata."""
        from backend.core.models import NodeMetadata
        
        return NodeMetadata(
            type=self.node_type,
            name=self.name,
            description=self.description,
            category=self.category,
            icon="search",  # Use search icon
            config_schema=self.get_schema(),
        )


# Register the node
from backend.core.node_registry import NodeRegistry

NodeRegistry.register(
    "ai_web_search",
    AIWebSearchNode,
    AIWebSearchNode().get_metadata(),
)
