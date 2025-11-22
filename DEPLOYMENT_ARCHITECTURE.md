# Deployment Architecture Explanation

## 🎯 Overview

This document explains how workflow deployment works in NodeAI, addressing:
- What gets stored when you deploy
- How queries are processed
- Cost tracking in deployment
- The difference between development and production execution

---

## 📦 What Happens When You Deploy a Workflow

### Current State (Development/Testing)
Right now, workflows are executed **on-demand** when you click "Run":
1. You build a workflow on the canvas (nodes + connections)
2. Click "Run" → Workflow is sent to backend
3. Backend executes it immediately
4. Results are returned and displayed
5. **Nothing is stored permanently** (except execution history)

### Future State (Deployment)
When you "Deploy" a workflow, here's what happens:

#### 1. **Workflow Definition is Stored**
```
✅ What gets saved:
- Workflow structure (nodes, edges, connections)
- Node configurations (model settings, parameters)
- Workflow metadata (name, description, version)
- Deployment settings (API keys, rate limits)

❌ What does NOT get saved:
- Actual data/content from nodes
- Execution results
- User inputs
- File contents
```

**Example:**
```json
{
  "workflow_id": "rag-pipeline-001",
  "name": "Document Q&A Pipeline",
  "nodes": [
    {
      "id": "file_loader",
      "type": "file_loader",
      "config": {
        "file_id": null  // ← Not stored, provided at query time
      }
    },
    {
      "id": "embed",
      "type": "embed",
      "config": {
        "model": "text-embedding-3-small"  // ← Stored
      }
    }
  ]
}
```

#### 2. **Deployment Creates an API Endpoint**
```
POST /api/v1/workflows/{workflow_id}/query
```

---

## 🔄 How Queries Work After Deployment

### Flow Diagram:
```
User Query
    ↓
API Endpoint (/workflows/{id}/query)
    ↓
Load Workflow Definition (from database)
    ↓
Execute Workflow with Query Data
    ↓
Return Results
```

### Step-by-Step Process:

#### Step 1: User Sends Query
```javascript
POST /api/v1/workflows/rag-pipeline-001/query
{
  "input": {
    "query": "What is NodeAI?",
    "file_id": "abc123.pdf"  // ← Provided at query time
  }
}
```

#### Step 2: Backend Loads Workflow
- Retrieves workflow definition from database
- Validates workflow is still valid
- Checks deployment status (active/paused)

#### Step 3: Execute Workflow with Query Data
- **File Loader Node**: Loads the file using `file_id` from query
- **Chunk Node**: Processes the file content
- **Embed Node**: Creates embeddings (uses stored model config)
- **Vector Store Node**: Stores vectors (if not already stored)
- **Vector Search Node**: Searches using query embedding
- **Chat Node**: Generates answer using retrieved context

#### Step 4: Return Results
```json
{
  "result": "NodeAI is a visual workflow builder...",
  "cost": 0.0025,
  "duration_ms": 1234,
  "metadata": {
    "chunks_retrieved": 3,
    "tokens_used": 150
  }
}
```

---

## 💰 Cost Tracking in Deployment

### How Costs Work:

#### 1. **Costs are Calculated Per Query**
Every time someone queries your deployed workflow:
- Each node that uses paid services (LLM, embeddings) incurs costs
- Costs are tracked in real-time
- Total cost is returned with the response

#### 2. **Cost Display Options**

**Option A: Show Costs in Response (Recommended)**
```json
{
  "result": "...",
  "cost": {
    "total": 0.0025,
    "breakdown": {
      "embedding": 0.0001,
      "llm": 0.0024
    }
  }
}
```

**Option B: Track Costs Separately**
- Store costs in a separate table
- Provide cost analytics dashboard
- Set up cost alerts/budgets

#### 3. **Cost Visibility**

**For Workflow Owners:**
- Dashboard showing total costs per workflow
- Cost per query statistics
- Cost trends over time
- Budget alerts

**For API Users:**
- Optional: Include costs in API response
- Optional: Cost tracking per API key
- Optional: Cost limits per API key

---

## 🏗️ Architecture Comparison

### Development Mode (Current)
```
Canvas → Run Button → Execute Immediately → Show Results
         (No storage)
```

### Production Mode (Deployment)
```
Canvas → Deploy Button → Save Workflow → Create API Endpoint
                                              ↓
                                    Wait for Queries
                                              ↓
                                    Query → Execute → Return
```

---

## 📊 Data Storage Strategy

### What's Stored Permanently:
1. **Workflow Definitions** (Database)
   - Structure, configs, metadata
   - Version history

2. **Vector Stores** (Optional, per workflow)
   - If workflow uses vector storage
   - Can be pre-populated or built on-demand
   - Stored in `data/vectors/{workflow_id}/`

3. **Execution History** (Optional)
   - For analytics and debugging
   - Can be purged after X days

### What's NOT Stored:
1. **User Inputs** (unless explicitly configured)
2. **Query Content** (unless logging enabled)
3. **File Contents** (only file_ids are stored)
4. **Temporary Execution Data**

---

## 🔐 Deployment Modes

### Mode 1: Public API (Default)
- Anyone with workflow ID can query
- Rate limits applied
- Cost tracking per workflow

### Mode 2: API Key Protected
- Requires API key
- Cost tracking per API key
- Usage limits per key

### Mode 3: Private/Internal
- Only accessible from same organization
- No public API endpoint
- Internal use only

---

## 🚀 Next Steps for Implementation

### Phase 1: Basic Deployment (MVP)
1. ✅ Save workflow to database
2. ✅ Create API endpoint for queries
3. ✅ Execute workflow on query
4. ✅ Return results with costs

### Phase 2: Enhanced Features
1. ⏳ API key management
2. ⏳ Rate limiting
3. ⏳ Cost analytics dashboard
4. ⏳ Workflow versioning

### Phase 3: Advanced Features
1. ⏳ Pre-computed vector stores
2. ⏳ Caching layer
3. ⏳ Load balancing
4. ⏳ Auto-scaling

---

## ❓ Common Questions

### Q: Do I need to re-deploy when I change a workflow?
**A:** Yes, changes require re-deployment. Versioning allows you to:
- Keep old version running
- Deploy new version
- Gradually migrate traffic

### Q: What if my workflow uses file uploads?
**A:** Files are uploaded separately. The workflow receives a `file_id`:
- Upload file → Get `file_id`
- Query workflow with `file_id`
- Workflow processes the file

### Q: Can I pre-process data before deployment?
**A:** Yes! You can:
- Pre-embed documents
- Pre-build vector stores
- Cache expensive operations
- Then deploy workflow that uses pre-processed data

### Q: How are costs billed?
**A:** Options:
1. **Per-query billing**: Each query pays for its own costs
2. **Subscription**: Fixed monthly fee + usage
3. **Credit system**: Pre-purchased credits

---

## 📝 Summary

**Deployment = Save Workflow Definition + Create API Endpoint**

- **Stored**: Workflow structure, configurations, metadata
- **Not Stored**: User data, query content, file contents
- **Execution**: Happens on-demand when queries arrive
- **Costs**: Calculated per query, tracked and reported
- **Data**: Files/inputs provided at query time, not stored in workflow

This architecture allows workflows to be:
- ✅ Reusable (same workflow, different inputs)
- ✅ Scalable (handle many concurrent queries)
- ✅ Cost-effective (pay per use)
- ✅ Flexible (update workflow without losing data)

