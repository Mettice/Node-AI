# Authentication & RBAC Implementation Plan

**Strategic plan for user authentication, authorization, and role-based access control**

---

## 🎯 Goals

1. **Multi-user support** - Each user has isolated resources
2. **Secure authentication** - Email/password, OAuth options
3. **Role-based access** - Admin, User, Viewer roles
4. **Resource sharing** - Share workflows between users
5. **API key scoping** - API keys tied to users

---

## 🔐 Authentication Strategy

### Recommended: Supabase Auth ✅

**Why Supabase Auth?**

1. **Built-in Features:**
   - Email/password authentication
   - OAuth providers (Google, GitHub, etc.)
   - Magic links (passwordless)
   - Email verification
   - Password reset
   - Session management
   - JWT tokens

2. **Security:**
   - Industry-standard security
   - Password hashing (bcrypt)
   - Rate limiting
   - Email verification
   - Session management

3. **Developer Experience:**
   - Simple integration
   - TypeScript SDK
   - React hooks
   - Auto-generated types

### Alternative: Custom JWT Auth

**When to use:**
- Need full control
- On-premise deployment
- Custom requirements

**Implementation complexity:** High (need to build everything)

---

## 👥 User Roles & Permissions

### Role Definitions

#### 1. **Admin**
- **Full system access**
- Manage all users
- System settings
- View all resources
- Billing management

**Permissions:**
- ✅ Create/Read/Update/Delete all workflows
- ✅ Deploy any workflow
- ✅ Manage all API keys
- ✅ View all usage data
- ✅ Manage users and roles
- ✅ System configuration

#### 2. **User** (Default)
- **Standard user access**
- Manage own resources
- Deploy own workflows
- Create API keys

**Permissions:**
- ✅ Create/Read/Update/Delete own workflows
- ✅ Deploy own workflows
- ✅ Create/Manage own API keys
- ✅ View own usage data
- ✅ Share workflows with others
- ❌ Cannot access other users' resources
- ❌ Cannot manage users

#### 3. **Viewer**
- **Read-only access**
- View shared resources
- No modifications

**Permissions:**
- ✅ View own workflows (read-only)
- ✅ View shared workflows (read-only)
- ✅ View own usage data
- ❌ Cannot create/modify workflows
- ❌ Cannot deploy
- ❌ Cannot create API keys

### Permission Matrix

| Action | Admin | User | Viewer |
|--------|-------|------|--------|
| Create Workflow | ✅ All | ✅ Own | ❌ |
| Read Workflow | ✅ All | ✅ Own + Shared | ✅ Own + Shared |
| Update Workflow | ✅ All | ✅ Own | ❌ |
| Delete Workflow | ✅ All | ✅ Own | ❌ |
| Deploy Workflow | ✅ All | ✅ Own | ❌ |
| Create API Key | ✅ All | ✅ Own | ❌ |
| View Usage | ✅ All | ✅ Own | ✅ Own |
| Share Workflow | ✅ All | ✅ Own | ❌ |
| Manage Users | ✅ | ❌ | ❌ |
| System Settings | ✅ | ❌ | ❌ |

---

## 🏗️ Architecture Design

### User Flow

```
1. User Registration/Login
   ↓
2. JWT Token Generated
   ↓
3. Token Sent with Requests
   ↓
4. Backend Verifies Token
   ↓
5. Extract User ID & Role
   ↓
6. Apply RLS Policies
   ↓
7. Return Filtered Data
```

### Database Schema (Supabase)

```sql
-- User Profiles (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'user', -- 'admin', 'user', 'viewer'
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer'))
);

-- Workflows (with user ownership)
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
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Sharing
CREATE TABLE workflow_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    permission TEXT NOT NULL DEFAULT 'read', -- 'read', 'write', 'deploy'
    shared_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(workflow_id, shared_with_user_id),
    CONSTRAINT valid_permission CHECK (permission IN ('read', 'write', 'deploy'))
);

-- API Keys (scoped to users)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    key_id TEXT UNIQUE NOT NULL,
    key_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    rate_limit INTEGER,
    cost_limit DECIMAL(10, 4),
    enabled BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Secrets Vault (for storing user API keys and integration secrets)
-- See SECRETS_VAULT_STRATEGY.md for full schema
```

