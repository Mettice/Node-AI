#!/usr/bin/env python3
"""
Supabase Migration Fix - Add settings column to profiles table.
This script works directly with Supabase without requiring the full backend setup.
"""

import os
import sys
import traceback
import json

def fix_supabase_settings():
    """Fix the settings column issue using Supabase client directly."""
    
    print("🔧 NodeFlow Supabase Settings Migration")
    print("=" * 60)
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    print(f"📋 Environment check:")
    print(f"   - SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"   - SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '❌ Missing'}")
    print(f"   - SUPABASE_ANON_KEY: {'✅ Set' if os.getenv('SUPABASE_ANON_KEY') else '❌ Missing'}")
    print()
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        print("📋 Please set these environment variables:")
        print("   export SUPABASE_URL=https://your-project.supabase.co")
        print("   export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        print("   # OR")
        print("   export SUPABASE_ANON_KEY=your-anonymous-key")
        print()
        print("💡 You can find these in your Supabase dashboard → Settings → API")
        return False
    
    try:
        # Import Supabase (try to install if missing)
        try:
            from supabase import create_client, Client
        except ImportError:
            print("❌ supabase package not found")
            print("📦 Installing supabase package...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
            from supabase import create_client, Client
            print("✅ supabase package installed")
        
        # Create Supabase client
        print(f"🔗 Connecting to Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by fetching profiles table schema
        try:
            # Test if we can query the profiles table
            result = supabase.table("profiles").select("id").limit(1).execute()
            print("✅ Supabase connection successful")
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            return False
        
        # Check if settings column exists
        print("🔍 Checking profiles table schema...")
        
        # Try to select settings column to see if it exists
        try:
            result = supabase.table("profiles").select("id, settings").limit(1).execute()
            print("✅ Settings column already exists!")
            return True
        except Exception as e:
            if "column" in str(e).lower() and "settings" in str(e).lower():
                print("⚠️  Settings column missing - this is the source of your 404 error!")
            else:
                print(f"❌ Unexpected error checking schema: {e}")
                return False
        
        # Provide SQL to run in Supabase dashboard
        print("\n🛠️  SOLUTION:")
        print("=" * 60)
        print("The settings column is missing from your profiles table.")
        print("This causes profile lookups to fail, which affects authentication.")
        print()
        print("📋 Please run this SQL in your Supabase dashboard (SQL Editor):")
        print()
        print("-- Add settings column to profiles table")
        print("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;")
        print()
        print("-- Create index for performance")  
        print("CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);")
        print()
        print("-- Add documentation")
        print("COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';")
        print()
        print("💡 How to do this:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Click 'SQL Editor' in the left sidebar")
        print("   3. Paste the above SQL and click 'Run'")
        print("   4. Try your RAG evaluation again")
        print()
        print("🔗 Dashboard URL: " + supabase_url.replace("supabase.co", "supabase.com") + "/project/default/sql/new")
        
        return True
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_supabase_settings()
    print("\n" + "=" * 60)
    if success:
        print("🎯 Migration guidance provided successfully!")
        print("🚀 After running the SQL, your RAG evaluation should work!")
    else:
        print("❌ Migration guidance failed. Check your Supabase configuration.")