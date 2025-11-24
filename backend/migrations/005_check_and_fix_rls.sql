-- Migration: Check and fix RLS policies for secrets_vault
-- Description: Properly handle service role access regardless of previous migrations
-- Created: 2025-11-24

-- ============================================
-- Check existing policies (run this first to see what exists)
-- ============================================
SELECT schemaname, tablename, policyname, cmd, permissive, roles, qual, with_check
FROM pg_policies 
WHERE tablename = 'secrets_vault'
ORDER BY policyname;

-- ============================================
-- Drop ALL existing policies for secrets_vault (clean slate)
-- ============================================
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

-- ============================================
-- Create comprehensive new policies
-- ============================================

-- INSERT: Service role OR authenticated user for their own secrets
CREATE POLICY "secrets_insert_policy"
    ON secrets_vault FOR INSERT
    WITH CHECK (
        -- Service role can insert anything
        auth.role() = 'service_role'
        OR
        -- Authenticated users can insert their own secrets
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

-- SELECT: Service role OR users for their own secrets OR admins
CREATE POLICY "secrets_select_policy"
    ON secrets_vault FOR SELECT
    USING (
        -- Service role can select anything
        auth.role() = 'service_role'
        OR
        -- Users can select their own secrets
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
        OR
        -- Admins can select all secrets
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- UPDATE: Service role OR users for their own secrets
CREATE POLICY "secrets_update_policy"
    ON secrets_vault FOR UPDATE
    USING (
        -- Service role can update anything
        auth.role() = 'service_role'
        OR
        -- Users can update their own secrets
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

-- DELETE: Service role OR users for their own secrets
CREATE POLICY "secrets_delete_policy"
    ON secrets_vault FOR DELETE
    USING (
        -- Service role can delete anything
        auth.role() = 'service_role'
        OR
        -- Users can delete their own secrets
        (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    );

-- ============================================
-- Verify the new policies
-- ============================================
SELECT schemaname, tablename, policyname, cmd, permissive, roles, qual, with_check
FROM pg_policies 
WHERE tablename = 'secrets_vault'
ORDER BY policyname;