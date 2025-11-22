"""
Web scraping tool implementation.
Extracts clean text content from web pages.
"""

import httpx
import asyncio
from typing import Dict, Any, Callable
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import lxml
    PARSER = 'lxml'
except ImportError:
    PARSER = 'html.parser'


def get_web_scraping_schema() -> Dict[str, Any]:
    """Get schema fields for web scraping tool."""
    return {
        "web_scraping_timeout": {
            "type": "integer",
            "default": 30,
            "minimum": 5,
            "maximum": 120,
            "title": "Timeout (seconds)",
            "description": "Maximum time to wait for page to load",
        },
        "web_scraping_headers": {
            "type": "string",
            "default": "{}",
            "title": "Custom Headers (JSON)",
            "description": "Optional custom HTTP headers as JSON string (e.g., {\"User-Agent\": \"Mozilla/5.0\"})",
        },
        "web_scraping_extract_links": {
            "type": "boolean",
            "default": False,
            "title": "Extract Links",
            "description": "Include links found on the page",
        },
        "web_scraping_remove_scripts": {
            "type": "boolean",
            "default": True,
            "title": "Remove Scripts",
            "description": "Remove script and style tags from content",
        },
    }


def _clean_text(html_content: str, remove_scripts: bool = True) -> str:
    """Extract clean text from HTML content."""
    if not BEAUTIFULSOUP_AVAILABLE:
        # Fallback: basic text extraction without BeautifulSoup
        import re
        # Remove script and style tags
        if remove_scripts:
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    try:
        soup = BeautifulSoup(html_content, PARSER)
        
        # Remove script and style elements
        if remove_scripts:
            for script in soup(["script", "style", "meta", "link", "noscript"]):
                script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up multiple whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return f"Error parsing HTML: {str(e)}"


def _extract_links(html_content: str, base_url: str) -> list:
    """Extract links from HTML content."""
    if not BEAUTIFULSOUP_AVAILABLE:
        return []
    
    try:
        soup = BeautifulSoup(html_content, PARSER)
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            
            # Resolve relative URLs
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            elif not href.startswith('http'):
                continue
            
            if text:
                links.append(f"{text}: {href}")
        
        return links
    except Exception:
        return []


def create_web_scraping_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create web scraping tool function."""
    timeout = config.get("web_scraping_timeout", 30)
    headers_str = config.get("web_scraping_headers", "{}")
    extract_links = config.get("web_scraping_extract_links", False)
    remove_scripts = config.get("web_scraping_remove_scripts", True)
    
    # Parse headers
    import json
    try:
        custom_headers = json.loads(headers_str) if headers_str else {}
    except json.JSONDecodeError:
        custom_headers = {}
    
    # Default headers
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    headers = {**default_headers, **custom_headers}
    
    async def web_scraping_func_async(url: str) -> str:
        """Scrape content from a web page."""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return f"Error: Invalid URL format: {url}"
            
            # Make request
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Get content
                html_content = response.text
                
                # Extract text
                text = _clean_text(html_content, remove_scripts)
                
                if not text:
                    return "Error: No text content found on the page"
                
                # Extract links if requested
                result = text
                if extract_links:
                    links = _extract_links(html_content, url)
                    if links:
                        result += "\n\n--- Links Found ---\n" + "\n".join(links[:50])  # Limit to 50 links
                
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
    def web_scraping_func(url: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(web_scraping_func_async(url))
        except RuntimeError:
            return asyncio.run(web_scraping_func_async(url))
    
    return web_scraping_func

