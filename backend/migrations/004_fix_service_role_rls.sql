-- Migration: Fix RLS for service role operations
-- Description: Allow service role to bypass RLS for secrets_vault operations
-- Created: 2025-11-24

-- ============================================
-- Add service role bypass policy for secrets_vault
-- ============================================

-- Add policy to allow service role to bypass RLS for INSERT operations
CREATE POLICY "Service role can insert secrets"
    ON secrets_vault FOR INSERT
    WITH CHECK (
        -- Allow if user is service role (has full access)
        auth.role() = 'service_role'
        OR
        -- Allow if user matches the user_id (normal user operation)
        auth.uid()::text = user_id::text
    );

-- Add policy to allow service role to bypass RLS for SELECT operations  
CREATE POLICY "Service role can select secrets"
    ON secrets_vault FOR SELECT
    USING (
        -- Allow if user is service role (has full access)
        auth.role() = 'service_role'
        OR
        -- Allow if user matches the user_id (normal user operation)
        auth.uid()::text = user_id::text
        OR
        -- Allow admins to view all secrets
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Add policy to allow service role to bypass RLS for UPDATE operations
CREATE POLICY "Service role can update secrets"
    ON secrets_vault FOR UPDATE
    USING (
        -- Allow if user is service role (has full access)
        auth.role() = 'service_role'
        OR
        -- Allow if user matches the user_id (normal user operation)
        auth.uid()::text = user_id::text
    );

-- Add policy to allow service role to bypass RLS for DELETE operations
CREATE POLICY "Service role can delete secrets"
    ON secrets_vault FOR DELETE
    USING (
        -- Allow if user is service role (has full access)
        auth.role() = 'service_role'
        OR
        -- Allow if user matches the user_id (normal user operation)
        auth.uid()::text = user_id::text
    );

-- Drop the old restrictive policies (if they exist)
DROP POLICY IF EXISTS "Users can create own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can view own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can update own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Users can delete own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Admins can view all secrets" ON secrets_vault;