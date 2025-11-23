# Phase 2: API Keys, Widgets, and SDKs

## ✅ Completed Features

### 1. API Key Management System

**Backend:**
- `backend/core/api_keys.py`: Core API key management
  - Secure key generation (SHA-256 hashing)
  - Key storage (file-based, can migrate to DB)
  - Key validation
- `backend/api/api_keys.py`: REST API endpoints
  - `POST /api/v1/api-keys`: Create new API key
  - `GET /api/v1/api-keys`: List all API keys
  - `GET /api/v1/api-keys/{key_id}`: Get specific key
  - `PUT /api/v1/api-keys/{key_id}`: Update key (name, active, limits)
  - `DELETE /api/v1/api-keys/{key_id}`: Delete key
  - `GET /api/v1/api-keys/{key_id}/usage`: Get usage statistics

**Frontend:**
- `frontend/src/services/apiKeys.ts`: API client service
- `frontend/src/components/APIKeys/APIKeyManager.tsx`: Management UI
- Added "API Keys" tab to Dashboard

### 2. Usage Tracking

**Backend:**
- `backend/core/usage_tracking.py`: Usage tracking system
  - Records requests, costs, duration per API key
  - Daily log files (JSONL format)
  - Statistics aggregation (total requests, costs, daily stats)
  - Rate limiting (requests per hour)
  - Cost limiting (dollars per month)

**Integration:**
- Usage automatically recorded when API key is used in query endpoint
- Rate and cost limits enforced on query requests

### 3. API Key Validation

**Backend:**
- Optional API key validation in `/workflows/{workflow_id}/query` endpoint
- Validates key via `X-API-Key` header
- Checks workflow association
- Enforces rate and cost limits
- Returns appropriate HTTP status codes (403, 429, 402)

## 🔄 In Progress

### 4. Embeddable Widgets

**Status:** Starting implementation

**Planned Features:**
- React component for embedding in external websites
- Configurable styling
- API key-based authentication
- Real-time query interface

## 📋 Remaining Tasks

### 5. SDK/Client Libraries

**Python SDK:**
- `nodai-python` package
- Simple client class
- Methods: `query_workflow(workflow_id, input, api_key)`
- Error handling
- Type hints

**JavaScript/TypeScript SDK:**
- `@nodai/sdk` npm package
- Browser and Node.js support
- TypeScript definitions
- Promise-based API

### 6. Hosted Service Configuration

**Documentation:**
- Deployment guide for cloud hosting
- Environment variables
- Scaling considerations
- Security best practices

## 🔑 API Key Format

- Format: `nk_<64_character_hex>`
- Example: `nk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2`
- Stored as SHA-256 hash (never plain text)
- Only shown once on creation

## 📊 Usage Tracking

**Metrics Tracked:**
- Total requests (all time)
- Total cost (all time)
- Requests today
- Cost today
- Last used timestamp

**Limits:**
- Rate limit: Requests per hour (optional)
- Cost limit: Dollars per month (optional)

## 🔐 Security Considerations

1. **Key Storage**: Keys are hashed (SHA-256) before storage
2. **Key Display**: Plain keys only shown once on creation
3. **Validation**: Keys validated on every request
4. **Rate Limiting**: Prevents abuse
5. **Cost Limiting**: Prevents unexpected charges
6. **Workflow Association**: Keys can be tied to specific workflows

## 🚀 Next Steps

1. Create embeddable widget component
2. Build Python SDK
3. Build JavaScript/TypeScript SDK
4. Add hosted deployment documentation
5. Add API key rotation mechanism
6. Add webhook support for usage alerts

