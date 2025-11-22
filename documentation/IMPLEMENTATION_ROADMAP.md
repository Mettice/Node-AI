# Implementation Roadmap: Database, Auth & RBAC

**Step-by-step implementation guide with timelines and dependencies**

---

## 📅 Timeline Overview

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 1: Database Setup** | 3-5 days | ⏳ Pending |
| **Phase 2: Authentication** | 5-7 days | ⏳ Pending |
| **Phase 3: User Scoping** | 3-5 days | ⏳ Pending |
| **Phase 4: RBAC** | 3-5 days | ⏳ Pending |
| **Phase 5: Sharing** | 2-3 days | ⏳ Pending |
| **Phase 6: Migration** | 3-5 days | ⏳ Pending |
| **Total** | **3-4 weeks** | |

---

## 🗄️ Phase 1: Database Setup

### Day 1: Supabase Project Setup

**Tasks:**
1. Create Supabase account
2. Create new project
3. Get connection strings
4. Install dependencies

**Dependencies:**
```bash
pip install supabase psycopg2-binary sqlalchemy
```

**Deliverables:**
- ✅ Supabase project created
- ✅ Connection tested
- ✅ Environment variables configured

### Day 2-3: Schema Design & Creation

**Tasks:**
1. Design database schema
2. Create migration files
3. Run migrations
4. Create indexes
5. Set up RLS policies

**Files to Create:**
- `backend/core/database.py` - Database connection
- `backend/core/models_db.py` - SQLAlchemy models (optional)
- `backend/migrations/` - Migration files

**Deliverables:**
- ✅ All tables created
- ✅ Indexes created
- ✅ RLS policies active

### Day 4-5: Database Layer

**Tasks:**
1. Create database abstraction layer
2. Implement CRUD operations
3. Add connection pooling
4. Test database operations

**Files to Create:**
- `backend/core/db_workflows.py` - Workflow DB operations
- `backend/core/db_api_keys.py` - API key DB operations
- `backend/core/db_deployments.py` - Deployment DB operations

**Deliverables:**
- ✅ Database layer implemented
- ✅ CRUD operations working
- ✅ Connection pooling configured

---

## 🔐 Phase 2: Authentication

### Day 1-2: Frontend Auth Setup

**Tasks:**
1. Install Supabase client
2. Create auth context
3. Add login/register UI
4. Add protected routes

