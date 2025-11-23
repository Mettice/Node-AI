"""
Enhanced Reddit Node for NodeAI.

This node provides a dedicated interface for Reddit operations with OAuth support.
Supports fetching posts, comments, searching Reddit, and monitoring subreddits.
"""

import base64
import json
from typing import Any, Dict, List, Optional

import httpx

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.oauth import OAuthManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RedditNode(BaseNode):
    """
    Enhanced Reddit Node.
    
    Provides a dedicated interface for Reddit operations with OAuth support.
    """

    node_type = "reddit"
    name = "Reddit"
    description = "Fetch posts, comments, search Reddit, and monitor subreddits using OAuth"
    category = "integration"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Reddit operation.
        
        Supports: fetch_posts, fetch_comments, search, get_post
        """
        node_id = config.get("_node_id", "reddit")
        operation = config.get("reddit_operation", "fetch_posts")
        
        # Get OAuth token or API key
        token_id = config.get("reddit_token_id")
        api_key = config.get("reddit_api_key")  # Alternative: API key for read-only access
        
        access_token = None
        auth_header = None
        
        if token_id:
            token_data = OAuthManager.get_token(token_id)
            if not token_data:
                raise ValueError("Reddit OAuth token not found. Please reconnect your Reddit account.")
            
            if not OAuthManager.is_token_valid(token_data):
                raise ValueError("Reddit OAuth token has expired. Please reconnect your Reddit account.")
            
            access_token = token_data["access_token"]
            auth_header = f"Bearer {access_token}"
        elif api_key:
            # For API key authentication (read-only, simpler setup)
            auth_header = f"Bearer {api_key}"
        else:
            raise ValueError("Reddit OAuth token ID or API key is required. Please connect your Reddit account or provide an API key.")
        
        await self.stream_progress(node_id, 0.1, f"Executing Reddit {operation}...")
        
        # Route to appropriate operation
        if operation == "fetch_posts":
            return await self._fetch_posts(auth_header, inputs, config, node_id)
        elif operation == "fetch_comments":
            return await self._fetch_comments(auth_header, inputs, config, node_id)
        elif operation == "search":
            return await self._search(auth_header, inputs, config, node_id)
        elif operation == "get_post":
            return await self._get_post(auth_header, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported Reddit operation: {operation}")

    async def _fetch_posts(
        self,
        auth_header: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Fetch posts from a subreddit."""
        subreddit = config.get("reddit_subreddit") or inputs.get("subreddit")
        sort = config.get("reddit_sort", "hot")  # hot, new, top, rising
        time_filter = config.get("reddit_time_filter", "day")  # hour, day, week, month, year, all
        limit = config.get("reddit_limit", 25)
        
        if not subreddit:
            raise ValueError("Subreddit name is required")
        
        await self.stream_progress(node_id, 0.3, f"Fetching {sort} posts from r/{subreddit}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://oauth.reddit.com/r/{subreddit}/{sort}.json"
            params = {
                "limit": min(limit, 100),  # Reddit API max is 100
            }
            if sort == "top":
                params["t"] = time_filter
            
            response = await client.get(
                url,
                headers={
                    "Authorization": auth_header,
                    "User-Agent": "NodAI/1.0",
                },
                params=params,
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Reddit API error: {error_message}")
            
            data = response.json()
            posts = [child["data"] for child in data.get("data", {}).get("children", [])]
            
            await self.stream_progress(node_id, 1.0, f"Fetched {len(posts)} posts")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "fetch_posts",
                    "subreddit": subreddit,
                    "count": len(posts),
                    "posts": posts,
                },
                "posts": posts,
                "post_list": posts,
                "subreddit": subreddit,
            }

    async def _fetch_comments(
        self,
        auth_header: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Fetch comments from a post."""
        post_id = config.get("reddit_post_id") or inputs.get("post_id")
        sort = config.get("reddit_comment_sort", "top")  # top, best, new, controversial, old
        limit = config.get("reddit_limit", 25)
        
        if not post_id:
            raise ValueError("Post ID is required")
        
        # Remove 't3_' prefix if present
        if post_id.startswith("t3_"):
            post_id = post_id[3:]
        
        await self.stream_progress(node_id, 0.3, f"Fetching comments from post {post_id}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://oauth.reddit.com/comments/{post_id}.json"
            params = {
                "sort": sort,
                "limit": min(limit, 100),
            }
            
            response = await client.get(
                url,
                headers={
                    "Authorization": auth_header,
                    "User-Agent": "NodAI/1.0",
                },
                params=params,
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Reddit API error: {error_message}")
            
            data = response.json()
            # First item is the post, second is comments
            post_data = data[0]["data"]["children"][0]["data"] if data[0]["data"]["children"] else {}
            comments = []
            
            if len(data) > 1:
                # Extract comments recursively
                def extract_comments(children):
                    result = []
                    for child in children:
                        if child["kind"] == "t1":  # Comment
                            comment_data = child["data"]
                            result.append(comment_data)
                            # Recursively get replies
                            if comment_data.get("replies") and isinstance(comment_data["replies"], dict):
                                result.extend(extract_comments(comment_data["replies"]["data"]["children"]))
                    return result
                
                comments = extract_comments(data[1]["data"]["children"])
                comments = comments[:limit]
            
            await self.stream_progress(node_id, 1.0, f"Fetched {len(comments)} comments")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "fetch_comments",
                    "post_id": post_id,
                    "count": len(comments),
                    "post": post_data,
                    "comments": comments,
                },
                "comments": comments,
                "post": post_data,
                "post_id": post_id,
            }

    async def _search(
        self,
        auth_header: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Search Reddit."""
        query = config.get("reddit_search_query") or inputs.get("query") or inputs.get("search_query")
        subreddit = config.get("reddit_subreddit") or inputs.get("subreddit")
        sort = config.get("reddit_sort", "relevance")  # relevance, hot, top, new, comments
        time_filter = config.get("reddit_time_filter", "all")
        limit = config.get("reddit_limit", 25)
        
        if not query:
            raise ValueError("Search query is required")
        
        await self.stream_progress(node_id, 0.3, f"Searching Reddit for '{query}'...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if subreddit:
                url = f"https://oauth.reddit.com/r/{subreddit}/search.json"
            else:
                url = "https://oauth.reddit.com/search.json"
            
            params = {
                "q": query,
                "sort": sort,
                "limit": min(limit, 100),
            }
            if sort == "top":
                params["t"] = time_filter
            
            response = await client.get(
                url,
                headers={
                    "Authorization": auth_header,
                    "User-Agent": "NodAI/1.0",
                },
                params=params,
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Reddit API error: {error_message}")
            
            data = response.json()
            posts = [child["data"] for child in data.get("data", {}).get("children", [])]
            
            await self.stream_progress(node_id, 1.0, f"Found {len(posts)} results")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "search",
                    "query": query,
                    "count": len(posts),
                    "posts": posts,
                },
                "posts": posts,
                "search_results": posts,
                "query": query,
            }

    async def _get_post(
        self,
        auth_header: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Get a specific post by ID."""
        post_id = config.get("reddit_post_id") or inputs.get("post_id")
        
        if not post_id:
            raise ValueError("Post ID is required")
        
        # Remove 't3_' prefix if present
        if post_id.startswith("t3_"):
            post_id = post_id[3:]
        
        await self.stream_progress(node_id, 0.3, f"Fetching post {post_id}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://oauth.reddit.com/api/info.json"
            params = {
                "id": f"t3_{post_id}",
            }
            
            response = await client.get(
                url,
                headers={
                    "Authorization": auth_header,
                    "User-Agent": "NodAI/1.0",
                },
                params=params,
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Reddit API error: {error_message}")
            
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            if not posts:
                raise ValueError(f"Post {post_id} not found")
            
            post_data = posts[0]["data"]
            
            await self.stream_progress(node_id, 1.0, "Post fetched successfully")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "get_post",
                    "post_id": post_id,
                    "post": post_data,
                },
                "post": post_data,
                "post_id": post_id,
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Reddit node configuration."""
        return {
            "type": "object",
            "properties": {
                "reddit_operation": {
                    "type": "string",
                    "enum": ["fetch_posts", "fetch_comments", "search", "get_post"],
                    "default": "fetch_posts",
                    "title": "Operation",
                    "description": "Reddit operation to perform",
                },
                "reddit_token_id": {
                    "type": "string",
                    "title": "OAuth Token ID",
                    "description": "OAuth token ID from connected Reddit account (optional if API key provided)",
                },
                "reddit_api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Reddit API key for read-only access (alternative to OAuth)",
                },
                "reddit_subreddit": {
                    "type": "string",
                    "title": "Subreddit",
                    "description": "Subreddit name (without r/ prefix) - required for fetch_posts and optional for search",
                },
                "reddit_post_id": {
                    "type": "string",
                    "title": "Post ID",
                    "description": "Reddit post ID (required for fetch_comments and get_post)",
                },
                "reddit_search_query": {
                    "type": "string",
                    "title": "Search Query",
                    "description": "Search query (required for search operation)",
                },
                "reddit_sort": {
                    "type": "string",
                    "enum": ["hot", "new", "top", "rising", "relevance", "comments"],
                    "default": "hot",
                    "title": "Sort",
                    "description": "Sort order for posts",
                },
                "reddit_comment_sort": {
                    "type": "string",
                    "enum": ["top", "best", "new", "controversial", "old"],
                    "default": "top",
                    "title": "Comment Sort",
                    "description": "Sort order for comments",
                },
                "reddit_time_filter": {
                    "type": "string",
                    "enum": ["hour", "day", "week", "month", "year", "all"],
                    "default": "day",
                    "title": "Time Filter",
                    "description": "Time filter for top posts (only applies when sort is 'top')",
                },
                "reddit_limit": {
                    "type": "integer",
                    "default": 25,
                    "minimum": 1,
                    "maximum": 100,
                    "title": "Limit",
                    "description": "Maximum number of results to return",
                },
            },
            "required": ["reddit_operation"],
        }


# Register the node
NodeRegistry.register(
    RedditNode.node_type,
    RedditNode,
    RedditNode().get_metadata(),
)

