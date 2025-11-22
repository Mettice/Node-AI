"""
RSS Feed Reader tool implementation.
Fetches and parses RSS/Atom feeds for content aggregation.
"""

import httpx
import asyncio
from typing import Dict, Any, Callable
from urllib.parse import urlparse
from datetime import datetime

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False


def get_rss_feed_schema() -> Dict[str, Any]:
    """Get schema fields for RSS feed tool."""
    return {
        "rss_feed_limit": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 100,
            "title": "Max Items",
            "description": "Maximum number of feed items to retrieve",
        },
        "rss_feed_timeout": {
            "type": "integer",
            "default": 30,
            "minimum": 5,
            "maximum": 120,
            "title": "Timeout (seconds)",
            "description": "Maximum time to wait for feed to load",
        },
        "rss_feed_include_content": {
            "type": "boolean",
            "default": True,
            "title": "Include Content",
            "description": "Include full article content in results (if available)",
        },
        "rss_feed_include_summary": {
            "type": "boolean",
            "default": True,
            "title": "Include Summary",
            "description": "Include article summary/description in results",
        },
    }


def _format_feed_item(entry: Any, include_content: bool, include_summary: bool) -> str:
    """Format a single feed item."""
    title = getattr(entry, 'title', 'No title')
    link = getattr(entry, 'link', 'No link')
    published = getattr(entry, 'published', None) or getattr(entry, 'updated', None) or 'Unknown date'
    
    result = f"Title: {title}\n"
    result += f"Link: {link}\n"
    result += f"Published: {published}\n"
    
    if include_summary:
        summary = getattr(entry, 'summary', None) or getattr(entry, 'description', None)
        if summary:
            # Clean HTML from summary
            if FEEDPARSER_AVAILABLE:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(summary, 'html.parser')
                    summary = soup.get_text(strip=True)
                except:
                    pass
            result += f"Summary: {summary[:500]}\n"  # Limit summary length
    
    if include_content:
        content = None
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif hasattr(entry, 'description'):
            content = entry.description
        
        if content:
            # Clean HTML from content
            if FEEDPARSER_AVAILABLE:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    content = soup.get_text(strip=True)
                except:
                    pass
            result += f"Content: {content[:1000]}\n"  # Limit content length
    
    # Add author if available
    author = getattr(entry, 'author', None)
    if author:
        result += f"Author: {author}\n"
    
    return result


def create_rss_feed_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create RSS feed reader tool function."""
    limit = config.get("rss_feed_limit", 10)
    timeout = config.get("rss_feed_timeout", 30)
    include_content = config.get("rss_feed_include_content", True)
    include_summary = config.get("rss_feed_include_summary", True)
    
    async def rss_feed_func_async(feed_url: str) -> str:
        """Fetch and parse RSS/Atom feed."""
        if not FEEDPARSER_AVAILABLE:
            return "Error: feedparser package not installed. Install with: pip install feedparser"
        
        try:
            # Validate URL
            parsed = urlparse(feed_url)
            if not parsed.scheme or not parsed.netloc:
                return f"Error: Invalid URL format: {feed_url}"
            
            # Fetch feed
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                feed_content = response.text
            
            # Parse feed
            import feedparser
            feed = feedparser.parse(feed_content)
            
            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                # Try to continue anyway, some feeds have minor issues
                pass
            
            # Get feed metadata
            feed_title = feed.feed.get('title', 'Untitled Feed')
            feed_link = feed.feed.get('link', feed_url)
            feed_description = feed.feed.get('description', '')
            
            # Build result
            result = f"Feed: {feed_title}\n"
            result += f"Feed URL: {feed_link}\n"
            if feed_description:
                result += f"Description: {feed_description}\n"
            result += f"Items: {len(feed.entries)}\n"
            result += "\n" + "="*80 + "\n\n"
            
            # Process entries
            entries = feed.entries[:limit]
            if not entries:
                return result + "No items found in feed."
            
            for i, entry in enumerate(entries, 1):
                result += f"--- Item {i} ---\n"
                result += _format_feed_item(entry, include_content, include_summary)
                result += "\n"
            
            if len(feed.entries) > limit:
                result += f"\n... ({len(feed.entries) - limit} more items not shown)\n"
            
            return result
                
        except httpx.TimeoutException:
            return f"Error: Request timed out after {timeout} seconds"
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP {e.response.status_code} - {e.response.reason_phrase}"
        except httpx.RequestError as e:
            return f"Error: Request failed - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Wrapper to make async function work with LangChain Tool
    def rss_feed_func(feed_url: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(rss_feed_func_async(feed_url))
        except RuntimeError:
            return asyncio.run(rss_feed_func_async(feed_url))
    
    return rss_feed_func