**Files to Create:**
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/components/Auth/LoginForm.tsx`
- `frontend/src/components/Auth/RegisterForm.tsx`
- `frontend/src/components/Auth/ProtectedRoute.tsx`

**Dependencies:**
```bash
npm install @supabase/supabase-js
```

**Deliverables:**
- ✅ Users can register
- ✅ Users can login
- ✅ Protected routes working

### Day 3-4: Backend Auth Integration

**Tasks:**
1. Install Supabase Python client
2. Create auth middleware
3. Verify JWT tokens
4. Extract user context
5. Update API endpoints

**Files to Create:**
- `backend/core/auth_middleware.py` - JWT verification
- `backend/core/user_context.py` - User context management

**Dependencies:**
```bash
pip install supabase python-jose
```

**Deliverables:**
- ✅ JWT verification working
- ✅ User context in requests
- ✅ Protected endpoints

### Day 5-7: Auth Features

**Tasks:**
1. Password reset flow
2. Email verification
3. Profile management
4. Session management
5. OAuth providers (optional)

**Deliverables:**
- ✅ Complete auth flow
- ✅ Profile management
- ✅ Session handling

---

## 👤 Phase 3: User Scoping

### Day 1-2: Add User ID to Resources

**Tasks:**
1. Update workflow model (add user_id)
2. Update API key model (add user_id)
3. Update deployment model (add user_id)
4. Update knowledge base model (add user_id)
5. Update webhook model (add user_id)
6. Create secrets vault schema (add user_id)

**Files to Modify:**
- `backend/core/models.py` - Add user_id fields
- `backend/api/workflows.py` - Filter by user_id
- `backend/api/api_keys.py` - Filter by user_id
- All other API endpoints

**Deliverables:**
- ✅ All models have user_id
- ✅ Queries filter by user_id

### Day 3-4: Update API Endpoints

**Tasks:**
1. Add user context to all endpoints
2. Filter queries by user_id
3. Validate ownership
4. Update error messages

**Files to Modify:**
- All API endpoint files
- Add user context extraction
- Add ownership checks

**Deliverables:**
- ✅ All endpoints scoped to users
- ✅ Users see only their resources

### Day 5: Data Migration

**Tasks:**
1. Create migration script
2. Export existing data
3. Create admin user
4. Assign data to admin
5. Validate migration

**Files to Create:**
- `backend/scripts/migrate_to_db.py`

**Deliverables:**
- ✅ Existing data migrated
- ✅ All workflows assigned to admin

---

## 🔐 Phase 3.5: Secrets Vault (Week 2)

### Day 1-2: Secrets Vault Backend

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

**Deliverables:**
- ✅ Secrets vault backend working
- ✅ Encryption/decryption working
- ✅ Audit logging working

### Day 3-4: Secrets Vault Frontend

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

**Deliverables:**
- ✅ Secrets vault UI in Settings
- ✅ Users can add/edit secrets
- ✅ Connection testing working

### Day 5: Integration

**Tasks:**
1. Update nodes to use user secrets
2. Add secret selection in node configs
3. Decrypt secrets on-demand
4. Update all LLM nodes
5. Update integration nodes

**Deliverables:**
- ✅ Nodes use secrets from vault
- ✅ Secret selection in node configs

---

## 🛡️ Phase 4: RBAC

### Day 1-2: Role Management

**Tasks:**
1. Add role to user profiles
2. Create role enum
3. Add role checks
4. Create permission helper functions

**Files to Create:**
- `backend/core/permissions.py` - Permission checks
- `backend/core/roles.py` - Role definitions

**Deliverables:**
- ✅ Roles defined
- ✅ Permission checks working

### Day 3-4: Permission Enforcement

**Tasks:**
1. Add permission middleware
2. Update API endpoints with permission checks
3. Add role-based UI
4. Test all permission scenarios

**Files to Modify:**
- All API endpoints
- Frontend components

**Deliverables:**
- ✅ Permissions enforced
- ✅ Role-based UI

### Day 5: Admin Features

**Tasks:**
1. User management UI (admin only)
2. Role assignment
3. System settings
4. Admin dashboard

**Deliverables:**
- ✅ Admin can manage users
- ✅ Role assignment working

---

## 🤝 Phase 5: Sharing

### Day 1-2: Sharing Backend

**Tasks:**
1. Create workflow_shares table
2. Add share API endpoints
3. Update queries for shared resources
4. Test sharing logic

**Files to Create:**
- `backend/api/sharing.py` - Share endpoints
- `backend/core/db_sharing.py` - Share DB operations

**Deliverables:**
- ✅ Sharing API working
- ✅ Shared resources visible

### Day 3: Sharing UI

**Tasks:**
1. Add share button to workflows
2. Share modal UI
3. Permission level selector
4. Share management UI

**Files to Create:**
- `frontend/src/components/Sharing/ShareWorkflowModal.tsx`
- `frontend/src/components/Sharing/ShareList.tsx`

**Deliverables:**
- ✅ Users can share workflows
- ✅ Share management UI

---

## 🔄 Phase 6: Migration & Testing

### Day 1-2: Data Migration

**Tasks:**
1. Final data export
2. Run migration script
3. Validate all data
4. Test all operations

**Deliverables:**
- ✅ All data migrated
- ✅ Data validated

### Day 3-4: Testing

**Tasks:**
1. Unit tests for auth
2. Integration tests for RBAC
3. E2E tests for user flows
4. Performance testing
5. Security testing

**Deliverables:**
- ✅ All tests passing
- ✅ Performance validated

### Day 5: Documentation & Cutover

**Tasks:**
1. Update documentation
2. Create migration guide
3. Cutover to database
4. Monitor for issues

**Deliverables:**
- ✅ Documentation updated
- ✅ System running on database

---

## 🛠️ Technical Stack Decision

### Recommended Stack

```
Database:     Supabase (PostgreSQL)
Auth:         Supabase Auth
ORM:          SQLAlchemy (optional) or raw SQL
Migrations:   Supabase Migrations or Alembic
Frontend:     @supabase/supabase-js
Backend:      supabase-py or python-jose
```

### Why This Stack?

1. **Supabase:**
   - ✅ Managed PostgreSQL
   - ✅ Built-in auth
   - ✅ Row Level Security
   - ✅ Free tier
   - ✅ Easy to use

2. **SQLAlchemy (Optional):**
   - ✅ ORM benefits
   - ✅ Type safety
   - ✅ Migration tools
   - ⚠️ Can use raw SQL if preferred

3. **Supabase Client:**
   - ✅ TypeScript support
   - ✅ React hooks
   - ✅ Auto-generated types

---

## 📋 Pre-Implementation Checklist

Before starting, ensure:

- [ ] Supabase account created
- [ ] Project created
- [ ] Connection strings obtained
- [ ] Environment variables configured
- [ ] Backup of existing data
- [ ] Test environment set up
- [ ] Team aligned on approach

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- ✅ Database schema created
- ✅ RLS policies working
- ✅ Database layer implemented
- ✅ Can read/write to database

### Phase 2 Complete When:
- ✅ Users can register/login
- ✅ JWT tokens working
- ✅ Protected routes working
- ✅ User context in backend

### Phase 3 Complete When:
- ✅ All resources scoped to users
- ✅ Users see only their resources
- ✅ Existing data migrated

### Phase 4 Complete When:
- ✅ Roles working
- ✅ Permissions enforced
- ✅ Admin can manage users

### Phase 5 Complete When:
- ✅ Workflows can be shared
- ✅ Shared workflows visible
- ✅ Permission levels working

### Phase 6 Complete When:
- ✅ All data migrated
- ✅ All tests passing
- ✅ System running on database
- ✅ Documentation complete

---

## 🚀 Ready to Start?

**Next Steps:**
1. Review and approve this plan
2. Set up Supabase project
3. Begin Phase 1: Database Setup

**I'm ready to implement when you are!** 🎉

