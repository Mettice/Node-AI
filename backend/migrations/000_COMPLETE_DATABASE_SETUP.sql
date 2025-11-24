-- ============================================
-- COMPLETE DATABASE SETUP FOR PRODUCTION
-- ============================================
-- This script ensures ALL tables, indexes, RLS policies, and relationships are created
-- Run this in your Supabase SQL editor to set up the complete database
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. USER PROFILES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    avatar_url TEXT,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer'))
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);

-- Enable RLS on profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Public profiles are viewable by everyone" ON profiles;
DROP POLICY IF EXISTS "Service role can manage all profiles" ON profiles;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Public profiles are viewable by everyone"
    ON profiles FOR SELECT
    USING (true);

CREATE POLICY "Service role can manage all profiles"
    ON profiles FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 2. WORKFLOWS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS workflows (
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

CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_deployed ON workflows(is_deployed);
CREATE INDEX IF NOT EXISTS idx_workflows_template ON workflows(is_template);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at);

-- Enable RLS on workflows
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own workflows" ON workflows;
DROP POLICY IF EXISTS "Users can create own workflows" ON workflows;
DROP POLICY IF EXISTS "Users can update own workflows" ON workflows;
DROP POLICY IF EXISTS "Users can delete own workflows" ON workflows;
DROP POLICY IF EXISTS "Service role can manage all workflows" ON workflows;

-- RLS Policies for workflows
CREATE POLICY "Users can view own workflows"
    ON workflows FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own workflows"
    ON workflows FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workflows"
    ON workflows FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workflows"
    ON workflows FOR DELETE
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all workflows"
    ON workflows FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 3. SECRETS VAULT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS secrets_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Identification
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    secret_type TEXT NOT NULL,
    
    -- Encrypted Value
    encrypted_value TEXT NOT NULL,
    encryption_key_id TEXT NOT NULL DEFAULT 'v1',
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage Tracking
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_in_workflow UUID REFERENCES workflows(id),
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, provider, secret_type)
);

CREATE INDEX IF NOT EXISTS idx_secrets_user_id ON secrets_vault(user_id);
CREATE INDEX IF NOT EXISTS idx_secrets_provider ON secrets_vault(provider);
CREATE INDEX IF NOT EXISTS idx_secrets_type ON secrets_vault(secret_type);
CREATE INDEX IF NOT EXISTS idx_secrets_active ON secrets_vault(is_active);
CREATE INDEX IF NOT EXISTS idx_secrets_user_provider ON secrets_vault(user_id, provider);

-- Enable RLS on secrets_vault
ALTER TABLE secrets_vault ENABLE ROW LEVEL SECURITY;

-- Drop ALL existing policies for secrets_vault
DROP POLICY IF EXISTS "Users can manage own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Admins can view all secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can create own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can view own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can update own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can delete own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Service role can insert secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Service role can select secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Service role can update secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Service role can delete secrets" ON secrets_vault;
DROP POLICY IF EXISTS "secrets_insert_policy" ON secrets_vault;
DROP POLICY IF EXISTS "secrets_select_policy" ON secrets_vault;
DROP POLICY IF EXISTS "secrets_update_policy" ON secrets_vault;
DROP POLICY IF EXISTS "secrets_delete_policy" ON secrets_vault;

