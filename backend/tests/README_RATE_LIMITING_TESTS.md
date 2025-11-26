# Rate Limiting Test Scripts

This directory contains test scripts to verify that rate limiting is working correctly on all API endpoints.

## Quick Start

### Option 1: Simple Test (Recommended for Quick Check)

```bash
# Make sure backend is running
python backend/tests/test_rate_limiting_simple.py
```

This will:
- Test a few key endpoints
- Show if rate limiting is working
- Display rate limit headers

### Option 2: Comprehensive Test

```bash
# Make sure backend is running
python backend/tests/test_rate_limiting.py
```

This will:
- Test multiple endpoints with different rate limits
- Show detailed results for each test
- Provide a summary report

## What Gets Tested

The tests verify:
1. ✅ Requests within the limit work (status 200)
2. ✅ Requests exceeding the limit return 429 (Too Many Requests)
3. ✅ Rate limit headers are present:
   - `X-RateLimit-Limit`: Maximum requests allowed
   - `X-RateLimit-Remaining`: Remaining requests
   - `X-RateLimit-Reset`: Time when limit resets

## Expected Behavior

For an endpoint with a 30/minute limit:
- Requests 1-30: Should return 200 OK
- Request 31+: Should return 429 Too Many Requests

## Troubleshooting

### "Connection refused" error
- Make sure your backend server is running on `http://localhost:8000`
- Check that the server started without errors

### "401 Unauthorized" errors
- Some endpoints require authentication
- Set `TEST_TOKEN` in the test script if needed
- Or test endpoints that don't require auth (like `/nodes`)

### Rate limiting not working
- Check that `@limiter.limit()` decorators are present
- Verify `request: Request` parameter is in function signature
- Check backend logs for any errors

## Test Results

After running tests, you should see:
- ✅ PASS: Rate limiting working correctly
- ❌ FAIL: Rate limiting not working (needs investigation)
- ⚠️ SKIP: Endpoint has other issues (auth, etc.)

## Manual Testing

You can also test manually with curl:

```bash
# Test GET endpoint (30/minute limit)
for i in {1..35}; do
  echo "Request $i:"
  curl -X GET http://localhost:8000/api/v1/nodes \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -w "\nStatus: %{http_code}\n" \
    -s -o /dev/null
  sleep 0.1
done
```

Request 31+ should return status 429.

