
# Workflow Deployment & Usage Guide

## 🎯 Current State: How Deployment Works Now

### What Happens When You Click "Deploy"

1. **Workflow is Validated**
   - Checks that all nodes are properly connected
   - Validates node configurations
   - Ensures required fields are set

2. **Workflow is Saved Locally**
   - Stored as JSON file in `backend/data/workflows/`
   - Marked with `is_deployed: true`
   - Timestamp recorded (`deployed_at`)

3. **API Endpoint is Created**
   - Endpoint: `POST /api/v1/workflows/{workflow_id}/query`
   - Workflow becomes queryable via this endpoint

### Where is it "Deployed"?

**Currently: It's deployed to YOUR local Nodeflow server**

- The workflow is saved on the same server where you're running Nodeflow
- It's accessible via the API endpoint on that server
- It's NOT deployed to external services, cloud, or websites yet
- Think of it as "saved and ready to use" in your system

---

## 🔄 How to Use a Deployed Workflow

### Option 1: Via API Endpoint (Current Method)

**Endpoint:**
```
POST http://localhost:8000/api/v1/workflows/{workflow_id}/query
```

**Request Body:**
```json
{
  "input": {
    "query": "What is the main topic?",
    "file_id": "abc-123-def",
    // ... other input data your workflow needs
  }
}
```

**Response:**
```json
{
  "execution_id": "exec-123",
  "status": "completed",
  "results": {
    "chat": {
      "response": "The main topic is...",
      "cost": 0.0023
    }
  },
  "total_cost": 0.0023,
  "duration_ms": 1250
}
```

**Example using cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/my-rag-workflow/query \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "Summarize the document"
    }
  }'
```

### Option 2: Via Frontend UI (Not Yet Implemented)

Currently, there's **no UI for querying deployed workflows** in the frontend. This would need to be built.

**Potential UI Features:**
- Query interface in the Dashboard
- Chat interface for deployed workflows
- API key management
- Usage analytics

---

## 🌐 Deploying to External Environments

### Current Limitations

Right now, deployment is **local only**. To deploy to external environments, you would need:

### Option A: Self-Hosted Deployment

**How it would work:**
1. Deploy Nodeflow backend to your own server (AWS, GCP, Azure, etc.)
2. Expose the API endpoint publicly
3. Use API keys for authentication
4. External apps call your Nodeflow API

**Architecture:**
```
Your Website/App
    ↓ (HTTP Request)
Your Nodeflow Server (hosted on AWS/GCP/etc.)
    ↓ (Executes Workflow)
Returns Results
```

**Requirements:**
- Server hosting (AWS EC2, Google Cloud Run, etc.)
- Domain name
- SSL certificate (HTTPS)
- API authentication
- Rate limiting
- Monitoring

### Option B: Embeddable Widget (Future)

**How it would work:**
1. Generate embed code for your workflow
2. Add to any website via `<script>` tag
3. Widget handles API calls to Nodeflow
4. Results displayed in the widget

**Example:**
```html
<!-- On your website -->
<div id="nodeflow-chat"></div>
<script src="https://nodeflow.ai/embed/workflow-123.js"></script>
```

### Option C: SDK/Client Libraries (Future)

**How it would work:**
1. Install Nodeflow SDK in your app
2. Initialize with API key
3. Call workflows programmatically

**Example (JavaScript):**
```javascript
import { NodeflowClient } from '@nodeflow/sdk';

const client = new NodeflowClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.nodeflow.ai'
});

const result = await client.queryWorkflow('workflow-123', {
  query: 'What is this about?',
  file_id: 'abc-123'
});
```

### Option D: API Gateway / Proxy (Future)

**How it would work:**
1. Nodeflow provides hosted API service
2. You deploy workflows to Nodeflow cloud
3. External apps call Nodeflow API
4. Nodeflow handles scaling, monitoring, etc.

**Architecture:**
```
Your Website/App
    ↓ (HTTP Request with API Key)
Nodeflow Cloud API
    ↓ (Executes Your Workflow)
