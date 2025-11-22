"""
NodAI Python Client

Simple client for querying NodAI workflows.
"""

import requests
from typing import Dict, Any, Optional


class NodAIError(Exception):
    """Base exception for NodAI SDK errors."""
    pass


class NodAIClient:
    """
    Client for interacting with NodAI API.
    
    Example:
        ```python
        from nodai import NodAIClient
        
        client = NodAIClient(
            api_key="nk_...",
            base_url="https://api.nodai.io"
        )
        
        result = client.query_workflow(
            workflow_id="workflow-123",
            input={"query": "What is AI?"}
        )
        print(result["results"])
        ```
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
    ):
        """
        Initialize the NodAI client.
        
        Args:
            api_key: Your NodAI API key
            base_url: Base URL of the NodAI API (default: localhost)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        })
    
    def query_workflow(
        self,
        workflow_id: str,
        input: Dict[str, Any],
        timeout: Optional[float] = 60.0,
    ) -> Dict[str, Any]:
        """
        Query a deployed workflow.
        
        Args:
            workflow_id: The ID of the deployed workflow
            input: Input data for the workflow (e.g., {"query": "..."})
            timeout: Request timeout in seconds (default: 60)
            
        Returns:
            Dictionary containing execution results, status, costs, etc.
            
        Raises:
            NodAIError: If the request fails
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/query"
        
        try:
            response = self.session.post(
                url,
                json={"input": input},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = "Request failed"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", {}).get("message", str(e))
            except:
                error_msg = str(e)
            raise NodAIError(f"HTTP {e.response.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise NodAIError(f"Request failed: {str(e)}")
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the API is healthy.
        
        Returns:
            Dictionary with status information
        """
        url = f"{self.base_url}/api/v1/health"
        try:
            response = self.session.get(url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise NodAIError(f"Health check failed: {str(e)}")