### Row Level Security (RLS) Policies

```sql
-- Enable RLS
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_shares ENABLE ROW LEVEL SECURITY;

-- Workflows: Users see own + shared
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

CREATE POLICY "Admins can view all workflows"
    ON workflows FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Workflows: Users can create/update/delete own
CREATE POLICY "Users can manage own workflows"
    ON workflows FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- API Keys: Users manage own
CREATE POLICY "Users can manage own API keys"
    ON api_keys FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
```

---

## 📋 Implementation Phases

### Phase 1: Database Setup (Week 1)

**Tasks:**
1. Set up Supabase project
2. Create database schema
3. Set up RLS policies
4. Create migration scripts
5. Test database connection

**Deliverables:**
- ✅ Supabase project configured
- ✅ Database schema created
- ✅ RLS policies active
- ✅ Connection tested

### Phase 2: Authentication (Week 1-2)

**Frontend:**
1. Install `@supabase/supabase-js`
2. Create auth context/provider
3. Add login/register UI
4. Add protected routes
5. Add user profile UI

**Backend:**
1. Install `supabase-py` or verify JWT
2. Create auth middleware
3. Extract user from JWT
4. Add user context to requests
5. Update API endpoints

**Deliverables:**
- ✅ Users can register/login
- ✅ JWT tokens working
- ✅ Protected routes
- ✅ User context in backend

### Phase 3: User Scoping (Week 2)

**Tasks:**
1. Add `user_id` to all resources
2. Update queries to filter by user
3. Migrate existing data (assign to admin)
4. Test user isolation
5. Update API endpoints

**Deliverables:**
- ✅ All resources scoped to users
- ✅ Users see only their resources
- ✅ Existing data migrated

### Phase 4: RBAC (Week 2-3)

**Tasks:**
1. Implement role checks
2. Add permission middleware
3. Update UI based on role
4. Add role management (admin only)
5. Test all permission scenarios

**Deliverables:**
- ✅ Roles working
- ✅ Permissions enforced
- ✅ Role-based UI

### Phase 5: Sharing (Week 3)

**Tasks:**
1. Implement workflow sharing
2. Add share UI
3. Update queries for shared resources
4. Test sharing scenarios
5. Add share notifications

**Deliverables:**
- ✅ Workflows can be shared
- ✅ Shared workflows visible
- ✅ Permission levels working

### Phase 6: Migration & Testing (Week 3-4)

**Tasks:**
1. Migrate all existing data
2. Comprehensive testing
3. Performance testing
4. Security audit
5. Documentation

**Deliverables:**
- ✅ All data migrated
- ✅ Tests passing
- ✅ Performance validated
- ✅ Documentation complete

---

## 🔄 Migration Strategy

### Data Migration Plan

#### Step 1: Export Existing Data

```python
# Migration script
def export_workflows():
    """Export all workflows from files."""
    workflows = []
    for file in WORKFLOWS_DIR.glob("*.json"):
        with open(file) as f:
            workflows.append(json.load(f))
    return workflows
```

#### Step 2: Create Default Admin User

```python
# Create admin user in Supabase
admin_user = create_user(
    email="admin@nodai.io",
    password="secure-password",
    role="admin"
)
```

#### Step 3: Migrate Data

```python
# Assign all existing workflows to admin
for workflow in workflows:
    workflow["user_id"] = admin_user.id
    insert_workflow(workflow)
```

#### Step 4: Validate

```python
# Verify data integrity
assert count_workflows() == len(exported_workflows)
```

### Dual-Write Pattern

During migration, write to both:

```python
def save_workflow(workflow):
    # Write to database
    db.save_workflow(workflow)
    
    # Also write to file (backup)
    file.save_workflow(workflow)
    
    # Log for validation
    log_dual_write(workflow.id)
```

---

## 🛡️ Security Considerations

### Authentication Security

1. **Password Requirements:**
   - Minimum 8 characters
   - Require uppercase, lowercase, number
   - Password strength indicator

2. **Session Management:**
   - JWT expiration (7 days)
   - Refresh tokens
   - Logout on all devices

3. **Rate Limiting:**
   - Login attempts: 5 per 15 minutes
   - Registration: 3 per hour
   - API requests: Per API key

### Authorization Security

