# Integration Implementation Plan

## 📋 Overview

This document outlines the plan for integrating external tools and services into NodAI. We'll use a **hybrid approach**: extend the existing Tool Node for simple API-key-based services, and create dedicated nodes for complex services requiring OAuth or specialized UX.

---

## 🎯 Current State

### ✅ Already Implemented (Tool Node)
- **Calculator** - Mathematical expressions
- **Web Search** - DuckDuckGo, SerpAPI, Brave Search
- **Code Execution** - Python, JavaScript
- **Database Query** - SQLite, PostgreSQL, MySQL
- **API Call** - Generic REST API calls
- **Custom** - Placeholder for custom tools

### 🎨 Icons Available
All icons are already implemented in `ProviderIcon.tsx`:
- ✅ S3, PostgreSQL, Reddit, Salesforce, Pipedrive, Resend, Serper, Slack, Notion, Airtable, Google Drive
- ✅ Search providers: SerpAPI, DuckDuckGo, Brave
- ✅ Databases: SQLite, MySQL, PostgreSQL

---

## 🚀 Integration Roadmap

### **Phase 1: Quick Wins (Extend Tool Node)** ⚡
*Simple API-key-based integrations that fit well in the existing Tool Node*

#### 1. **Serper** (Web Search) 🔴 HIGH PRIORITY
- **What it does**: Google Search API with structured results
- **Why**: Better results than DuckDuckGo, more reliable than SerpAPI
- **How it works**:
  - Add `serper` to `web_search_provider` enum
  - Add `serper_api_key` field
  - Implement Serper API call in `create_langchain_tool()`
  - Returns structured search results (title, snippet, URL, position)
- **Input**: Search query string
- **Output**: Formatted search results
- **Config**: API key, number of results (default: 10)
- **Effort**: Low (2-3 hours)
- **Status**: ⏳ Pending

#### 2. **Perplexity** (AI Search) 🔴 HIGH PRIORITY
- **What it does**: AI-powered search that understands context and provides comprehensive answers
- **Why**: Perfect for AI workflows, provides better context than traditional search
- **How it works**:
  - Add `perplexity` to `web_search_provider` enum
  - Add `perplexity_api_key` field
  - Implement Perplexity API call (uses chat completion endpoint)
  - Returns AI-generated answer with citations
- **Input**: Search query string
- **Output**: AI-generated answer with sources
- **Config**: API key, model (sonar, sonar-pro), search focus (web, academic, writing, etc.)
- **Effort**: Low (2-3 hours)
- **Status**: ⏳ Pending

#### 3. **Resend** (Email) 🟡 MEDIUM PRIORITY
- **What it does**: Send transactional emails from workflows
- **Why**: Essential for notifications, alerts, and communication workflows
- **How it works**:
  - Add `email` to `tool_type` enum
  - Add `email_provider` enum (resend, sendgrid - start with resend)
  - Add `resend_api_key`, `email_from`, `email_to`, `email_subject`, `email_body` fields
  - Implement Resend API call in `create_langchain_tool()`
  - Returns email status (sent, failed, message_id)
- **Input**: To, Subject, Body (from previous node or config)
- **Output**: Email status and message ID
- **Config**: API key, from email, reply-to (optional), template support (future)
- **Effort**: Low (2-3 hours)
- **Status**: ⏳ Pending

#### 4. **S3** (Cloud Storage) 🔴 HIGH PRIORITY
- **What it does**: Upload/download files to/from AWS S3
- **Why**: Most common cloud storage, needed for file-based workflows
- **How it works**:
  - Add `s3` to `tool_type` enum
  - Add `s3_operation` enum (upload, download, list, delete)
  - Add `aws_access_key_id`, `aws_secret_access_key`, `s3_bucket`, `s3_region` fields
  - Implement S3 operations using `boto3`
  - Returns file URL (upload) or file content (download)
- **Input**: File content/URL (for upload), file key (for download)
- **Output**: File URL (upload), file content (download), file list (list)
- **Config**: AWS credentials, bucket name, region, path prefix (optional)
- **Effort**: Medium (4-5 hours)
- **Status**: ⏳ Pending

---

### **Phase 2: Dedicated Nodes (Better UX)** 🎨
*Complex integrations that benefit from dedicated nodes with specialized UIs*

