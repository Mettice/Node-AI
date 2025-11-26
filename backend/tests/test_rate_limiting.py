"""
Rate Limiting Test Script

This script tests that rate limiting is working correctly on all endpoints.
Run this after starting the backend server.

Usage:
    python -m pytest backend/tests/test_rate_limiting.py -v
    OR
    python backend/tests/test_rate_limiting.py
"""

import asyncio
import time
from typing import Dict, List, Optional
import httpx
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000/api/v1"
TEST_TOKEN = None  # Set this if you need authentication


class RateLimitTester:
    """Test rate limiting on API endpoints."""
    
    def __init__(self, base_url: str = BASE_URL, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        expected_limit: int,
        request_body: Optional[Dict] = None,
        description: str = ""
    ) -> Dict:
        """
        Test rate limiting on a single endpoint.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            expected_limit: Expected rate limit (requests per minute)
            request_body: Optional request body for POST/PUT requests
            description: Description of the test
        
        Returns:
            Test results dictionary
        """
        url = f"{self.base_url}{endpoint}"
        results = {
            "endpoint": endpoint,
            "method": method,
            "expected_limit": expected_limit,
            "description": description,
            "passed": False,
            "requests_made": 0,
            "successful_requests": 0,
            "rate_limited_requests": 0,
            "errors": [],
            "rate_limit_headers": {}
        }
        
        print(f"\n{'='*60}")
        print(f"Testing: {method} {endpoint}")
        print(f"Expected Limit: {expected_limit}/minute")
        if description:
            print(f"Description: {description}")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Make requests up to limit + 5 extra
            requests_to_make = expected_limit + 5
            rate_limited = False
            
            for i in range(requests_to_make):
                try:
                    if method == "GET":
                        response = await client.get(url, headers=self.headers)
                    elif method == "POST":
                        response = await client.post(
                            url,
                            headers=self.headers,
                            json=request_body or {}
                        )
                    elif method == "PUT":
                        response = await client.put(
                            url,
                            headers=self.headers,
                            json=request_body or {}
                        )
                    elif method == "DELETE":
                        response = await client.delete(url, headers=self.headers)
                    else:
                        results["errors"].append(f"Unsupported method: {method}")
                        break
                    
                    results["requests_made"] += 1
                    
                    # Check for rate limit headers
                    if "X-RateLimit-Limit" in response.headers:
                        results["rate_limit_headers"] = {
                            "limit": response.headers.get("X-RateLimit-Limit"),
                            "remaining": response.headers.get("X-RateLimit-Remaining"),
                            "reset": response.headers.get("X-RateLimit-Reset"),
                        }
                    
                    # Check status code
                    if response.status_code == 200 or response.status_code == 201:
                        results["successful_requests"] += 1
                        if i < expected_limit:
                            print(f"  ✓ Request {i+1}: {response.status_code} (OK)")
                        else:
                            print(f"  ⚠ Request {i+1}: {response.status_code} (Should be rate limited!)")
                    elif response.status_code == 429:
                        results["rate_limited_requests"] += 1
                        rate_limited = True
                        print(f"  ✗ Request {i+1}: {response.status_code} (Rate Limited)")
                        if "X-RateLimit-Remaining" in response.headers:
                            print(f"    Remaining: {response.headers['X-RateLimit-Remaining']}")
                        break
                    else:
                        # Other error (401, 404, etc.)
                        print(f"  ⚠ Request {i+1}: {response.status_code}")
                        if i == 0:
                            # If first request fails, endpoint might need auth or have other issues
                            results["errors"].append(
                                f"First request failed with {response.status_code}: {response.text[:100]}"
                            )
                            break
                    
                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    results["errors"].append(f"Request {i+1} failed: {str(e)}")
                    print(f"  ✗ Request {i+1}: Error - {str(e)}")
                    break
            
            # Evaluate results
            if results["errors"] and results["successful_requests"] == 0:
                results["passed"] = False
                print(f"\n  ❌ TEST FAILED: {results['errors'][0]}")
            elif results["successful_requests"] >= expected_limit and not rate_limited:
                results["passed"] = False
                print(f"\n  ❌ TEST FAILED: Made {results['successful_requests']} requests without rate limiting!")
                print(f"     Expected to be rate limited after {expected_limit} requests")
            elif rate_limited and results["successful_requests"] <= expected_limit:
                results["passed"] = True
                print(f"\n  ✅ TEST PASSED: Rate limiting working correctly!")
                print(f"     Made {results['successful_requests']} successful requests")
                print(f"     Rate limited at request {results['requests_made']}")
            else:
                results["passed"] = False
                print(f"\n  ⚠ TEST UNCLEAR: {results['successful_requests']} successful, rate limited: {rate_limited}")
        
        return results
    
    async def run_all_tests(self) -> Dict:
        """Run tests on multiple endpoints."""
        print("\n" + "="*60)
        print("RATE LIMITING TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Testing endpoints with various rate limits...")
        
        test_cases = [
            # GET endpoints (30/minute)
            {
                "method": "GET",
                "endpoint": "/nodes",
                "expected_limit": 30,
                "description": "List nodes endpoint"
            },
            {
                "method": "GET",
                "endpoint": "/nodes/categories",
                "expected_limit": 30,
                "description": "Get node categories"
            },
            # POST endpoints (20/minute)
            {
                "method": "POST",
                "endpoint": "/workflows",
                "expected_limit": 20,
                "description": "Create workflow",
                "request_body": {
                    "name": "Test Workflow",
                    "description": "Test",
                    "nodes": [],
                    "edges": []
                }
            },
            # DELETE endpoints (10/minute)
            # Note: We'll skip DELETE tests to avoid deleting actual data
            # {
            #     "method": "DELETE",
            #     "endpoint": "/workflows/test-id",
            #     "expected_limit": 10,
            #     "description": "Delete workflow"
            # },
        ]
        
        results = []
        for test_case in test_cases:
            result = await self.test_endpoint(**test_case)
            results.append(result)
            # Wait a bit between tests to avoid interference
            await asyncio.sleep(2)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} - {result['method']} {result['endpoint']}")
            if not result["passed"] and result["errors"]:
                print(f"      Error: {result['errors'][0]}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "results": results
        }


async def main():
    """Main test function."""
    print("Rate Limiting Test Script")
    print("="*60)
    print("\nMake sure your backend server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel, or wait 5 seconds to start...")
    
    try:
        await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        return
    
    tester = RateLimitTester(base_url=BASE_URL, token=TEST_TOKEN)
    summary = await tester.run_all_tests()
    
    if summary["passed"] == summary["total"]:
        print("\n🎉 All rate limiting tests passed!")
        return 0
    else:
        print(f"\n⚠️  {summary['failed']} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

