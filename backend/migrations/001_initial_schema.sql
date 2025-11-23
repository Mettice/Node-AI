-- Migration: Initial Database Schema
-- Description: Creates all tables for workflows, users, API keys, deployments, etc.
-- Created: 2025-01-XX

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- User Profiles (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'user', -- 'admin', 'user', 'viewer'
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer'))
);

-- ============================================
-- Workflows
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

-- ============================================
-- API Keys (for NodAI API access)
-- ============================================
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

-- ============================================
-- Usage Tracking
-- ============================================
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    execution_id TEXT,
    cost DECIMAL(10, 6) NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_api_key ON usage_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_workflow ON usage_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_logs(created_at);

-- ============================================
-- Deployments
-- ============================================
CREATE TABLE IF NOT EXISTS deployments (
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
    
    UNIQUE(workflow_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_deployments_workflow ON deployments(workflow_id);
CREATE INDEX IF NOT EXISTS idx_deployments_user ON deployments(user_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);

-- ============================================
-- Knowledge Bases
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    config JSONB NOT NULL, -- chunk_size, embed_model, etc.
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'ready', 'error'
    file_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_user_id ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_status ON knowledge_bases(status);

-- ============================================
-- Webhooks
-- ============================================
CREATE TABLE IF NOT EXISTS webhooks (
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
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhooks_workflow ON webhooks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_webhook_id ON webhooks(webhook_id);

-- ============================================
-- Workflow Sharing
-- ============================================
CREATE TABLE IF NOT EXISTS workflow_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    permission TEXT NOT NULL DEFAULT 'read', -- 'read', 'write', 'deploy'
    shared_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(workflow_id, shared_with_user_id),
    CONSTRAINT valid_permission CHECK (permission IN ('read', 'write', 'deploy'))
);

CREATE INDEX IF NOT EXISTS idx_shares_workflow ON workflow_shares(workflow_id);
CREATE INDEX IF NOT EXISTS idx_shares_user ON workflow_shares(shared_with_user_id);

-- ============================================
-- Secrets Vault
-- ============================================
CREATE TABLE IF NOT EXISTS secrets_vault (
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
    UNIQUE(user_id, provider, secret_type)
);

CREATE INDEX IF NOT EXISTS idx_secrets_user_id ON secrets_vault(user_id);
CREATE INDEX IF NOT EXISTS idx_secrets_provider ON secrets_vault(provider);
CREATE INDEX IF NOT EXISTS idx_secrets_type ON secrets_vault(secret_type);
CREATE INDEX IF NOT EXISTS idx_secrets_active ON secrets_vault(is_active);

-- ============================================
-- Secret Access Log (audit trail)
-- ============================================
CREATE TABLE IF NOT EXISTS secret_access_log (
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

CREATE INDEX IF NOT EXISTS idx_access_secret ON secret_access_log(secret_id);
CREATE INDEX IF NOT EXISTS idx_access_user ON secret_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_access_workflow ON secret_access_log(workflow_id);
CREATE INDEX IF NOT EXISTS idx_access_time ON secret_access_log(accessed_at);

