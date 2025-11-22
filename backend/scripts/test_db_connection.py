"""
Test database connection script.

This script tests the database connection using the DATABASE_URL from environment.
"""

import os
import sys
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

from backend.config import settings
from backend.core.database import initialize_database, get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def test_connection():
    """Test database connection."""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    # Check if configured
    if not settings.supabase_url:
        print("❌ ERROR: SUPABASE_URL not set in environment")
        return False
    
    print(f"✅ Supabase URL: {settings.supabase_url}")
    
    # Check DATABASE_URL
    db_url = settings.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set in environment")
        return False
    
    # Mask password in output
    masked_url = db_url.split('@')[0] + '@' + db_url.split('@')[1] if '@' in db_url else db_url
    print(f"✅ Database URL: {masked_url}")
    
    # Initialize database
    try:
        print("\nInitializing database connection...")
        initialize_database(settings)
        
        if not is_database_configured():
            print("❌ ERROR: Database not configured")
            return False
        
        print("✅ Database initialized")
        
        # Test connection
        print("\nTesting connection...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"✅ Connected successfully!")
                print(f"   PostgreSQL version: {version[0]}")
                
                # Test query
                cur.execute("SELECT current_database(), current_user;")
                db_info = cur.fetchone()
                print(f"   Database: {db_info[0]}")
                print(f"   User: {db_info[1]}")
                
                # Check if tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cur.fetchall()
                if tables:
                    print(f"\n✅ Found {len(tables)} tables:")
                    for table in tables[:10]:  # Show first 10
                        print(f"   - {table[0]}")
                    if len(tables) > 10:
                        print(f"   ... and {len(tables) - 10} more")
                else:
                    print("\n⚠️  WARNING: No tables found. Run migrations first!")
        
        print("\n" + "=" * 60)
        print("✅ Connection test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Connection failed")
        print(f"   {type(e).__name__}: {e}")
        print("\n" + "=" * 60)
        print("❌ Connection test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

