# Database Migration & Authentication Strategy

**Strategic Plan for Multi-User, RBAC, and Database Implementation**

---

## 🎯 Goals

1. **Migrate from file-based to database storage**
2. **Implement user authentication and authorization**
3. **Add role-based access control (RBAC)**
4. **Maintain backward compatibility during migration**
5. **Ensure zero data loss**

---

## 📊 Current State Analysis

### Current Storage (File-Based)

| Data Type | Current Storage | Location | Migration Priority |
|-----------|----------------|----------|-------------------|
| **Workflows** | JSON files | `backend/data/workflows/` | 🔴 HIGH |
| **API Keys** | JSON files | `backend/data/api_keys/` | 🔴 HIGH |
| **Usage Tracking** | JSONL files | `backend/data/usage/` | 🟡 MEDIUM |
| **Deployments** | JSON files | `backend/data/deployments/` | 🟡 MEDIUM |
| **Knowledge Bases** | JSON files | `backend/data/knowledge_bases/` | 🟡 MEDIUM |
| **Webhooks** | JSON files | `backend/data/webhooks/` | 🟡 MEDIUM |
| **Secrets Vault** | N/A (new feature) | N/A | 🔴 HIGH |
| **Executions** | JSON files | `backend/data/executions/` | 🟢 LOW |
| **Vector Stores** | FAISS files | `backend/data/vectors/` | 🟢 LOW (keep file-based) |
| **Uploaded Files** | Filesystem | `backend/uploads/` | 🟢 LOW (keep file-based) |

### Current Limitations

- ❌ No user isolation (all workflows are global)
- ❌ No authentication (API keys are global)
- ❌ No access control (anyone with API key can access any workflow)
- ❌ No multi-tenancy
- ❌ Limited querying capabilities
- ❌ No transactions
- ❌ Difficult to scale

---

## 🗄️ Database Service Recommendation

### **Recommended: Supabase** ✅

**Why Supabase?**

1. **PostgreSQL** - Robust, ACID-compliant, SQL-based
2. **Built-in Auth** - Email/password, OAuth, magic links
3. **Row Level Security (RLS)** - Perfect for multi-tenancy
4. **Real-time** - Built-in subscriptions (future feature)
5. **Storage** - File storage API (for uploaded files)
6. **Free Tier** - Generous free tier for development
7. **Managed** - No infrastructure management
8. **TypeScript SDK** - Great for frontend integration
9. **REST API** - Auto-generated from schema
10. **Migrations** - Built-in migration system

### Alternative Options

#### Option 2: Self-Hosted PostgreSQL
- ✅ Full control
- ✅ No vendor lock-in
- ❌ More setup/maintenance
- ❌ Need to implement auth separately
- **Best for:** Enterprise deployments, on-premise

#### Option 3: MongoDB Atlas
- ✅ Document-based (similar to current JSON)
- ✅ Easy migration
- ❌ Less structured
- ❌ Need separate auth solution
- **Best for:** If you prefer NoSQL

#### Option 4: SQLite (Development Only)
- ✅ Simple, no setup
- ✅ Good for development
- ❌ Not scalable for production
- ❌ No built-in auth
- **Best for:** Local development, testing

---

## 🏗️ Proposed Architecture

### Database Schema Design

```sql
-- Users Table (handled by Supabase Auth, but we'll have a profiles table)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'user', -- 'admin', 'user', 'viewer'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflows Table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    tags TEXT[],
    is_template BOOLEAN DEFAULT FALSE,
    is_deployed BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_workflows_user_id (user_id),
    INDEX idx_workflows_deployed (is_deployed),
    INDEX idx_workflows_template (is_template)
);

-- API Keys Table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    key_id TEXT UNIQUE NOT NULL,
    key_hash TEXT NOT NULL, -- Hashed API key
    name TEXT NOT NULL,
    rate_limit INTEGER,
    cost_limit DECIMAL(10, 4),
    enabled BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    INDEX idx_api_keys_user_id (user_id),
    INDEX idx_api_keys_key_id (key_id)
);

-- Usage Tracking Table
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    execution_id TEXT,
    cost DECIMAL(10, 6) NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_usage_api_key (api_key_id),
    INDEX idx_usage_user (user_id),
    INDEX idx_usage_workflow (workflow_id),
    INDEX idx_usage_created (created_at)
);

-- Deployments Table
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id),
    version_number INTEGER NOT NULL,
    workflow_snapshot JSONB NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'inactive', 'rolled_back'
    deployed_at TIMESTAMP DEFAULT NOW(),
    deployed_by UUID REFERENCES profiles(id),
    
    -- Metrics
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    failed_queries INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10, 2) DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    
    UNIQUE(workflow_id, version_number),
    INDEX idx_deployments_workflow (workflow_id),
    INDEX idx_deployments_user (user_id)
);

-- Knowledge Bases Table
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    config JSONB NOT NULL, -- chunk_size, embed_model, etc.
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'ready', 'error'
    file_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_kb_user_id (user_id)
);

-- Webhooks Table
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    webhook_id TEXT UNIQUE NOT NULL,
    name TEXT,
    secret TEXT,
    method TEXT DEFAULT 'POST',
    enabled BOOLEAN DEFAULT TRUE,
    headers_required JSONB DEFAULT '{}',
    payload_mapping JSONB DEFAULT '{}',
    
    -- Statistics
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    last_called_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_webhooks_workflow (workflow_id),
    INDEX idx_webhooks_user (user_id),
    INDEX idx_webhooks_webhook_id (webhook_id)
);

-- Shared Resources (for team collaboration)
CREATE TABLE workflow_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    permission TEXT NOT NULL DEFAULT 'read', -- 'read', 'write', 'deploy'
    shared_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(workflow_id, shared_with_user_id),
    INDEX idx_shares_workflow (workflow_id),
    INDEX idx_shares_user (shared_with_user_id)
);

-- Secrets Vault (for storing user API keys and integration secrets)
CREATE TABLE secrets_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Identification
    name TEXT NOT NULL,
    provider TEXT NOT NULL, -- 'openai', 'anthropic', 'slack', 'google', etc.
    secret_type TEXT NOT NULL, -- 'api_key', 'oauth_token', 'connection_string', 'webhook_secret'
    
    -- Encrypted Value
    encrypted_value TEXT NOT NULL, -- AES-256-GCM encrypted
    encryption_key_id TEXT NOT NULL DEFAULT 'v1', -- For key rotation
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage Tracking
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_in_workflow UUID REFERENCES workflows(id),
    
    -- Expiration (optional)
    expires_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, provider, secret_type),
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
    ip_address INET,
    user_agent TEXT,
    
    INDEX idx_access_secret (secret_id),
    INDEX idx_access_user (user_id),
    INDEX idx_access_workflow (workflow_id),
    INDEX idx_access_time (accessed_at)
);
```

### Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;

-- Workflows: Users can only see their own workflows or shared ones
CREATE POLICY "Users can view own workflows"
    ON workflows FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view shared workflows"
    ON workflows FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM workflow_shares
            WHERE workflow_shares.workflow_id = workflows.id
            AND workflow_shares.shared_with_user_id = auth.uid()
        )
    );

-- Secrets Vault: Users can only access their own secrets
CREATE POLICY "Users can manage own secrets"
    ON secrets_vault FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Admins can view all secrets (for support)
CREATE POLICY "Admins can view all secrets"
    ON secrets_vault FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

CREATE POLICY "Users can create own workflows"
    ON workflows FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workflows"
    ON workflows FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workflows"
    ON workflows FOR DELETE
    USING (auth.uid() = user_id);

-- API Keys: Users can only manage their own keys
CREATE POLICY "Users can manage own API keys"
    ON api_keys FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Similar policies for other tables...
```

---

## 🔐 Authentication Strategy

### Option 1: Supabase Auth (Recommended) ✅

**Pros:**
- ✅ Built-in email/password
- ✅ OAuth providers (Google, GitHub, etc.)
- ✅ Magic links
- ✅ Email verification
- ✅ Password reset
- ✅ Session management
- ✅ JWT tokens automatically

**Implementation:**
1. Use Supabase Auth for user management
2. Frontend: `@supabase/supabase-js` client
3. Backend: Verify JWT tokens from Supabase
4. Row Level Security handles authorization

### Option 2: Custom JWT Auth

**Pros:**
- ✅ Full control
- ✅ No external dependency
- ✅ Customizable

**Cons:**
- ❌ Need to implement everything
- ❌ More code to maintain
- ❌ Need to handle OAuth separately

**Implementation:**
1. Use `python-jose` for JWT (already added)
2. Implement registration/login endpoints
3. Password hashing with `passlib` (already added)
4. Session management

---

## 👥 Role-Based Access Control (RBAC)

### Roles

| Role | Permissions | Use Case |
|------|------------|----------|
| **Admin** | All permissions | System administrators |
| **User** | Create, read, update, delete own resources | Regular users |
| **Viewer** | Read-only access | Read-only users, auditors |

### Permissions Matrix

| Resource | Admin | User | Viewer |
|----------|-------|------|--------|
| Own Workflows | CRUD + Deploy | CRUD + Deploy | Read |
| Shared Workflows | CRUD + Deploy | Based on share | Based on share |
| API Keys | All | Own only | None |
| Deployments | All | Own only | View own |
| Knowledge Bases | All | Own only | View own |
| Webhooks | All | Own only | View own |
| System Settings | Full | None | None |

### Permission Levels

- **Read (R):** View resource
- **Write (W):** Create, update, delete
- **Deploy (D):** Deploy workflows
- **Manage (M):** Full control including sharing

---

## 📋 Migration Strategy

### Phase 1: Database Setup (Week 1)

1. **Set up Supabase project**
   - Create project
   - Configure authentication
   - Set up database

2. **Create schema**
   - Run migrations
   - Set up RLS policies
   - Create indexes

3. **Add database client**
   - Install `supabase-py` or `psycopg2`
   - Create database connection layer
   - Add connection pooling

### Phase 2: Dual-Write System (Week 2)

1. **Implement database layer**
   - Create database models (SQLAlchemy or raw SQL)
   - Implement CRUD operations
   - Keep file-based as backup

2. **Dual-write pattern**
   - Write to both database AND files
   - Read from database (fallback to files)
   - Log any discrepancies

3. **Migration script**
   - Migrate existing data from files to database
   - Validate data integrity
   - Create rollback plan

### Phase 3: Authentication (Week 2-3)

1. **Frontend auth**
   - Integrate Supabase Auth client
   - Add login/register UI
   - Add protected routes

2. **Backend auth**
   - Verify JWT tokens
   - Extract user ID from token
   - Add user context to requests

3. **Migration**
   - Create default admin user
   - Migrate existing workflows to admin user
   - Set up user profiles

### Phase 4: RBAC Implementation (Week 3)

1. **Role management**
   - Add role to user profiles
   - Implement permission checks
   - Add role-based UI

2. **Resource ownership**
   - Add user_id to all resources
   - Update queries to filter by user
   - Implement sharing mechanism

3. **API key scoping**
   - Link API keys to users
   - Update validation logic
   - Add user context to queries

### Phase 5: Cutover (Week 4)

1. **Testing**
   - Test all operations
   - Verify RLS policies
   - Load testing

2. **Cutover**
   - Switch to database-only
   - Keep file backup for 30 days
   - Monitor for issues

3. **Cleanup**
   - Remove file-based code
   - Archive old files
   - Update documentation

---

## 🛠️ Implementation Plan

### Step 1: Choose Stack

**Recommended Stack:**
- **Database:** Supabase (PostgreSQL)
- **ORM:** SQLAlchemy (optional, can use raw SQL)
- **Auth:** Supabase Auth
- **Migration Tool:** Supabase Migrations or Alembic

### Step 2: Database Schema Design

1. **Design tables** (see schema above)
2. **Design relationships**
3. **Design indexes**
4. **Design RLS policies**

### Step 3: Migration Script

1. **Export existing data** from files
2. **Transform data** to match schema
3. **Import to database**
4. **Validate** data integrity
5. **Create rollback** script

### Step 4: Code Changes

1. **Create database layer**
   - Replace file operations with DB operations
   - Add user context
   - Add permission checks

2. **Update API endpoints**
   - Add authentication middleware
   - Add user context
   - Filter by user_id

3. **Update frontend**
   - Add auth UI
   - Add user context
   - Update API calls

---

## ⚠️ Risks & Mitigation

### Risk 1: Data Loss During Migration
**Mitigation:**
- Dual-write system
- Comprehensive backups
- Rollback plan
- Data validation

### Risk 2: Breaking Changes
**Mitigation:**
- Feature flags
- Gradual rollout
- Backward compatibility layer
- Extensive testing

### Risk 3: Performance Issues
**Mitigation:**
- Connection pooling
- Proper indexing
- Query optimization
- Load testing

### Risk 4: Auth Complexity
**Mitigation:**
- Use Supabase Auth (managed)
- Clear documentation
- Migration guide for users

---

## 📊 Comparison: Supabase vs Self-Hosted

| Feature | Supabase | Self-Hosted PostgreSQL |
|---------|----------|------------------------|
| **Setup Time** | 5 minutes | 1-2 hours |
| **Auth** | Built-in | Need to implement |
| **RLS** | Built-in | Need to implement |
| **Scalability** | Auto-scaling | Manual scaling |
| **Maintenance** | Managed | Self-maintained |
| **Cost** | Free tier, then $25/mo | Server costs |
| **Control** | Less control | Full control |
| **Vendor Lock-in** | Some | None |
| **Best For** | Most use cases | Enterprise, on-premise |

---

## 🎯 Recommendation

### **Use Supabase** for:
- ✅ Faster development
- ✅ Built-in auth
- ✅ Row Level Security
- ✅ Managed infrastructure
- ✅ Free tier for development
- ✅ Easy scaling

### **Consider Self-Hosted** if:
- ❌ Need on-premise deployment
- ❌ Have strict compliance requirements
- ❌ Want full control
- ❌ Have dedicated DevOps team

---

## 📝 Next Steps

1. **Review this plan** - Make sure it aligns with your goals
2. **Set up Supabase** - Create account and project
3. **Design schema** - Finalize table structure
4. **Create migration script** - Export existing data
5. **Implement database layer** - Start with workflows
6. **Add authentication** - Integrate Supabase Auth
7. **Implement RBAC** - Add roles and permissions
8. **Test thoroughly** - Before cutover
9. **Migrate data** - Run migration script
10. **Cutover** - Switch to database

---

## 🤔 Questions to Consider

1. **Do you need on-premise deployment?**
   - If yes → Self-hosted PostgreSQL
   - If no → Supabase

2. **What's your timeline?**
   - Fast → Supabase (built-in auth)
   - Flexible → Either works

3. **What's your team size?**
   - Small → Supabase (less maintenance)
   - Large → Either works

4. **What's your budget?**
   - Limited → Supabase free tier
   - Flexible → Either works

---

**Ready to proceed? Let me know your preferences and I'll start implementing!** 🚀

