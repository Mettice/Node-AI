-- Migration: Add settings column to profiles table
-- Description: Adds JSONB settings column for user preferences including observability keys
-- Created: 2025-01-XX

-- Add settings column to profiles table
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

-- Create index for settings queries
CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);

-- Add comment
COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';

