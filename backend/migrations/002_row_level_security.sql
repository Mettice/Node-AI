-- Migration: Row Level Security (RLS) Policies
-- Description: Enables RLS and creates policies for all tables
-- Created: 2025-01-XX

-- ============================================
-- Enable Row Level Security
-- ============================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE secrets_vault ENABLE ROW LEVEL SECURITY;
ALTER TABLE secret_access_log ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Profiles Policies
-- ============================================
-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

-- ============================================
-- Workflows Policies
-- ============================================
-- Users can view their own workflows
CREATE POLICY "Users can view own workflows"
    ON workflows FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view shared workflows
CREATE POLICY "Users can view shared workflows"
    ON workflows FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM workflow_shares
            WHERE workflow_shares.workflow_id = workflows.id
            AND workflow_shares.shared_with_user_id = auth.uid()
        )
    );

-- Admins can view all workflows
CREATE POLICY "Admins can view all workflows"
    ON workflows FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Users can create their own workflows
CREATE POLICY "Users can create own workflows"
    ON workflows FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own workflows
CREATE POLICY "Users can update own workflows"
    ON workflows FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own workflows
CREATE POLICY "Users can delete own workflows"
    ON workflows FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- API Keys Policies
-- ============================================
-- Users can manage their own API keys
CREATE POLICY "Users can manage own API keys"
    ON api_keys FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- Deployments Policies
-- ============================================
-- Users can view their own deployments
CREATE POLICY "Users can view own deployments"
    ON deployments FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create deployments for their workflows
CREATE POLICY "Users can create own deployments"
    ON deployments FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own deployments
CREATE POLICY "Users can update own deployments"
    ON deployments FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================
-- Knowledge Bases Policies
-- ============================================
-- Users can manage their own knowledge bases
CREATE POLICY "Users can manage own knowledge bases"
    ON knowledge_bases FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- Webhooks Policies
-- ============================================
-- Users can manage their own webhooks
CREATE POLICY "Users can manage own webhooks"
    ON webhooks FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- Workflow Shares Policies
-- ============================================
-- Users can view shares for workflows they own or are shared with
CREATE POLICY "Users can view relevant shares"
    ON workflow_shares FOR SELECT
    USING (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
        OR shared_with_user_id = auth.uid()
    );

-- Users can create shares for workflows they own
CREATE POLICY "Users can share own workflows"
    ON workflow_shares FOR INSERT
    WITH CHECK (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
        AND shared_by = auth.uid()
    );

-- Users can update shares for workflows they own
CREATE POLICY "Users can update own workflow shares"
    ON workflow_shares FOR UPDATE
    USING (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );

-- Users can delete shares for workflows they own
CREATE POLICY "Users can delete own workflow shares"
    ON workflow_shares FOR DELETE
    USING (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );

-- ============================================
-- Secrets Vault Policies
-- ============================================
-- Users can manage their own secrets
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

-- ============================================
-- Secret Access Log Policies
-- ============================================
-- Users can view access logs for their own secrets
CREATE POLICY "Users can view own secret access logs"
    ON secret_access_log FOR SELECT
    USING (
        secret_id IN (
            SELECT id FROM secrets_vault WHERE user_id = auth.uid()
        )
    );