1. **RLS Policies:**
   - Enforced at database level
   - Cannot be bypassed
   - Tested thoroughly

2. **API Key Scoping:**
   - Keys tied to users
   - Can only access user's resources
   - Revocable

3. **Resource Sharing:**
   - Explicit sharing required
   - Permission levels
   - Audit trail

---

## 📊 Comparison: Supabase vs Custom Auth

| Feature | Supabase Auth | Custom JWT |
|---------|---------------|------------|
| **Setup Time** | 1 hour | 1-2 weeks |
| **Email/Password** | ✅ Built-in | ❌ Need to build |
| **OAuth** | ✅ Built-in | ❌ Need to build |
| **Magic Links** | ✅ Built-in | ❌ Need to build |
| **Email Verification** | ✅ Built-in | ❌ Need to build |
| **Password Reset** | ✅ Built-in | ❌ Need to build |
| **Session Management** | ✅ Built-in | ❌ Need to build |
| **Security** | ✅ Managed | ⚠️ Your responsibility |
| **Maintenance** | ✅ None | ❌ Ongoing |
| **Cost** | Free tier | Server costs |
| **Control** | Less | Full |

**Recommendation:** Use Supabase Auth unless you have specific requirements.

---

## 🎯 Implementation Checklist

### Database Setup
- [ ] Create Supabase project
- [ ] Design schema
- [ ] Create tables
- [ ] Set up RLS policies
- [ ] Create indexes
- [ ] Test queries

### Authentication
- [ ] Install Supabase client
- [ ] Create auth context
- [ ] Add login UI
- [ ] Add register UI
- [ ] Add logout
- [ ] Add password reset
- [ ] Add email verification
- [ ] Backend JWT verification
- [ ] Protected routes

### User Scoping
- [ ] Add user_id to workflows
- [ ] Add user_id to API keys
- [ ] Add user_id to deployments
- [ ] Add user_id to knowledge bases
- [ ] Add user_id to webhooks
- [ ] Update all queries
- [ ] Test isolation

### RBAC
- [ ] Add role to profiles
- [ ] Create permission checks
- [ ] Update API endpoints
- [ ] Add role-based UI
- [ ] Add role management (admin)
- [ ] Test all roles

### Sharing
- [ ] Create workflow_shares table
- [ ] Add share API endpoints
- [ ] Add share UI
- [ ] Update queries for shared
- [ ] Test sharing

### Migration
- [ ] Export existing data
- [ ] Create admin user
- [ ] Migrate workflows
- [ ] Migrate API keys
- [ ] Migrate deployments
- [ ] Validate data
- [ ] Test system

---

## 🚀 Recommended Approach

### **Use Supabase** for:

1. **Database:** PostgreSQL with RLS
2. **Authentication:** Supabase Auth
3. **Storage:** Supabase Storage (for files)
4. **Real-time:** Supabase Realtime (future feature)

### **Implementation Order:**

1. **Week 1:** Database setup + Auth
2. **Week 2:** User scoping + RBAC
3. **Week 3:** Sharing + Migration
4. **Week 4:** Testing + Polish

### **Why This Works:**

- ✅ Fast development (built-in features)
- ✅ Secure (managed security)
- ✅ Scalable (auto-scaling)
- ✅ Cost-effective (free tier)
- ✅ Well-documented
- ✅ Active community

---

## ⚠️ Risks & Mitigation

### Risk 1: Data Loss
**Mitigation:**
- Dual-write during migration
- Comprehensive backups
- Rollback plan
- Data validation

### Risk 2: Breaking Changes
**Mitigation:**
- Feature flags
- Gradual rollout
- Backward compatibility
- Extensive testing

### Risk 3: Vendor Lock-in
**Mitigation:**
- Use standard PostgreSQL
- Can migrate to self-hosted
- Export data anytime
- Open source client

### Risk 4: Performance
**Mitigation:**
- Connection pooling
- Proper indexing
- Query optimization
- Load testing

---

## 📝 Next Steps

1. **Review this plan** - Confirm approach
2. **Set up Supabase** - Create account
3. **Design schema** - Finalize tables
4. **Start Phase 1** - Database setup
5. **Iterate** - Build incrementally

---

**Ready to start? Let me know and I'll begin with Phase 1!** 🚀

