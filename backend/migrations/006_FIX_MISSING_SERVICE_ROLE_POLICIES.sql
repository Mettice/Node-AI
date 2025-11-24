-- ============================================
-- FIX MISSING SERVICE ROLE POLICIES
-- ============================================
-- This script adds service role policies for backend operations
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- 1. TRACES - Add Service Role Policy
-- ============================================
-- Drop existing service role policy if it exists
DROP POLICY IF EXISTS "Service role can manage all traces" ON traces;

-- Create service role policy for traces
CREATE POLICY "Service role can manage all traces"
    ON traces FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================
-- 2. SPANS - Add Service Role Policy
-- ============================================
-- Drop existing service role policy if it exists
DROP POLICY IF EXISTS "Service role can manage all spans" ON spans;

-- Create service role policy for spans
CREATE POLICY "Service role can manage all spans"
    ON spans FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================
-- 3. USAGE_LOGS - Enable RLS and Add Policies
-- ============================================
-- Enable RLS
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own usage_logs" ON usage_logs;
DROP POLICY IF EXISTS "Service role can manage all usage_logs" ON usage_logs;

-- Users can view their own usage logs
CREATE POLICY "Users can view own usage_logs"
    ON usage_logs FOR SELECT
    USING (auth.uid() = user_id);

-- Service role can manage all usage logs (for backend operations)
CREATE POLICY "Service role can manage all usage_logs"
    ON usage_logs FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================
-- 4. VERIFY SECRETS_VAULT POLICIES
-- ============================================
-- Check if secrets_vault policies allow service role
-- If not, we'll recreate them

-- First, check the current policies
DO $$
BEGIN
    -- Check if secrets_select_policy allows service role
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'secrets_vault' 
        AND policyname = 'secrets_select_policy'
        AND (qual::text LIKE '%service_role%' OR with_check::text LIKE '%service_role%')
    ) THEN
        -- Recreate the policy to ensure service role access
        DROP POLICY IF EXISTS "secrets_select_policy" ON secrets_vault;
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
    END IF;
END $$;

-- ============================================
-- 5. ADD SERVICE ROLE POLICIES TO OTHER TABLES
-- ============================================

-- WORKFLOWS - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all workflows" ON workflows;
CREATE POLICY "Service role can manage all workflows"
    ON workflows FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- PROFILES - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all profiles" ON profiles;
CREATE POLICY "Service role can manage all profiles"
    ON profiles FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- API_KEYS - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all api_keys" ON api_keys;
CREATE POLICY "Service role can manage all api_keys"
    ON api_keys FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- DEPLOYMENTS - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all deployments" ON deployments;
CREATE POLICY "Service role can manage all deployments"
    ON deployments FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- KNOWLEDGE_BASES - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all knowledge_bases" ON knowledge_bases;
CREATE POLICY "Service role can manage all knowledge_bases"
    ON knowledge_bases FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- WEBHOOKS - Add service role policy
DROP POLICY IF EXISTS "Service role can manage all webhooks" ON webhooks;
CREATE POLICY "Service role can manage all webhooks"
    ON webhooks FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check all tables have service role policies
SELECT 
    tablename,
    policyname,
    cmd,
    CASE 
        WHEN qual::text LIKE '%service_role%' OR with_check::text LIKE '%service_role%' 
        THEN 'YES' 
        ELSE 'NO' 
    END as has_service_role_access
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('traces', 'spans', 'secrets_vault', 'workflows', 'profiles', 'api_keys', 'deployments', 'knowledge_bases', 'webhooks', 'usage_logs')
ORDER BY tablename, policyname;

-- Check RLS is enabled on all tables
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('traces', 'spans', 'secrets_vault', 'workflows', 'profiles', 'api_keys', 'deployments', 'knowledge_bases', 'webhooks', 'usage_logs')
ORDER BY tablename;