#### 5. **S3 Node** (Enhanced) 🔴 HIGH PRIORITY
- **What it does**: Full-featured S3 integration with better UX
- **Why**: Better than tool node for file operations, supports batch operations, progress tracking
- **How it works**:
  - Create `backend/nodes/storage/s3.py`
  - Create `frontend/src/components/Properties/S3NodeForm.tsx`
  - Support: upload, download, list, delete, copy, move
  - Show file browser UI, progress bars, error handling
- **Input**: File data from previous nodes
- **Output**: File URLs, file metadata, operation status
- **Config**: Connection (stored credentials), bucket, region, path
- **Effort**: Medium-High (6-8 hours)
- **Status**: ⏳ Pending

#### 6. **Email Node** (Enhanced) 🟡 MEDIUM PRIORITY
- **What it does**: Dedicated email node with template support
- **Why**: Better UX than tool node, supports templates, attachments, HTML emails
- **How it works**:
  - Create `backend/nodes/communication/email.py`
  - Create `frontend/src/components/Properties/EmailNodeForm.tsx`
  - Support: HTML/text emails, attachments, templates, batch sending
  - Show email preview, template selector
- **Input**: To, Subject, Body, Attachments (from previous nodes)
- **Output**: Email status, message IDs, delivery status
- **Config**: Provider (Resend, SendGrid), from email, templates, attachments
- **Effort**: Medium (5-6 hours)
- **Status**: ⏳ Pending

#### 7. **Database Node** (Enhanced) 🟡 MEDIUM PRIORITY
- **What it does**: Better database integration with query builder
- **Why**: Current tool node is too generic, needs query builder, connection management
- **How it works**:
  - Create `backend/nodes/storage/database.py`
  - Create `frontend/src/components/Properties/DatabaseNodeForm.tsx`
  - Support: Query builder UI, connection testing, schema browser, result preview
  - Store connections securely, support connection pooling
- **Input**: Query parameters (from previous nodes)
- **Output**: Query results (formatted), row count, execution time
- **Config**: Connection (stored), query type (SELECT, INSERT, UPDATE, DELETE), query builder
- **Effort**: Medium-High (6-8 hours)
- **Status**: ⏳ Pending

---

### **Phase 3: OAuth Integrations** 🔐
*Services requiring OAuth authentication*

#### 8. **Slack** (Notifications) 🟡 MEDIUM PRIORITY
- **What it does**: Send messages, create channels, post to channels
- **Why**: Popular for team workflows, notifications
- **How it works**:
  - Create `backend/nodes/communication/slack.py`
  - Create `frontend/src/components/Properties/SlackNodeForm.tsx`
  - Implement OAuth 2.0 flow for Slack
  - Support: Send message, create channel, upload file, post to thread
- **Input**: Message content, channel, user (from previous nodes)
- **Output**: Message timestamp, channel ID, thread timestamp
- **Config**: OAuth connection, channel selector, message format (text, blocks, attachments)
- **Effort**: High (8-10 hours) - OAuth complexity
- **Status**: ⏳ Pending

#### 9. **Google Drive** (File Storage) 🟡 MEDIUM PRIORITY
- **What it does**: Upload/download files, list files, share files
- **Why**: Popular file storage, integrates with Google Workspace
- **How it works**:
  - Create `backend/nodes/storage/google_drive.py`
  - Create `frontend/src/components/Properties/GoogleDriveNodeForm.tsx`
  - Implement OAuth 2.0 flow for Google Drive API
  - Support: Upload, download, list, search, share, create folders
- **Input**: File data, folder ID (from previous nodes)
- **Output**: File ID, file URL, file metadata
- **Config**: OAuth connection, folder selector, file type filter
- **Effort**: High (8-10 hours) - OAuth complexity
- **Status**: ⏳ Pending

#### 10. **Reddit** (Content Aggregation) 🟢 LOW PRIORITY
- **What it does**: Fetch posts, comments, search Reddit
- **Why**: Content aggregation, monitoring, social listening
- **How it works**:
  - Create `backend/nodes/integration/reddit.py`
  - Create `frontend/src/components/Properties/RedditNodeForm.tsx`
  - Implement OAuth 2.0 flow (or use API key for read-only)
  - Support: Fetch posts, comments, search, monitor subreddits
- **Input**: Subreddit, search query, post ID (from previous nodes)
- **Output**: Posts/comments data (JSON), formatted text
- **Config**: OAuth connection (or API key), subreddit, sort order, time range
- **Effort**: Medium (5-6 hours) - OAuth optional
- **Status**: ⏳ Pending

---

### **Phase 4: Business Tools** 💼
*Enterprise/business integrations*

