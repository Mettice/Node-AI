# Integrations System Architecture

## Overview

This document explains how to add integrations/connections to external tools and services (like S3, PostgreSQL, Reddit, Salesforce, etc.) in NodAI.

---

## 🏗️ Architecture

### **Two Types of Integrations:**

1. **Provider Integrations** (Already Implemented)
   - LLM providers (OpenAI, Anthropic, Gemini)
   - Embedding providers (OpenAI, Cohere, Voyage AI)
   - Vector stores (FAISS, Pinecone, Gemini File Search)
   - **How it works:** Built into node types, configured via provider selector

2. **Tool/Service Integrations** (To Be Implemented)
   - External APIs (Reddit, Salesforce, S3, etc.)
   - Databases (PostgreSQL, MongoDB, etc.)
   - Services (Resend, Serper, Perplexity, etc.)
   - **How it works:** New "Integration" node type or extend "Tool" node

---

## 🔌 How Integrations Work

### **Current System (Providers):**

```
User selects node → Chooses provider → Configures API keys → Uses service
Example: Chat node → OpenAI → Enter API key → Use GPT-4
```

### **Future System (Tool Integrations):**

```
User adds Integration node → Selects service → Authenticates (OAuth/API key) → 
Connects to service → Uses in workflow
Example: Integration node → Reddit → OAuth → Fetch posts → Process with LLM
```

---

## 📋 Implementation Plan

### **Phase 1: Integration Node Type**

Create a new node type called `integration` that can connect to external services.

**Backend:**
```python
# backend/nodes/tools/integration.py
class IntegrationNode(BaseNode):
    """
    Generic integration node for connecting to external services.
    """
    def get_schema(self):
        return {
            "service": {
                "type": "string",
                "enum": ["reddit", "s3", "postgresql", "salesforce", ...],
                "description": "Service to integrate with"
            },
            "action": {
                "type": "string",
                "description": "Action to perform (e.g., 'fetch_posts', 'upload_file')"
            },
            "credentials": {
                "type": "object",
                "description": "Authentication credentials"
            },
            # ... service-specific config
        }
```

**Frontend:**
```tsx
// Integration selector with icons
<IntegrationSelector
  service={selectedService}
  onServiceChange={setService}
  onActionChange={setAction}
/>
```

### **Phase 2: Credential Management**

Store and manage API keys/OAuth tokens securely.

**Backend:**
```python
# backend/core/credentials.py
class CredentialManager:
    """
    Manages API keys and OAuth tokens for integrations.
    """
    def store_credential(self, service: str, credential: dict):
        # Encrypt and store credentials
        pass
    
    def get_credential(self, service: str):
        # Retrieve and decrypt credentials
        pass
```

**Frontend:**
```tsx
// Credential management UI
<CredentialManager
  service="reddit"
  onSave={handleSaveCredential}
/>
```

### **Phase 3: Service Implementations**

Implement specific integrations one by one.

**Example: Reddit Integration**
```python
# backend/integrations/reddit.py
class RedditIntegration:
    def fetch_posts(self, subreddit: str, limit: int):
        # Use Reddit API
        pass
    
    def search(self, query: str):
        # Search Reddit
        pass
```

---

## 🎯 Integration Categories

### **1. Data Sources (Input)**
- **Reddit** - Fetch posts, comments
- **Twitter/X** - Fetch tweets
- **RSS Feeds** - Parse feeds
- **APIs** - Generic REST API calls
- **Databases** - PostgreSQL, MongoDB, MySQL

### **2. Data Destinations (Output)**
- **S3** - Upload files
- **Google Drive** - Upload documents
- **Slack** - Send messages
- **Email** - Send via Resend, SendGrid
- **Databases** - Write to databases

### **3. Processing Services**
- **Serper** - Google search API
- **Perplexity** - AI search
- **Web Scraping** - Scrape websites
- **Image Processing** - Resize, transform

### **4. Business Tools**
- **Salesforce** - CRM operations
- **Pipedrive** - Sales pipeline
- **HubSpot** - Marketing automation
- **Zapier** - Connect to Zapier workflows

---

## 🔐 Authentication Methods

### **1. API Keys** (Simplest)
```
User enters API key → Stored encrypted → Used in requests
Example: OpenAI, Serper, Resend
```

