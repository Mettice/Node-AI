-- Migration: Fix RLS by ensuring profiles exist for auth users
-- Description: Creates trigger to auto-create profiles and fixes RLS policies
-- Created: 2025-11-24

-- ============================================
-- Auto-create profiles for new auth users
-- ============================================

-- Function to create profile when user is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        'user'
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, profiles.name),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- Fix RLS policy for secrets_vault  
-- ============================================

-- Drop existing policies and recreate more permissive ones
DROP POLICY IF EXISTS "Users can manage own secrets" ON secrets_vault;
DROP POLICY IF EXISTS "Admins can view all secrets" ON secrets_vault;

-- Allow users to insert their own secrets (more permissive)
CREATE POLICY "Users can create own secrets"
    ON secrets_vault FOR INSERT
    WITH CHECK (
        auth.uid()::text = user_id::text
    );

-- Allow users to view their own secrets
CREATE POLICY "Users can view own secrets"
    ON secrets_vault FOR SELECT
    USING (
        auth.uid()::text = user_id::text
    );

-- Allow users to update their own secrets
CREATE POLICY "Users can update own secrets"
    ON secrets_vault FOR UPDATE
    USING (
        auth.uid()::text = user_id::text
    );

-- Allow users to delete their own secrets
CREATE POLICY "Users can delete own secrets"
    ON secrets_vault FOR DELETE
    USING (
        auth.uid()::text = user_id::text
    );

-- Admins can view all secrets (for support)
CREATE POLICY "Admins can view all secrets"
    ON secrets_vault FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- ============================================
-- Backfill profiles for existing auth users
-- ============================================

-- Create profiles for existing auth users who don't have one
INSERT INTO public.profiles (id, email, name, role, created_at, updated_at)
SELECT 
    auth_users.id,
    auth_users.email,
    COALESCE(
        auth_users.raw_user_meta_data->>'name',
        auth_users.raw_user_meta_data->>'full_name',
        split_part(auth_users.email, '@', 1)
    ) as name,
    'user' as role,
    auth_users.created_at,
    NOW() as updated_at
FROM auth.users auth_users
LEFT JOIN public.profiles ON profiles.id = auth_users.id
WHERE profiles.id IS NULL;