Returns Results
```

---

## 📋 What Gets Deployed vs. What Doesn't

### ✅ What IS Deployed (Stored):

- **Workflow Structure**
  - Node types and connections
  - Node configurations (models, parameters)
  - Workflow metadata (name, description)

- **Configuration**
  - Model settings (e.g., `gemini-2.5-flash`)
  - Temperature, max tokens
  - Chunk sizes, embedding models
  - Vector store settings

### ❌ What is NOT Deployed (Provided at Query Time):

- **Input Data**
  - User queries
  - File IDs (files must be uploaded separately)
  - Context data
  - Session information

- **Runtime Data**
  - Execution results
  - Temporary files
  - Cache data

---

## 🔐 Security & Authentication (Future Needs)

### Current State: No Authentication

Right now, anyone with the workflow ID can query it if they know your server URL.

### What's Needed for Production:

1. **API Keys**
   - Generate keys per workflow or per user
   - Store keys securely
   - Validate on each request

2. **Rate Limiting**
   - Limit queries per API key
   - Prevent abuse
   - Track usage

3. **CORS Configuration**
   - Allow specific domains
   - Block unauthorized origins

4. **Input Validation**
   - Sanitize user inputs
   - Validate file IDs
   - Check data types

---

## 🚀 Deployment Scenarios

### Scenario 1: Internal Tool

**Use Case:** Your team uses Nodeflow internally

**Setup:**
- Deploy Nodeflow on internal server
- Access via internal network
- No external access needed
- ✅ Works with current implementation

### Scenario 2: Public API Service

**Use Case:** You want to offer your workflow as a service

**Setup:**
- Deploy Nodeflow on cloud server
- Expose API endpoint publicly
- Add API key authentication
- ⚠️ Needs authentication layer

### Scenario 3: Website Integration

**Use Case:** Add AI features to your website

**Setup:**
- Deploy Nodeflow backend
- Create frontend widget/component
- Embed in your website
- ⚠️ Needs embeddable widget

### Scenario 4: Mobile App

**Use Case:** Mobile app uses your workflow

**Setup:**
- Deploy Nodeflow backend
- Mobile app calls API
- Handle authentication
- ⚠️ Needs SDK/client library

---

## 📊 Monitoring & Analytics

### Current State: Basic Metrics

- Execution history stored
- Cost tracking per execution
- Basic metrics in Dashboard

### What's Available:

- Total queries
- Success rate
- Average response time
- Total cost
- Cost per query

### What's Missing for Production:

- Real-time monitoring
- Error alerting
- Usage dashboards
- Performance optimization
- Cost budgets/alerts

---

## 🎯 Recommended Next Steps

### For Immediate Use (Current System):

1. **Use API Endpoint Directly**
   - Call `/workflows/{id}/query` from your apps
   - Handle authentication at your app level
   - Works for internal tools

2. **Build Simple Query UI**
   - Add query interface to Dashboard
   - Test deployed workflows easily
   - Useful for demos

### For External Deployment (Future):

1. **Add API Authentication**
   - Generate API keys
   - Validate on requests
   - Track usage per key

2. **Create Embeddable Widget**
   - Generate embed codes
   - Handle CORS
   - Style customization

3. **Build SDK/Client Libraries**
   - JavaScript/TypeScript SDK
   - Python SDK
   - Easy integration

4. **Hosted Service Option**
   - Nodeflow Cloud
   - Managed infrastructure
   - Auto-scaling

---

## 💡 Summary

**Current State:**
- ✅ Workflows can be deployed (saved as ready-to-use)
- ✅ Queryable via API endpoint
- ✅ Works for internal/local use
- ❌ No external deployment yet
- ❌ No authentication
- ❌ No embeddable widgets
- ❌ No SDK

**To Deploy Externally:**
- Deploy Nodeflow backend to cloud server
- Add API authentication
- Expose endpoint publicly
- Build client integration (widget/SDK)

**Best Use Cases Right Now:**
- Internal tools
- Testing/demos
- Development workflows
- API-first integrations

