#!/usr/bin/env python3
"""
Quick fix for database migration - add settings column to profiles table.
"""

import os
import sys
import traceback

# Add current directory to Python path
sys.path.insert(0, '.')

try:
    # Import backend modules
    from backend.config import Settings
    from backend.core.database import get_db_connection, is_database_configured, get_supabase_client, is_supabase_configured
    
    # Load settings to initialize database connections
    settings = Settings()
    
    # Import initialization function
    from backend.core.database import initialize_database
    
    # Initialize database connections with settings
    print("🔄 Initializing database connections...")
    initialize_database(settings)
    
    print("🔧 NodeFlow Database Migration Fix")
    print("=" * 50)
    
    # Check direct database connection
    if is_database_configured():
        print("✅ Direct database connection available")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    print("🔨 Adding settings column to profiles table...")
                    
                    # Add settings column
                    cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;")
                    print("   - Settings column added")
                    
                    # Add index for performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);")
                    print("   - GIN index created for settings column")
                    
                    # Add comment for documentation
                    cur.execute("COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';")
                    print("   - Column comment added")
                    
                    # Commit changes
                    conn.commit()
                    print("✅ Migration completed successfully!")
                    
                    # Verify the column exists
                    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'profiles' AND column_name = 'settings';")
                    result = cur.fetchone()
                    if result:
                        print(f"✅ Verified: settings column exists ({result[0]}, {result[1]})")
                        
                        # Test a simple query
                        cur.execute("SELECT COUNT(*) FROM profiles;")
                        count = cur.fetchone()[0]
                        print(f"✅ Table query test passed ({count} profiles exist)")
                        
                    else:
                        print("❌ ERROR: settings column not found after migration")
                        
        except Exception as e:
            print(f"❌ Database migration failed: {e}")
            traceback.print_exc()
            
    elif is_supabase_configured():
        print("✅ Supabase connection available")
        print("⚠️  DDL migrations require Supabase dashboard access")
        print("📋 Please run this SQL in your Supabase SQL editor:")
        print()
        print("-- Add settings column to profiles table")
        print("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;")
        print("CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);")
        print("COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';")
        print()
        
        # Try to test the connection
        try:
            supabase = get_supabase_client()
            result = supabase.table("profiles").select("id").limit(1).execute()
            print(f"✅ Supabase connection test passed")
        except Exception as e:
            print(f"❌ Supabase connection test failed: {e}")
            
    else:
        print("❌ No database connection configured")
        print("📋 Please configure either:")
        print("   - Direct PostgreSQL connection (DATABASE_URL)")
        print("   - Supabase connection (SUPABASE_URL + SUPABASE_KEY)")

except Exception as e:
    print(f"❌ Script failed: {e}")
    traceback.print_exc()
    
print("\n" + "=" * 50)
print("Migration script completed.")