#### 11. **Salesforce** (CRM) 🟢 LOW PRIORITY
- **What it does**: Create/update leads, contacts, opportunities
- **Why**: Enterprise CRM automation
- **How it works**:
  - Create `backend/nodes/integration/salesforce.py`
  - Create `frontend/src/components/Properties/SalesforceNodeForm.tsx`
  - Implement OAuth 2.0 flow for Salesforce
  - Support: SOQL queries, create/update records, trigger workflows
- **Input**: Record data (from previous nodes)
- **Output**: Record ID, success status, error messages
- **Config**: OAuth connection, object type (Lead, Contact, Opportunity), operation
- **Effort**: High (10-12 hours) - Complex API
- **Status**: ⏳ Pending

#### 12. **Notion** (Knowledge Base) 🟢 LOW PRIORITY
- **What it does**: Read/write Notion pages, databases
- **Why**: Knowledge base integration, content management
- **How it works**:
  - Create `backend/nodes/integration/notion.py`
  - Create `frontend/src/components/Properties/NotionNodeForm.tsx`
  - Implement OAuth 2.0 flow for Notion
  - Support: Read pages, create pages, query databases, update pages
- **Input**: Page content, database query (from previous nodes)
- **Output**: Page data, database results, page ID
- **Config**: OAuth connection, workspace, page/database selector
- **Effort**: High (8-10 hours) - Complex API
- **Status**: ⏳ Pending

#### 13. **Airtable** (Structured Data) 🟢 LOW PRIORITY
- **What it does**: Read/write Airtable records
- **Why**: Structured data storage, easy to use
- **How it works**:
  - Create `backend/nodes/integration/airtable.py`
  - Create `frontend/src/components/Properties/AirtableNodeForm.tsx`
  - Use API key (no OAuth needed)
  - Support: List records, create records, update records, query records
- **Input**: Record data (from previous nodes)
- **Output**: Record IDs, record data, success status
- **Config**: API key, base ID, table name, view (optional)
- **Effort**: Medium (5-6 hours)
- **Status**: ⏳ Pending

---

## 📊 Implementation Summary

| Integration | Phase | Priority | Effort | Approach | Status |
|------------|-------|----------|--------|----------|--------|
| Serper | 1 | 🔴 High | Low (2-3h) | Extend Tool Node | ⏳ Pending |
| Perplexity | 1 | 🔴 High | Low (2-3h) | Extend Tool Node | ⏳ Pending |
| Resend | 1 | 🟡 Medium | Low (2-3h) | Extend Tool Node | ⏳ Pending |
| S3 (Tool) | 1 | 🔴 High | Medium (4-5h) | Extend Tool Node | ⏳ Pending |
| S3 (Node) | 2 | 🔴 High | Medium-High (6-8h) | Dedicated Node | ⏳ Pending |
| Email (Node) | 2 | 🟡 Medium | Medium (5-6h) | Dedicated Node | ⏳ Pending |
| Database (Node) | 2 | 🟡 Medium | Medium-High (6-8h) | Dedicated Node | ⏳ Pending |
| Slack | 3 | 🟡 Medium | High (8-10h) | Dedicated Node + OAuth | ⏳ Pending |
| Google Drive | 3 | 🟡 Medium | High (8-10h) | Dedicated Node + OAuth | ⏳ Pending |
| Reddit | 3 | 🟢 Low | Medium (5-6h) | Dedicated Node | ⏳ Pending |
| Salesforce | 4 | 🟢 Low | High (10-12h) | Dedicated Node + OAuth | ⏳ Pending |
| Notion | 4 | 🟢 Low | High (8-10h) | Dedicated Node + OAuth | ⏳ Pending |
| Airtable | 4 | 🟢 Low | Medium (5-6h) | Dedicated Node | ⏳ Pending |

---

## 🛠️ Implementation Details

### **Phase 1: Extend Tool Node**

#### Step 1: Update Backend Schema
```python
# backend/nodes/tools/tool_node.py

# Add to tool_type enum:
"tool_type": {
    "enum": ["calculator", "web_search", "code_execution", "database_query", "api_call", "email", "s3", "custom"],
    ...
}

# Add Serper to web_search_provider:
"web_search_provider": {
    "enum": ["brave", "serpapi", "duckduckgo", "serper", "perplexity"],
    ...
}

# Add new fields:
"serper_api_key": {...},
"perplexity_api_key": {...},
"email_provider": {...},
"resend_api_key": {...},
"s3_operation": {...},
"aws_access_key_id": {...},
"aws_secret_access_key": {...},
"s3_bucket": {...},
"s3_region": {...},
```