-- RLS Policies for secrets_vault (CRITICAL - must allow service role)
CREATE POLICY "secrets_insert_policy"
    ON secrets_vault FOR INSERT
    WITH CHECK (
        auth.role() = 'service_role'
        OR
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

CREATE POLICY "secrets_select_policy"
    ON secrets_vault FOR SELECT
    USING (
        auth.role() = 'service_role'
        OR
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
        OR
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

CREATE POLICY "secrets_update_policy"
    ON secrets_vault FOR UPDATE
    USING (
        auth.role() = 'service_role'
        OR
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

CREATE POLICY "secrets_delete_policy"
    ON secrets_vault FOR DELETE
    USING (
        auth.role() = 'service_role'
        OR
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

-- ============================================
-- 4. TRACES TABLE (Observability)
-- ============================================
CREATE TABLE IF NOT EXISTS traces (
    trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    query TEXT,
    
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_duration_ms INTEGER DEFAULT 0,
    
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    error TEXT,
    
    total_cost DECIMAL(10, 6) DEFAULT 0.0,
    total_tokens JSONB DEFAULT '{}'::jsonb,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_traces_workflow_id ON traces(workflow_id);
CREATE INDEX IF NOT EXISTS idx_traces_execution_id ON traces(execution_id);
CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces(user_id);
CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_workflow_started ON traces(workflow_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_metadata_gin ON traces USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_traces_total_tokens_gin ON traces USING GIN (total_tokens);

-- Enable RLS on traces
ALTER TABLE traces ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own traces" ON traces;
DROP POLICY IF EXISTS "Users can insert their own traces" ON traces;
DROP POLICY IF EXISTS "Users can update their own traces" ON traces;
DROP POLICY IF EXISTS "Admins can view all traces" ON traces;
DROP POLICY IF EXISTS "Service role can manage all traces" ON traces;

-- RLS Policies for traces
CREATE POLICY "Users can view their own traces"
    ON traces FOR SELECT
    USING (
        user_id = auth.uid()
        OR user_id IS NULL
        OR auth.role() = 'service_role'
    );

CREATE POLICY "Users can insert their own traces"
    ON traces FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        OR user_id IS NULL
        OR auth.role() = 'service_role'
    );

CREATE POLICY "Users can update their own traces"
    ON traces FOR UPDATE
    USING (
        user_id = auth.uid()
        OR user_id IS NULL
        OR auth.role() = 'service_role'
    );

CREATE POLICY "Service role can manage all traces"
    ON traces FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 5. SPANS TABLE (Observability)
-- ============================================
CREATE TABLE IF NOT EXISTS spans (
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    parent_span_id UUID REFERENCES spans(span_id) ON DELETE SET NULL,
    
    span_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER DEFAULT 0,
    
    inputs JSONB DEFAULT '{}'::jsonb,
    outputs JSONB DEFAULT '{}'::jsonb,
    
    tokens JSONB DEFAULT '{}'::jsonb,
    cost DECIMAL(10, 6) DEFAULT 0.0,
    model VARCHAR(255),
    provider VARCHAR(100),
    
    error TEXT,
    error_type VARCHAR(100),
    error_stack TEXT,
    
    api_limits JSONB DEFAULT '{}'::jsonb,
    retry_count INTEGER DEFAULT 0,
    timeout INTEGER,
    
    evaluation JSONB DEFAULT '{}'::jsonb,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    
    child_spans TEXT[] DEFAULT '{}',
    
    CONSTRAINT valid_span_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_span_type ON spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_status ON spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_started_at ON spans(started_at);
CREATE INDEX IF NOT EXISTS idx_spans_trace_started ON spans(trace_id, started_at);
CREATE INDEX IF NOT EXISTS idx_spans_tokens_gin ON spans USING GIN (tokens);
CREATE INDEX IF NOT EXISTS idx_spans_metadata_gin ON spans USING GIN (metadata);

-- Enable RLS on spans
ALTER TABLE spans ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view spans from their own traces" ON spans;
DROP POLICY IF EXISTS "Users can insert spans to their own traces" ON spans;
DROP POLICY IF EXISTS "Users can update spans in their own traces" ON spans;
DROP POLICY IF EXISTS "Admins can view all spans" ON spans;
DROP POLICY IF EXISTS "Service role can manage all spans" ON spans;

-- RLS Policies for spans
CREATE POLICY "Users can view spans from their own traces"
    ON spans FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid()
                OR traces.user_id IS NULL
                OR auth.role() = 'service_role'
            )
        )
    );

CREATE POLICY "Users can insert spans to their own traces"
    ON spans FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid()
                OR traces.user_id IS NULL
                OR auth.role() = 'service_role'
            )
        )
    );

CREATE POLICY "Users can update spans in their own traces"
    ON spans FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid()
                OR traces.user_id IS NULL
                OR auth.role() = 'service_role'
            )
        )
    );

CREATE POLICY "Service role can manage all spans"
    ON spans FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- 6. OTHER TABLES (API Keys, Deployments, etc.)
-- ============================================

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
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

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_enabled ON api_keys(enabled);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own api_keys" ON api_keys;
DROP POLICY IF EXISTS "Service role can manage all api_keys" ON api_keys;

CREATE POLICY "Users can manage own api_keys"
    ON api_keys FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all api_keys"
    ON api_keys FOR ALL
    USING (auth.role() = 'service_role');

-- Deployments
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id),
    version_number INTEGER NOT NULL,
    workflow_snapshot JSONB NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    deployed_at TIMESTAMP DEFAULT NOW(),
    deployed_by UUID REFERENCES profiles(id),
    
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    failed_queries INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10, 2) DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    
    UNIQUE(workflow_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_deployments_workflow ON deployments(workflow_id);
CREATE INDEX IF NOT EXISTS idx_deployments_user ON deployments(user_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);

ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own deployments" ON deployments;
DROP POLICY IF EXISTS "Service role can manage all deployments" ON deployments;

CREATE POLICY "Users can manage own deployments"
    ON deployments FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all deployments"
    ON deployments FOR ALL
    USING (auth.role() = 'service_role');

-- Knowledge Bases
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    file_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_user_id ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_status ON knowledge_bases(status);

ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own knowledge_bases" ON knowledge_bases;
DROP POLICY IF EXISTS "Service role can manage all knowledge_bases" ON knowledge_bases;

CREATE POLICY "Users can manage own knowledge_bases"
    ON knowledge_bases FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all knowledge_bases"
    ON knowledge_bases FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify everything is set up correctly:

-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans', 'api_keys', 'deployments', 'knowledge_bases')
ORDER BY table_name;

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans', 'api_keys', 'deployments', 'knowledge_bases')
ORDER BY tablename;

-- Check policies exist for secrets_vault
SELECT policyname, cmd, permissive, roles, qual, with_check
FROM pg_policies 
WHERE tablename = 'secrets_vault'
ORDER BY policyname;

-- Check indexes exist
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans')
ORDER BY tablename, indexname;

