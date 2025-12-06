# Step 1.2: Rate Limit Strategy

**Date**: December 2025
**Purpose**: Define comprehensive rate limiting strategy for all API endpoints

---

## 🎯 Strategy Overview

We'll use a **tiered rate limiting approach** based on endpoint type and operation cost:

1. **Very Low (5/minute)** - Authentication, critical security operations
2. **Low (10/minute)** - Expensive operations, deletions, executions
3. **Medium (20/minute)** - Create/update operations
4. **High (30/minute)** - Read operations, queries
5. **Very High (100/minute)** - File uploads (already set)

---

## 📊 Rate Limit Tiers

### **Tier 1: Very Low (5/minute)** 🔒
**Use for**: Authentication and critical security operations

**Rationale**: 
- Prevents brute force attacks
- Protects sensitive operations
- Limits abuse of authentication endpoints

**Endpoints**:
- OAuth endpoints (init, callback, exchange)
- API key creation
- Any authentication-related operations

---

### **Tier 2: Low (10/minute)** ⚠️
**Use for**: Expensive operations, deletions, executions

**Rationale**:
- Prevents resource exhaustion
- Limits expensive operations (workflow execution, AI calls)
- Protects against accidental mass deletions

**Endpoints**:
- DELETE operations (workflows, files, secrets, etc.)
- Workflow execution
- Workflow deployment/undeployment
- Query endpoints (workflow queries)
- Knowledge base processing
- RAG evaluation
- Batch operations

---

### **Tier 3: Medium (20/minute)** 📝
**Use for**: Create and update operations

**Rationale**:
- Allows reasonable creation/update frequency
- Prevents spam creation
- Balances usability with protection

**Endpoints**:
- POST operations (create workflows, knowledge bases, etc.)
- PUT/PATCH operations (update resources)
- Webhook creation/updates
- Settings updates
- Budget/ROI calculations

---

### **Tier 4: High (30/minute)** 📖
**Use for**: Read operations, queries, analytics

**Rationale**:
- Allows frequent reads for dashboards/UI
- Prevents excessive polling
- Still protects against abuse

**Endpoints**:
- GET operations (list, retrieve resources)
- Analytics endpoints
- Metrics queries
- Trace queries
- Cost forecasting
- Model queries
- Version queries

---

### **Tier 5: Very High (100/minute)** 📤
**Use for**: File uploads (already implemented)

**Rationale**:
- File uploads are common but resource-intensive
- Higher limit allows legitimate use
- Still prevents abuse

**Endpoints**:
- File upload (already set ✅)

---

## 📋 Endpoint Classification

### **Authentication & Security (5/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/oauth/init` | POST | 5/minute |
| `/api/v1/oauth/callback` | GET | 5/minute |
| `/api/v1/oauth/exchange` | POST | 5/minute |
| `/api/v1/api-keys` | POST | 5/minute |

---

### **Expensive Operations (10/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/workflows/execute` | POST | 10/minute ✅ (already set) |
| `/api/v1/workflows/{workflow_id}/query` | POST | 10/minute |
| `/api/v1/workflows/{workflow_id}/deploy` | POST | 10/minute |
| `/api/v1/workflows/{workflow_id}/undeploy` | POST | 10/minute |
| `/api/v1/workflows/{workflow_id}/deployments/{version_number}/rollback` | POST | 10/minute |
| `/api/v1/knowledge-bases/{kb_id}/process` | POST | 10/minute |
| `/api/v1/knowledge-bases/{kb_id}/versions/{version_number}/rollback` | POST | 10/minute |
| `/api/v1/rag-eval/evaluate` | POST | 10/minute |
| `/api/v1/rag-eval/ab-test` | POST | 10/minute |
| `/api/v1/rag-optimize/analyze` | POST | 10/minute |
| `/api/v1/prompt/test/batch` | POST | 10/minute |
| `/api/v1/prompt/ab-test` | POST | 10/minute |
| `/api/v1/webhooks/{webhook_id}/trigger` | POST | 10/minute |

---

### **Delete Operations (10/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/workflows/{workflow_id}` | DELETE | 10/minute ✅ (already set) |
| `/api/v1/files/{file_id}` | DELETE | 10/minute |
| `/api/v1/secrets/{secret_id}` | DELETE | 10/minute |
| `/api/v1/api-keys/{key_id}` | DELETE | 10/minute |
| `/api/v1/knowledge-bases/{kb_id}` | DELETE | 10/minute |
| `/api/v1/webhooks/{webhook_id}` | DELETE | 10/minute |
| `/api/v1/models/{model_id}` | DELETE | 10/minute |
| `/api/v1/oauth/tokens/{token_id}` | DELETE | 10/minute |