### **2. OAuth 2.0** (For user data)
```
User clicks "Connect" → Redirected to service → Authorizes → 
OAuth token stored → Used in requests
Example: Reddit, Google Drive, Salesforce
```

### **3. Basic Auth** (Username/Password)
```
User enters username/password → Stored encrypted → Used in requests
Example: Database connections
```

---

## 📦 Implementation Steps

### **Step 1: Create Integration Node**

1. **Backend:**
   - Create `backend/nodes/tools/integration.py`
   - Define schema with service selector
   - Create base integration handler

2. **Frontend:**
   - Add "Integration" to node palette
   - Create integration selector component
   - Add credential management UI

### **Step 2: Add First Integration (Example: Reddit)**

1. **Backend:**
   - Create `backend/integrations/reddit.py`
   - Implement Reddit API wrapper
   - Add to integration node

2. **Frontend:**
   - Add Reddit icon to ProviderIcon
   - Create Reddit configuration form
   - Add OAuth flow (if needed)

### **Step 3: Credential Storage**

1. **Backend:**
   - Create credential storage system
   - Encrypt sensitive data
   - Add credential management API

2. **Frontend:**
   - Create credential management UI
   - Add "Connect" buttons for OAuth
   - Show connected services

### **Step 4: Expand Integrations**

- Add more services one by one
- Create integration templates
- Build integration marketplace

---

## 🎨 UI/UX Design

### **Integration Selector:**
```
┌─────────────────────────────────┐
│ Select Integration              │
├─────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐        │
│ │ 🤖  │ │ ☁️  │ │ 🐘  │        │
│ │Reddit│ │  S3 │ │Postgres│    │
│ └─────┘ └─────┘ └─────┘        │
│                                 │
│ ┌─────┐ ┌─────┐ ┌─────┐        │
│ │ 📧  │ │ 🔍  │ │ 📊  │        │
│ │Resend│ │Serper│ │Salesforce│ │
│ └─────┘ └─────┘ └─────┘        │
└─────────────────────────────────┘
```

### **Credential Management:**
```
┌─────────────────────────────────┐
│ Connected Services              │
├─────────────────────────────────┤
│ ✅ Reddit (Connected)           │
│ ✅ OpenAI (API Key)             │
│ ❌ Salesforce (Not Connected)   │
│    [Connect]                    │
└─────────────────────────────────┘
```

---

## 🔄 Workflow Example

### **Reddit → LLM → Slack Workflow:**

```
1. Integration Node (Reddit)
   - Service: Reddit
   - Action: Fetch posts from r/MachineLearning
   - Output: List of posts

2. Processing Node (Chunk)
   - Split posts into chunks

3. LLM Node (Chat)
   - Summarize posts
   - Output: Summary

4. Integration Node (Slack)
   - Service: Slack
   - Action: Send message
   - Input: Summary from LLM
```

---

## 🚀 Quick Start: Adding a New Integration

### **1. Backend Implementation:**

```python
# backend/integrations/my_service.py
class MyServiceIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_data(self, params: dict):
        # Implement API call
        response = requests.get(
            "https://api.myservice.com/data",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params=params
        )
        return response.json()
```

### **2. Add to Integration Node:**

```python
# backend/nodes/tools/integration.py
INTEGRATIONS = {
    "my_service": MyServiceIntegration,
    # ... other integrations
}
```

### **3. Frontend:**

```tsx
// Add to ProviderIcon.tsx
my_service: {
  bg: 'bg-[#YOUR_COLOR]',
  icon: '🔧',
  name: 'My Service',
}

// Add to integration options
{ value: 'my_service', label: 'My Service' }
```

---

## 📚 Resources

- **OAuth 2.0 Flow:** https://oauth.net/2/
- **API Design:** RESTful best practices
- **Security:** Encrypt credentials at rest
- **Rate Limiting:** Respect API limits

---

## 🎯 Next Steps

1. ✅ Add provider icons (DONE)
2. ⏳ Create integration node type
3. ⏳ Implement credential management
4. ⏳ Add first integration (Reddit or S3)
5. ⏳ Expand to more services

**Start with one integration, then expand!** 🚀

