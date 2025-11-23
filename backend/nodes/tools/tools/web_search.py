"""
Web search tool implementation.
Supports: DuckDuckGo, SerpAPI, Brave Search, Serper, Perplexity
"""

import asyncio
import httpx
from typing import Dict, Any, Callable


def get_web_search_schema() -> Dict[str, Any]:
    """Get schema fields for web search tool."""
    return {
        "web_search_provider": {
            "type": "string",
            "enum": ["brave", "serpapi", "duckduckgo", "serper", "perplexity"],
            "default": "duckduckgo",
            "title": "Search Provider",
            "description": "Web search provider to use",
        },
        "web_search_api_key": {
            "type": "string",
            "title": "API Key",
            "description": "API key for search provider (if required)",
        },
        "serper_api_key": {
            "type": "string",
            "title": "Serper API Key",
            "description": "API key for Serper (Google Search API)",
        },
        "perplexity_api_key": {
            "type": "string",
            "title": "Perplexity API Key",
            "description": "API key for Perplexity (AI-powered search)",
        },
    }


async def _search_duckduckgo(query: str) -> str:
    """Search using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                formatted = "\n".join([
                    f"{i+1}. {r.get('title', 'No title')}\n   {r.get('body', 'No description')}\n   {r.get('href', 'No URL')}"
                    for i, r in enumerate(results)
                ])
                return formatted
            return f"No results found for: {query}"
    except ImportError:
        return "Error: duckduckgo-search package not installed. Install with: pip install duckduckgo-search"


async def _search_serpapi(query: str, api_key: str) -> str:
    """Search using SerpAPI."""
    if not api_key:
        return "Error: API key required for SerpAPI"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": api_key}
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("organic_results", [])[:5]
            formatted = "\n".join([
                f"{i+1}. {r.get('title', 'No title')}\n   {r.get('snippet', 'No description')}\n   {r.get('link', 'No URL')}"
                for i, r in enumerate(results)
            ])
            return formatted
        return f"Error: Search failed with status {response.status_code}"


async def _search_brave(query: str, api_key: str) -> str:
    """Search using Brave Search."""
    if not api_key:
        return "Error: API key required for Brave Search"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query},
            headers={"X-Subscription-Token": api_key}
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("web", {}).get("results", [])[:5]
            formatted = "\n".join([
                f"{i+1}. {r.get('title', 'No title')}\n   {r.get('description', 'No description')}\n   {r.get('url', 'No URL')}"
                for i, r in enumerate(results)
            ])
            return formatted
        return f"Error: Search failed with status {response.status_code}"


async def _search_serper(query: str, api_key: str) -> str:
    """Search using Serper."""
    if not api_key:
        return "Error: API key required for Serper"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": 10},
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("organic", [])[:10]
            if results:
                formatted = "\n".join([
                    f"{i+1}. {r.get('title', 'No title')}\n   {r.get('snippet', 'No description')}\n   {r.get('link', 'No URL')}"
                    for i, r in enumerate(results)
                ])
                return formatted
            return f"No results found for: {query}"
        return f"Error: Search failed with status {response.status_code}: {response.text[:200]}"


async def _search_perplexity(query: str, api_key: str) -> str:
    """Search using Perplexity AI."""
    if not api_key:
        return "Error: API key required for Perplexity"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate, up-to-date information from the web."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1000
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
            
            if answer:
                result = f"Answer: {answer}\n\n"
                if citations:
                    result += "Sources:\n"
                    result += "\n".join([f"- {cite}" for cite in citations[:5]])
                return result
            return "No answer generated"
        return f"Error: Search failed with status {response.status_code}: {response.text[:200]}"


def create_web_search_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create web search tool function."""
    async def search_func_async(query: str) -> str:
        """Search the web for information."""
        provider = config.get("web_search_provider", "duckduckgo")
        api_key = config.get("web_search_api_key", "")
        serper_api_key = config.get("serper_api_key", "") or api_key
        perplexity_api_key = config.get("perplexity_api_key", "") or api_key
        
        try:
            if provider == "duckduckgo":
                return await _search_duckduckgo(query)
            elif provider == "serpapi":
                return await _search_serpapi(query, api_key)
            elif provider == "brave":
                return await _search_brave(query, api_key)
            elif provider == "serper":
                return await _search_serper(query, serper_api_key)
            elif provider == "perplexity":
                return await _search_perplexity(query, perplexity_api_key)
            else:
                return f"Error: Unknown search provider: {provider}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Wrapper to make async function work with LangChain Tool
    def search_func(query: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(search_func_async(query))
        except RuntimeError:
            # If no event loop, create one
            return asyncio.run(search_func_async(query))
    
    return search_func