---

### **Create Operations (20/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/workflows` | POST | 20/minute ✅ (already set) |
| `/api/v1/knowledge-bases` | POST | 20/minute |
| `/api/v1/webhooks` | POST | 20/minute |
| `/api/v1/secrets` | POST | 20/minute |
| `/api/v1/models` | POST | 20/minute |
| `/api/v1/prompt/test` | POST | 20/minute |
| `/api/v1/prompt/version` | POST | 20/minute |
| `/api/v1/rag-eval/dataset` | POST | 20/minute |
| `/api/v1/cost/budget` | POST | 20/minute |
| `/api/v1/cost/roi` | POST | 20/minute |
| `/api/v1/finetune/{job_id}/register` | POST | 20/minute |
| `/api/v1/tools/test-connection` | POST | 20/minute |

---

### **Update Operations (20/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/workflows/{workflow_id}` | PUT | 30/minute ✅ (already set - can keep or change) |
| `/api/v1/secrets/{secret_id}` | PUT | 20/minute |
| `/api/v1/api-keys/{key_id}` | PUT | 20/minute |
| `/api/v1/knowledge-bases/{kb_id}` | PUT | 20/minute |
| `/api/v1/webhooks/{webhook_id}` | PUT | 20/minute |
| `/api/v1/models/{model_id}` | PATCH | 20/minute |
| `/api/v1/observability/settings` | PUT | 20/minute |

---

### **Read Operations (30/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/workflows` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/deployments` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/deployments/{version_number}` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/deployments/health` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/webhooks` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/traces` | GET | 30/minute |
| `/api/v1/executions/{execution_id}` | GET | 30/minute |
| `/api/v1/executions/{execution_id}/trace` | GET | 30/minute |
| `/api/v1/executions` | GET | 30/minute |
| `/api/v1/executions/{execution_id}/stream` | GET | 30/minute |
| `/api/v1/files/list` | GET | 30/minute |
| `/api/v1/files/{file_id}` | GET | 30/minute |
| `/api/v1/files/{file_id}/text` | GET | 30/minute |
| `/api/v1/secrets` | GET | 30/minute |
| `/api/v1/secrets/{secret_id}` | GET | 30/minute |
| `/api/v1/api-keys` | GET | 30/minute |
| `/api/v1/api-keys/{key_id}` | GET | 30/minute |
| `/api/v1/api-keys/{key_id}/usage` | GET | 30/minute |
| `/api/v1/knowledge-bases` | GET | 30/minute |
| `/api/v1/knowledge-bases/{kb_id}` | GET | 30/minute |
| `/api/v1/knowledge-bases/{kb_id}/versions` | GET | 30/minute |
| `/api/v1/knowledge-bases/{kb_id}/versions/{version_number}` | GET | 30/minute |
| `/api/v1/knowledge-bases/{kb_id}/versions/compare` | GET | 30/minute |
| `/api/v1/nodes` | GET | 30/minute |
| `/api/v1/nodes/{node_type}` | GET | 30/minute |
| `/api/v1/nodes/categories` | GET | 30/minute |
| `/api/v1/webhooks` | GET | 30/minute |
| `/api/v1/webhooks/{webhook_id}` | GET | 30/minute |
| `/api/v1/oauth/tokens` | GET | 30/minute |
| `/api/v1/traces/{execution_id}` | GET | 30/minute |
| `/api/v1/traces/{execution_id}/summary` | GET | 30/minute |
| `/api/v1/traces` | GET | 30/minute |
| `/api/v1/traces/{trace_id}` | GET | 30/minute |
| `/api/v1/observability/settings` | GET | 30/minute |
| `/api/v1/cost-forecast` | POST | 30/minute |
| `/api/v1/cost-forecast/{workflow_id}/trends` | GET | 30/minute |
| `/api/v1/cost-forecast/{workflow_id}/breakdown` | GET | 30/minute |
| `/api/v1/cost/analyze/{execution_id}` | GET | 30/minute |
| `/api/v1/cost/predict` | GET | 30/minute |
| `/api/v1/cost/forecast/{workflow_id}` | GET | 30/minute |
| `/api/v1/cost/budget/{workflow_id}` | GET | 30/minute |
| `/api/v1/cost/optimize/{execution_id}` | GET | 30/minute |
| `/api/v1/cost/record` | POST | 30/minute |
| `/api/v1/models` | GET | 30/minute |
| `/api/v1/models/{model_id}` | GET | 30/minute |
| `/api/v1/models/{model_id}/usage` | GET | 30/minute |
| `/api/v1/models/{model_id}/versions` | GET | 30/minute |
| `/api/v1/models/available/{provider}` | GET | 30/minute |
| `/api/v1/models/base/{provider}` | GET | 30/minute |
| `/api/v1/models/{model_id}/usage` | POST | 30/minute |
| `/api/v1/prompt/versions` | GET | 30/minute |
| `/api/v1/prompt/test/{test_id}` | GET | 30/minute |
| `/api/v1/rag-eval/dataset/{dataset_id}` | GET | 30/minute |
| `/api/v1/rag-eval/{evaluation_id}` | GET | 30/minute |
| `/api/v1/rag-eval` | GET | 30/minute |
| `/api/v1/rag-eval/quality-trends` | GET | 30/minute |
| `/api/v1/rag-optimize/{analysis_id}` | GET | 30/minute |
| `/api/v1/executions/{execution_id}/record` | POST | 30/minute |
| `/api/v1/workflows/{workflow_id}/metrics` | GET | 30/minute |
| `/api/v1/workflows/{workflow_id}/versions/compare` | GET | 30/minute |
| `/api/v1/finetune/{job_id}/status` | GET | 30/minute |
| `/api/v1/finetune/jobs` | GET | 30/minute |

