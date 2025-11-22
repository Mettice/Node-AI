# Secrets Vault Strategy

**Secure storage and management of user API keys and integration secrets**

---

## 🎯 Goals

1. **Secure Storage** - Encrypt API keys at rest
2. **User Isolation** - Each user's secrets are private
3. **Easy Access** - Users can manage their keys easily
4. **Integration Ready** - Support all LLM providers and integrations
5. **Audit Trail** - Track key usage and access

---

## 🔐 Security Requirements

### Encryption

- **At Rest:** Encrypt all secrets before storing in database
- **In Transit:** HTTPS/TLS for all API calls
- **Key Management:** Use environment-based encryption keys
- **Algorithm:** AES-256-GCM (industry standard)

### Access Control

- **User Isolation:** Users can only access their own secrets
- **No Plaintext Storage:** Never store unencrypted secrets
- **Secure Retrieval:** Decrypt only when needed, in memory
- **Audit Logging:** Log all access to secrets

---

## 🗄️ Database Schema

### Secrets Vault Table

```sql
CREATE TABLE secrets_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Secret Metadata
    name TEXT NOT NULL, -- e.g., "OpenAI API Key", "Slack Bot Token"
    provider TEXT NOT NULL, -- e.g., "openai", "anthropic", "slack", "google"
    secret_type TEXT NOT NULL, -- 'api_key', 'oauth_token', 'webhook_secret', 'connection_string'
    
    -- Encrypted Secret
    encrypted_value TEXT NOT NULL, -- AES-256-GCM encrypted
    encryption_key_id TEXT NOT NULL, -- Reference to encryption key version
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage Tracking
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- Expiration (optional)
    expires_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id),
    
    -- Indexes
    INDEX idx_secrets_user_id (user_id),
    INDEX idx_secrets_provider (provider),
    INDEX idx_secrets_type (secret_type),
    INDEX idx_secrets_active (is_active)
);

-- Secret Access Log (audit trail)
CREATE TABLE secret_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    secret_id UUID NOT NULL REFERENCES secrets_vault(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id),
    accessed_at TIMESTAMP DEFAULT NOW(),
    access_type TEXT NOT NULL, -- 'read', 'update', 'delete', 'use'
    workflow_id UUID REFERENCES workflows(id),
    node_id TEXT,
    ip_address TEXT,
    user_agent TEXT
);
```

### Row Level Security

```sql
-- Users can only access their own secrets
CREATE POLICY "Users can manage own secrets"
    ON secrets_vault FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Admins can view all (for support)
CREATE POLICY "Admins can view all secrets"
    ON secrets_vault FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );
```

---

## 🔒 Encryption Strategy

### Encryption Key Management

**Option 1: Environment-Based Key (Recommended for Start)**
```python
# Master encryption key from environment
ENCRYPTION_KEY = os.getenv("VAULT_ENCRYPTION_KEY")  # 32 bytes (256 bits)
```

**Option 2: Key Derivation (More Secure)**
```python
# Derive key from user ID + master key
def derive_user_key(user_id: str, master_key: bytes) -> bytes:
    """Derive encryption key for user."""
    return pbkdf2_hmac('sha256', master_key, user_id.encode(), 100000)
```

**Option 3: Key Management Service (Production)**
- AWS KMS
- HashiCorp Vault
- Google Cloud KMS

