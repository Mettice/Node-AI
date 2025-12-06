# 🚀 Workflow Deployment & Embed Widgets - Complete Guide

> **📖 Related Guide**: See [WORKFLOW_EXECUTION_VS_DEPLOYMENT.md](./WORKFLOW_EXECUTION_VS_DEPLOYMENT.md) to understand when to deploy vs execute workflows directly.

## 📍 Where Are Workflows Deployed?

### **Short Answer:**
Workflows are deployed to **your Nodeflow backend server** (wherever it's hosted - Railway, AWS, your own server, etc.). They are **NOT** deployed to Supabase or to client devices.

### **Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Nodeflow Backend                     │
│                  (Railway, AWS, GCP, etc.)                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Workflow Storage (JSON files on server)             │  │
│  │  - backend/data/workflows/*.json                     │  │
│  │  - Stored in Supabase (if configured)                │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Deployment Manager                                  │  │
│  │  - Marks workflow as is_deployed = true              │  │
│  │  - Creates deployment version                        │  │
│  │  - Enables persistence for vector stores             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Query Endpoint                                      │  │
│  │  POST /api/v1/workflows/{workflow_id}/query          │  │
│  │  - Accepts input data                                │  │
│  │  - Executes workflow                                 │  │
│  │  - Returns results                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ HTTP Request
                          │ (with API key)
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐              ┌───────────▼──────────┐
│  Your Website  │              │  External App        │
│  (with widget) │              │  (API client)        │
└────────────────┘              └──────────────────────┘
```

---

## 🔄 How Deployment Works

### **Step 1: User Clicks "Deploy"**

When you click the "Deploy" button in the UI:

1. **Frontend** calls: `POST /api/v1/workflows/{workflow_id}/deploy`
2. **Backend** receives the request

### **Step 2: Backend Processing**

The backend does the following:

```python
# 1. Loads the workflow from storage
workflow = _load_workflow(workflow_id)

# 2. Validates the workflow structure
engine._validate_workflow(workflow)

# 3. Configures vector stores for persistence
#    - Enables FAISS persistence
#    - Sets deployment-specific file paths
#    - Creates index_id for consistency

# 4. Marks workflow as deployed
workflow.is_deployed = True
workflow.deployed_at = datetime.now()

# 5. Saves workflow back to storage
_save_workflow(workflow)

# 6. Creates a deployment version snapshot
DeploymentManager.create_deployment_version(
    workflow_id=workflow_id,
    workflow_snapshot=workflow_dict,  # Full JSON snapshot
    description=f"Deployment of {workflow.name}"
)
```

### **Step 3: Deployment Complete**

After deployment:
- ✅ Workflow is marked as `is_deployed = true`
- ✅ Deployment version is created (for rollback capability)
- ✅ Vector stores are configured for persistence
- ✅ Workflow becomes queryable via `/query` endpoint

---

## 🌐 How to Query Deployed Workflows

### **Option 1: Direct API Call**

```javascript
// From your website or app
const response = await fetch('https://your-nodeflow-server.com/api/v1/workflows/my-workflow-id/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key-here',  // Optional but recommended
  },
  body: JSON.stringify({
    input: {
      query: 'What is your return policy?',
      // ... other input data
    }
  })
});

const data = await response.json();
console.log(data.results);  // Workflow execution results
```

### **Option 2: Using the Embed Widget**

The embed widget is a React component that wraps the API call:

```tsx
import { NodAIWidget } from '@nodeflow/widget';

// In your website
<NodAIWidget
  apiKey="nk_..."
  workflowId="my-workflow-id"
  apiUrl="https://your-nodeflow-server.com"
/>
```

---

## 🎨 How Embed Widgets Work

### **What is the Embed Widget?**

The embed widget (`NodAIWidget.tsx`) is a **React component** that provides a ready-made UI for querying deployed workflows. It's like a chat interface that you can embed in any website.

### **How is it Generated?**

The widget is **NOT automatically generated** for all workflows. Instead:

1. **It's a reusable component** - You can use it for any deployed workflow
2. **You configure it** - Pass the `workflowId` and `apiKey` as props
3. **It makes API calls** - Internally calls `/workflows/{workflow_id}/query`

### **Widget Code Flow:**

```tsx
// User types a question
query = "What is your return policy?"

// Widget makes API call
POST /api/v1/workflows/{workflowId}/query
Headers: { 'X-API-Key': apiKey }
Body: { input: { query: "What is your return policy?" } }

// Backend executes workflow
// Returns results

// Widget displays response
setResponse(data.results);
```

### **Is it for All Workflows?**

**No, it's optional:**
- ✅ You can use the widget for any deployed workflow
- ✅ You can use direct API calls instead
- ✅ You can build your own UI
- ✅ The widget is just a convenience component

---

## 📊 Data Storage

### **Where is Workflow Data Stored?**

1. **Workflow Definitions (JSON):**
   - **Local**: `backend/data/workflows/*.json`
   - **Supabase** (if configured): Stored in database
   - **Not in client**: Workflows never leave your server

2. **Vector Stores:**
   - **FAISS**: `backend/data/vectors/{workflow_id}/{node_id}.faiss`
   - **Pinecone**: In your Pinecone account
   - **Chroma**: In your Chroma instance

3. **Deployment Versions:**
   - **In-memory** (current): `_deployment_versions` dictionary
   - **Future**: Should be stored in database for persistence

---

## 🔐 Security & Access Control

### **API Keys (Optional but Recommended)**

```python
# In query endpoint
x_api_key: Optional[str] = Header(None, alias="X-API-Key")

# You can validate API keys here
if x_api_key:
    # Validate API key
    # Check permissions
    # Rate limiting per key
```

### **Current Implementation:**
- API keys are **optional** (can be None)
- No validation yet (you can add this)
- Recommended for production use

### **Future Enhancements:**
- API key management UI
- Per-workflow API keys
- Rate limiting per key
- Usage tracking per key

---

## 🎯 Common Use Cases

### **Use Case 1: Website Chat Widget**

```html
<!-- On your website -->
<div id="chat-widget"></div>
<script>
  // Load widget
  ReactDOM.render(
    <NodAIWidget
      apiKey="nk_..."
      workflowId="customer-support-bot"
      apiUrl="https://api.yourcompany.com"
    />,
    document.getElementById('chat-widget')
  );
</script>
```

### **Use Case 2: Backend Service Integration**

```python
# In your Python backend
import requests

response = requests.post(
    'https://api.yourcompany.com/api/v1/workflows/rag-chatbot/query',
    headers={'X-API-Key': 'your-api-key'},
    json={'input': {'query': user_question}}
)

answer = response.json()['results']['chat']['output']
```

### **Use Case 3: Mobile App**

```javascript
// In your React Native app
const queryWorkflow = async (question) => {
  const response = await fetch(
    'https://api.yourcompany.com/api/v1/workflows/my-workflow/query',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body: JSON.stringify({
        input: { query: question }
      })
    }
  );
  return await response.json();
};
```

---

## ❓ FAQ

### **Q: Where exactly are workflows deployed?**
**A:** To your Nodeflow backend server (Railway, AWS, etc.). The workflow JSON is stored on the server's file system or in Supabase.

### **Q: Do clients download the workflow?**
**A:** No. Workflows never leave your server. Clients only send queries and receive results.

### **Q: Is the embed widget automatically created?**
**A:** No. It's a reusable React component. You configure it with a `workflowId` and use it wherever you want.

### **Q: Can I use the widget for multiple workflows?**
**A:** Yes! Just change the `workflowId` prop. Each widget instance can query a different workflow.

### **Q: Do I need Supabase for deployment?**
**A:** No. Supabase is optional. Workflows can be stored in JSON files on the server.

### **Q: How do I get an API key?**
**A:** Currently, API keys are not automatically generated. You can:
- Generate them manually
- Use a simple token system
- Implement API key management (future feature)

### **Q: Can I deploy to multiple environments?**
**A:** Currently, deployment is to your single backend instance. For multiple environments, you'd need:
- Separate backend instances (dev, staging, prod)
- Or environment-specific workflow IDs

---

## 🚀 Next Steps

1. **Deploy a workflow** via the UI
2. **Test the query endpoint** with curl or Postman
3. **Embed the widget** in a test HTML page
4. **Set up API keys** for production use
5. **Monitor usage** via deployment metrics

---

## 📝 Summary

- **Deployment Location**: Your Nodeflow backend server (not Supabase, not clients)
- **Deployment Process**: Marks workflow as deployed, creates version snapshot, enables persistence
- **Query Method**: `POST /api/v1/workflows/{workflow_id}/query`
- **Embed Widget**: Optional React component for easy integration
- **Storage**: Workflows stored on server (JSON files or Supabase)
- **Security**: API keys optional but recommended

The key insight: **Deployment makes your workflow queryable via API. The embed widget is just a UI component that calls that API.**

