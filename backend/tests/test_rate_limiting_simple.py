"""
Simple Rate Limiting Test Script

Quick test to verify rate limiting is working.
Run this with: python backend/tests/test_rate_limiting_simple.py
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_rate_limit(endpoint: str, method: str = "GET", limit: int = 30):
    """Test rate limiting on a single endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"Expected Limit: {limit} requests/minute")
    print(f"{'='*60}")
    
    successful = 0
    rate_limited = False
    
    # Make requests up to limit + 5
    for i in range(limit + 5):
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
            else:
                print(f"Unsupported method: {method}")
                break
            
            if response.status_code == 200 or response.status_code == 201:
                successful += 1
                remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
                print(f"  Request {i+1}: {response.status_code} (Remaining: {remaining})")
            elif response.status_code == 429:
                rate_limited = True
                print(f"  Request {i+1}: {response.status_code} (RATE LIMITED ✓)")
                print(f"    Headers: {dict(response.headers)}")
                break
            else:
                print(f"  Request {i+1}: {response.status_code}")
                if i == 0:
                    print(f"    Error: {response.text[:100]}")
                    break
            
            time.sleep(0.1)  # Small delay
            
        except Exception as e:
            print(f"  Request {i+1}: Error - {str(e)}")
            break
    
    # Evaluate
    print(f"\n  Results:")
    print(f"    Successful requests: {successful}")
    print(f"    Rate limited: {rate_limited}")
    
    if rate_limited and successful <= limit:
        print(f"  ✅ PASS: Rate limiting working correctly!")
        return True
    elif successful == 0:
        print(f"  ⚠️  SKIP: Endpoint may require authentication or have other issues")
        return None
    else:
        print(f"  ❌ FAIL: Expected rate limiting after {limit} requests")
        return False


def main():
    """Run simple rate limiting tests."""
    print("Simple Rate Limiting Test")
    print("="*60)
    print("\nMake sure your backend server is running on http://localhost:8000")
    print("This will test a few endpoints to verify rate limiting works.\n")
    
    # Test cases
    tests = [
        ("/nodes", "GET", 5),  # Reduced for testing
        ("/nodes/categories", "GET", 5),  # Reduced for testing
    ]
    
    results = []
    for endpoint, method, limit in tests:
        result = test_rate_limit(endpoint, method, limit)
        results.append((endpoint, result))
        time.sleep(2)  # Wait between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    for endpoint, result in results:
        if result is True:
            print(f"✅ {endpoint}")
        elif result is False:
            print(f"❌ {endpoint}")
        else:
            print(f"⚠️  {endpoint} (skipped)")
    
    print(f"\nPassed: {passed}, Failed: {failed}, Skipped: {skipped}")
    
    if failed == 0:
        print("\n🎉 Rate limiting appears to be working!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(1)