### Encryption Implementation

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class SecretsVault:
    """Secure secrets storage and retrieval."""
    
    def __init__(self, master_key: bytes):
        self.master_key = master_key
    
    def encrypt_secret(self, user_id: str, secret: str) -> str:
        """Encrypt a secret for storage."""
        # Derive user-specific key
        user_key = self._derive_key(user_id)
        f = Fernet(user_key)
        
        # Encrypt
        encrypted = f.encrypt(secret.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_secret(self, user_id: str, encrypted_secret: str) -> str:
        """Decrypt a secret for use."""
        # Derive user-specific key
        user_key = self._derive_key(user_id)
        f = Fernet(user_key)
        
        # Decrypt
        encrypted_bytes = base64.b64decode(encrypted_secret.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def _derive_key(self, user_id: str) -> bytes:
        """Derive encryption key for user."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id.encode(),  # User ID as salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return key
```

---

## 🎨 UI/UX Design

### Settings Tab Structure

```
Settings
├── Profile
│   ├── Name, Email
│   └── Avatar
├── Secrets Vault ⭐ NEW
│   ├── API Keys
│   │   ├── OpenAI
│   │   ├── Anthropic
│   │   ├── Google Gemini
│   │   └── [Add Provider]
│   ├── Integrations
│   │   ├── Slack
│   │   ├── Google Drive
│   │   ├── Reddit
│   │   └── [Add Integration]
│   ├── Database Connections
│   │   ├── PostgreSQL
│   │   ├── MySQL
│   │   └── [Add Database]
│   └── Other Secrets
│       └── [Custom Secrets]
└── Preferences
    ├── Theme
    └── Notifications
```

### Secret Management UI

**List View:**
- Card for each secret
- Provider icon
- Name/description
- Status (Active/Inactive)
- Last used
- Actions (Edit, Delete, Test)

**Add/Edit Modal:**
- Provider selector (with icons)
- Secret type selector
- Name field
- Secret value field (masked input)
- Description
- Tags
- Expiration (optional)
- Test connection button

**Security Features:**
- Masked display (show only last 4 chars)
- Copy to clipboard (with confirmation)
- Test connection before saving
- Usage history
- Access logs

---

## 🔧 Implementation Plan

### Phase 1: Backend Vault System (Week 1)

**Tasks:**
1. Create encryption utilities
2. Create secrets vault models
3. Create database schema
4. Implement CRUD operations
5. Add encryption/decryption
6. Add audit logging

**Files to Create:**
- `backend/core/secrets_vault.py` - Vault logic
- `backend/core/encryption.py` - Encryption utilities
- `backend/api/secrets.py` - API endpoints

### Phase 2: Frontend UI (Week 1-2)

**Tasks:**
1. Create Secrets Vault component
2. Add to Settings tab
3. Create secret list view
4. Create add/edit modal
5. Add provider icons
6. Add test connection

**Files to Create:**
- `frontend/src/components/Settings/SecretsVault.tsx`
- `frontend/src/components/Settings/SecretForm.tsx`
- `frontend/src/components/Settings/SecretCard.tsx`
- `frontend/src/services/secrets.ts`

### Phase 3: Integration (Week 2)

**Tasks:**
1. Update nodes to use user secrets
2. Add secret selection in node configs
3. Decrypt secrets on-demand
4. Cache decrypted secrets (in-memory, short TTL)
5. Update all LLM nodes
6. Update integration nodes

**Files to Modify:**
- All LLM nodes (chat, vision, embed)
- All integration nodes (slack, email, etc.)
- Node configuration forms

### Phase 4: Security & Testing (Week 2-3)

**Tasks:**
1. Security audit
2. Penetration testing
3. Encryption testing
4. Access control testing
5. Performance testing
6. Documentation

---

## 🔐 Security Best Practices

### 1. Encryption

- ✅ **AES-256-GCM** for encryption
- ✅ **User-specific keys** (derived from master + user ID)
- ✅ **Never log secrets** (even in debug mode)
- ✅ **Secure key storage** (environment variables, KMS)

### 2. Access Control

- ✅ **RLS policies** at database level
- ✅ **User isolation** (users see only their secrets)
- ✅ **Audit logging** (all access logged)
- ✅ **Rate limiting** (prevent brute force)

### 3. Secret Handling

- ✅ **Masked display** (show only last 4 chars)
- ✅ **In-memory only** (decrypt when needed, clear after use)
- ✅ **Short TTL cache** (cache decrypted secrets briefly)
- ✅ **Secure deletion** (overwrite before delete)

### 4. Key Rotation

- ✅ **Support key rotation** (re-encrypt with new key)
- ✅ **Version tracking** (track encryption key versions)
- ✅ **Migration path** (re-encrypt all secrets)

---

## 📋 Secret Types

### API Keys

| Provider | Secret Type | Example |
|----------|-------------|---------|
| OpenAI | `api_key` | `sk-...` |
| Anthropic | `api_key` | `sk-ant-...` |
| Google Gemini | `api_key` | `AIza...` |
| Cohere | `api_key` | `...` |
| Voyage AI | `api_key` | `...` |

### OAuth Tokens

| Integration | Secret Type | Example |
|-------------|-------------|---------|
| Slack | `oauth_token` | `xoxb-...` |
| Google Drive | `oauth_token` | `ya29...` |
| Reddit | `oauth_token` | `...` |

### Connection Strings

| Type | Secret Type | Example |
|------|-------------|---------|
| PostgreSQL | `connection_string` | `postgresql://...` |
| MySQL | `connection_string` | `mysql://...` |
| Pinecone | `api_key` | `...` |

### Webhook Secrets

| Type | Secret Type | Example |
|------|-------------|---------|
| Webhook Secret | `webhook_secret` | `whsec_...` |

---

## 🎯 Usage in Nodes

### How Nodes Access Secrets

```python
# In node execution
async def execute(self, inputs, config):
    # Get user ID from context
    user_id = config.get("_user_id")
    
    # Get secret from vault
    secret = await get_user_secret(
        user_id=user_id,
        provider="openai",
        secret_type="api_key"
    )
    
    # Use secret (it's already decrypted)
    client = OpenAI(api_key=secret)
    # ...
    
    # Secret is cleared from memory after use
```

### Node Configuration UI

```typescript
// In node config form
<SecretSelector
  provider="openai"
  secretType="api_key"
  value={config.api_key_secret_id}
  onChange={(secretId) => updateConfig({ api_key_secret_id: secretId })}
/>
```

---

## 🔄 Migration Strategy

### Existing API Keys

**Current State:**
- API keys stored in environment variables
- Global for all users

**Migration:**
1. Create default secrets for admin user
2. Import from environment variables
3. Users can add their own keys
4. Gradually migrate to user-specific keys

---

## 📊 Database Schema Details

### Secrets Vault Table

```sql
CREATE TABLE secrets_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Identification
    name TEXT NOT NULL,
    provider TEXT NOT NULL, -- 'openai', 'anthropic', 'slack', etc.
    secret_type TEXT NOT NULL, -- 'api_key', 'oauth_token', 'connection_string'
    
    -- Encrypted Value
    encrypted_value TEXT NOT NULL,
    encryption_key_id TEXT NOT NULL DEFAULT 'v1', -- For key rotation
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_in_workflow UUID REFERENCES workflows(id),
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_provider UNIQUE(user_id, provider, secret_type)
);
```

### Access Log Table

```sql
CREATE TABLE secret_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    secret_id UUID NOT NULL REFERENCES secrets_vault(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id),
    accessed_at TIMESTAMP DEFAULT NOW(),
    access_type TEXT NOT NULL, -- 'read', 'update', 'delete', 'use'
    workflow_id UUID REFERENCES workflows(id),
    node_id TEXT,
    ip_address INET,
    user_agent TEXT
);
```

---

## 🎨 UI Components

### Secrets Vault Manager

**Location:** Settings Tab → Secrets Vault

**Features:**
- List all secrets (grouped by provider)
- Add new secret
- Edit existing secret
- Delete secret
- Test connection
- View usage history
- Copy secret ID (for reference)

### Secret Form Modal

**Fields:**
- Provider (dropdown with icons)
- Secret Type (auto-selected based on provider)
- Name (auto-filled, editable)
- Secret Value (masked input, show/hide toggle)
- Description (optional)
- Tags (optional)
- Expiration (optional)
- Test Connection button

### Secret Card

**Display:**
- Provider icon
- Name
- Type badge
- Status (Active/Inactive)
- Last used timestamp
- Usage count
- Actions (Edit, Delete, Test)

---

## 🔐 Security Implementation

### Encryption Flow

```
1. User enters secret in UI
   ↓
2. Frontend sends to backend (HTTPS)
   ↓
3. Backend derives user-specific key
   ↓
4. Encrypt secret with user key
   ↓
5. Store encrypted value in database
   ↓
6. Never store plaintext
```

### Decryption Flow

```
1. Node needs secret
   ↓
2. Backend retrieves encrypted value
   ↓
3. Derive user-specific key
   ↓
4. Decrypt secret
   ↓
5. Return to node (in-memory only)
   ↓
6. Clear from memory after use
```

---

## 📋 Implementation Checklist

### Backend
- [ ] Create encryption utilities
- [ ] Create secrets vault models
- [ ] Create database schema
- [ ] Implement CRUD API endpoints
- [ ] Add encryption/decryption
- [ ] Add audit logging
- [ ] Add secret validation
- [ ] Add connection testing

### Frontend
- [ ] Create Secrets Vault component
- [ ] Add to Settings tab
- [ ] Create secret list view
- [ ] Create add/edit modal
- [ ] Add provider icons
- [ ] Add secret selector component
- [ ] Add test connection UI
- [ ] Add usage history view

### Integration
- [ ] Update LLM nodes to use vault
- [ ] Update integration nodes to use vault
- [ ] Add secret selection in node configs
- [ ] Update node execution to fetch secrets
- [ ] Add secret caching (short TTL)
- [ ] Update all node forms

### Security
- [ ] Security audit
- [ ] Encryption testing
- [ ] Access control testing
- [ ] Penetration testing
- [ ] Documentation

---

## 🚀 Quick Start

### Step 1: Add Encryption Key

Add to `.env`:
```env
VAULT_ENCRYPTION_KEY=generate-a-32-byte-random-key
```

Generate key:
```python
import secrets
key = secrets.token_bytes(32)
print(key.hex())  # Use this as VAULT_ENCRYPTION_KEY
```

### Step 2: Create Database Schema

Run migrations to create `secrets_vault` and `secret_access_log` tables.

### Step 3: Implement Backend

Create vault service and API endpoints.

### Step 4: Implement Frontend

Add Secrets Vault to Settings tab.

---

## 💡 Key Features

1. **Secure Storage** - AES-256-GCM encryption
2. **User Isolation** - Each user's secrets are private
3. **Easy Management** - Simple UI in Settings
4. **Provider Support** - All LLM providers and integrations
5. **Connection Testing** - Test before saving
6. **Usage Tracking** - See when/where secrets are used
7. **Audit Trail** - Complete access logging

---

**This vault system will securely store all user API keys and integration secrets!** 🔐