---

### **File Upload (100/minute)**

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/upload` | POST | 100/minute ✅ (already set) |

---

## 🎯 Implementation Rules

### **Rule 1: Request Parameter Required**
All endpoints with rate limiting **MUST** have `request: Request` as the first parameter after `self` (for class methods) or as the first parameter (for function endpoints).

**Correct**:
```python
@router.get("/endpoint")
@limiter.limit("30/minute")
async def my_endpoint(request: Request, ...):
    ...
```

**Incorrect**:
```python
@router.get("/endpoint")
@limiter.limit("30/minute")
async def my_endpoint(workflow_id: str, ...):  # Missing request parameter!
    ...
```

---

### **Rule 2: Import Limiter**
All API files need to import the limiter:

```python
from backend.core.security import limiter
```

---

### **Rule 3: Decorator Order**
The `@limiter.limit()` decorator must come **after** the `@router` decorator:

```python
@router.get("/endpoint")  # First
@limiter.limit("30/minute")  # Second
async def my_endpoint(request: Request, ...):
    ...
```

---

### **Rule 4: Rate Limit Format**
Use the format: `"X/minute"` where X is the number of requests.

Valid formats:
- `"5/minute"`
- `"10/minute"`
- `"20/minute"`
- `"30/minute"`
- `"100/minute"`

---

## 📊 Summary Statistics

| Tier | Rate Limit | Count | Purpose |
|------|------------|-------|---------|
| Tier 1 | 5/minute | 4 | Authentication |
| Tier 2 | 10/minute | 25 | Expensive operations, deletions |
| Tier 3 | 20/minute | 20 | Create/update operations |
| Tier 4 | 30/minute | 57 | Read operations |
| Tier 5 | 100/minute | 1 | File uploads |
| **Total** | | **107** | |

**Note**: 5 endpoints already have rate limits, so we need to add 106 more.

---

## ✅ Next Steps

1. ✅ **Step 1.1 Complete**: Identified all endpoints
2. ✅ **Step 1.2 Complete**: Defined rate limit strategy
3. **Step 1.3**: Start adding rate limits to workflows API
4. **Step 1.4**: Continue with other API files

---

## 📝 Quick Reference

**When adding rate limits, use this decision tree**:

1. **Is it authentication?** → 5/minute
2. **Is it DELETE?** → 10/minute
3. **Is it expensive (execution, deploy, process)?** → 10/minute
4. **Is it POST (create)?** → 20/minute
5. **Is it PUT/PATCH (update)?** → 20/minute
6. **Is it GET (read)?** → 30/minute
7. **Is it file upload?** → 100/minute

---

**Step 1.2 Complete! ✅**

**Ready for Step 1.3: Add Rate Limits to Workflows API**