#### Step 2: Implement Tool Functions
```python
# In create_langchain_tool():

elif tool_type == "web_search":
    # Add Serper implementation
    elif provider == "serper":
        # Call Serper API
        ...
    elif provider == "perplexity":
        # Call Perplexity API
        ...

elif tool_type == "email":
    # Implement Resend email sending
    ...

elif tool_type == "s3":
    # Implement S3 operations
    ...
```

#### Step 3: Update Frontend
```typescript
// frontend/src/components/Properties/ToolTypeSelector.tsx
// Add new tool types with icons

// frontend/src/components/Properties/SchemaForm.tsx
// Add special handling for new tool types
// - Email: Show provider selector, from/to/subject/body fields
// - S3: Show operation selector, AWS credentials, bucket/region
```

---

### **Phase 2: Dedicated Nodes**

#### Step 1: Create Backend Node
```python
# backend/nodes/storage/s3.py
class S3Node(BaseNode):
    node_type = "s3"
    name = "S3 Storage"
    description = "Upload, download, and manage files in AWS S3"
    
    async def execute(self, inputs, config):
        # Implement S3 operations
        ...
```

#### Step 2: Create Frontend Form
```typescript
// frontend/src/components/Properties/S3NodeForm.tsx
// Custom form with:
// - Connection selector (stored credentials)
// - Operation selector (upload/download/list/delete)
// - Bucket/region/path inputs
// - File browser UI (for list operation)
// - Progress indicator (for upload/download)
```

#### Step 3: Register Node
```python
# backend/core/node_registry.py
NodeRegistry.register(S3Node.node_type, S3Node, S3Node().get_metadata())
```

```typescript
// frontend/src/components/Sidebar/NodePalette.tsx
// Add S3 node to palette with icon
```

---

### **Phase 3: OAuth Integrations**

#### Step 1: Create OAuth Flow
```python
# backend/core/oauth.py
class OAuthManager:
    def get_authorization_url(self, service: str) -> str:
        # Generate OAuth authorization URL
        ...
    
    def handle_callback(self, service: str, code: str) -> dict:
        # Exchange code for access token
        # Store token securely
        ...
```

#### Step 2: Create Backend Node
```python
# backend/nodes/communication/slack.py
class SlackNode(BaseNode):
    async def execute(self, inputs, config):
        # Get OAuth token from credential store
        token = get_oauth_token("slack", config["connection_id"])
        # Use token to call Slack API
        ...
```

#### Step 3: Create Frontend OAuth UI
```typescript
// frontend/src/components/Properties/SlackNodeForm.tsx
// Show "Connect" button if not connected
// On click, redirect to OAuth URL
// Handle callback, show connection status
```

---

## 🎯 Recommended Starting Point

### **Week 1: Quick Wins**
1. ✅ **Serper** (2-3 hours) - Extend web_search tool
2. ✅ **Perplexity** (2-3 hours) - Extend web_search tool
3. ✅ **Resend** (2-3 hours) - Add email tool type

**Total: ~8 hours**

### **Week 2: Storage**
4. ✅ **S3 (Tool Node)** (4-5 hours) - Add S3 to tool node
5. ✅ **S3 (Dedicated Node)** (6-8 hours) - Create full S3 node

**Total: ~12 hours**

### **Week 3: Communication**
6. ✅ **Email Node** (5-6 hours) - Dedicated email node
7. ✅ **Database Node** (6-8 hours) - Enhanced database node

**Total: ~13 hours**

### **Week 4: OAuth Setup**
8. ✅ **OAuth Infrastructure** (8-10 hours) - Build OAuth system
9. ✅ **Slack** (8-10 hours) - First OAuth integration

**Total: ~18 hours**

---

## 📝 Next Steps

1. **Review this plan** - Confirm priorities and approach
2. **Start with Phase 1** - Implement Serper, Perplexity, Resend
3. **Test thoroughly** - Ensure each integration works end-to-end
4. **Document usage** - Create examples for each integration
5. **Iterate** - Gather feedback and improve

---

## 🔗 Related Documentation

- `INTEGRATIONS_PRIORITY.md` - Priority analysis
- `INTEGRATIONS_SYSTEM.md` - Architecture overview
- `TOOL_NODE_GUIDE.md` - Current tool node implementation

---

**Ready to start? Let's begin with Phase 1!** 🚀

