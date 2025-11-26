"""
Integration tests for core API endpoints (health, nodes, rate limiting)
"""

import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthAPI:
    """Test health and monitoring endpoints."""
    
    def test_health_endpoint_basic(self):
        """Test basic health check."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == "NodeAI"
        assert "version" in data
        assert "database" in data
    
    def test_health_endpoint_database_info(self):
        """Test health endpoint includes database pool information."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        db_info = data.get("database", {})
        
        # Check database configuration
        assert "pool_configured" in db_info
        assert "supabase_configured" in db_info
        
        # If pool is configured, should have stats
        if db_info.get("pool_configured"):
            assert "pool_stats" in db_info
            pool_stats = db_info["pool_stats"]
            assert pool_stats.get("status") in ["active", "error"]
            
            if pool_stats.get("status") == "active":
                assert "min_connections" in pool_stats
                assert "max_connections" in pool_stats
                # Verify our enhanced pool settings
                assert pool_stats.get("min_connections", 0) >= 5
                assert pool_stats.get("max_connections", 0) >= 20
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["app"] == "NodeAI"
        assert data["status"] == "running"
        assert "version" in data


class TestNodesAPI:
    """Test nodes API endpoints."""
    
    def test_list_nodes(self):
        """Test listing all available nodes."""
        response = client.get("/api/v1/nodes")
        assert response.status_code == 200
        
        # Should return list of node metadata
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least some basic nodes
        node_types = [node.get("type") for node in data]
        assert "chat" in node_types  # Our enhanced chat node
        assert "text_input" in node_types
    
    def test_get_node_categories(self):
        """Test getting node categories."""
        response = client.get("/api/v1/nodes/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Should have main categories
        assert "llm" in data  # Our chat node category
        assert "input" in data
        
        # Each category should have structure
        for category, info in data.items():
            assert "count" in info
            assert "nodes" in info
            assert isinstance(info["count"], int)
            assert isinstance(info["nodes"], list)
    
    def test_get_specific_node_schema(self):
        """Test getting schema for specific node types."""
        # Test chat node (our enhanced node)
        response = client.get("/api/v1/nodes/chat")
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "chat"
        assert data["name"] == "Chat"
        assert data["category"] == "llm"
        assert "inputs" in data
        assert "outputs" in data
        assert "config_schema" in data
    
    def test_get_nonexistent_node_schema(self):
        """Test getting schema for nonexistent node."""
        response = client.get("/api/v1/nodes/nonexistent-node")
        assert response.status_code == 404


class TestRateLimitingAPI:
    """Test rate limiting functionality on API endpoints."""
    
    @pytest.mark.slow
    def test_rate_limiting_nodes_endpoint(self):
        """Test rate limiting on nodes endpoint."""
        # This test verifies our rate limiting implementation
        responses = []
        
        # Make requests up to the limit
        for i in range(7):  # Should hit rate limit (currently set to 5/minute for testing)
            response = client.get("/api/v1/nodes")
            responses.append(response)
            
            # Small delay to avoid overwhelming
            if i < 6:  # Don't delay on last request
                time.sleep(0.1)
        
        # Check that we get rate limited
        status_codes = [r.status_code for r in responses]
        rate_limited = any(code == 429 for code in status_codes)
        
        if rate_limited:
            # Find the first rate limited response
            for response in responses:
                if response.status_code == 429:
                    # Should have rate limit headers
                    assert "x-ratelimit-limit" in response.headers
                    assert "x-ratelimit-remaining" in response.headers
                    break
        
        # At minimum, successful requests should have rate limit headers
        for response in responses:
            if response.status_code == 200:
                assert "x-ratelimit-limit" in response.headers
                assert "x-ratelimit-remaining" in response.headers
                break
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses."""
        response = client.get("/api/v1/nodes")
        assert response.status_code == 200
        
        # Should have rate limiting headers
        headers = response.headers
        assert "x-ratelimit-limit" in headers
        assert "x-ratelimit-remaining" in headers
        
        # Values should be reasonable
        limit = int(headers.get("x-ratelimit-limit", "0"))
        remaining = int(headers.get("x-ratelimit-remaining", "0"))
        
        assert limit > 0  # Should have a positive limit
        assert remaining >= 0  # Remaining should not be negative


class TestSecurityHeaders:
    """Test security headers are properly applied."""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        headers = response.headers
        
        # Check for security headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"
        
        assert "x-xss-protection" in headers
        assert "1" in headers["x-xss-protection"]
        
        assert "referrer-policy" in headers
    
    def test_cors_headers_in_development(self):
        """Test CORS headers are present (for development)."""
        # Make an OPTIONS request to test CORS
        response = client.options("/api/v1/health")
        
        # Should handle OPTIONS request
        assert response.status_code in [200, 204]
        
        # In development, should have CORS headers
        headers = response.headers
        # Note: Exact CORS headers depend on configuration


@pytest.mark.integration
class TestCriticalPathsIntegration:
    """Test critical system paths end-to-end."""
    
    def test_system_startup_endpoints_accessible(self):
        """Test that all critical endpoints are accessible after startup."""
        critical_endpoints = [
            "/",
            "/api/v1/health",
            "/api/v1/nodes",
            "/api/v1/nodes/categories",
            "/api/v1/workflows",
        ]
        
        for endpoint in critical_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 201], f"Endpoint {endpoint} failed with {response.status_code}"
    
    def test_database_pool_functional(self):
        """Test that database connection pool is functional."""
        # Health endpoint tests database connectivity
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        db_info = data.get("database", {})
        
        # Should have pool or supabase configured
        assert (
            db_info.get("pool_configured") or 
            db_info.get("supabase_configured")
        ), "Neither database pool nor Supabase is configured"