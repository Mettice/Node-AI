# Database Migrations

This directory contains SQL migration files for setting up the Supabase PostgreSQL database.

## Migration Files

1. **001_initial_schema.sql** - Creates all database tables and indexes
2. **002_row_level_security.sql** - Enables RLS and creates security policies

## Running Migrations

### Option 1: Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of each migration file
4. Run them in order (001, then 002)

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

### Option 3: Using psql

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"

# Run migrations
\i migrations/001_initial_schema.sql
\i migrations/002_row_level_security.sql
```

## Migration Order

**Important:** Run migrations in this order:

1. First: `001_initial_schema.sql` (creates tables)
2. Then: `002_row_level_security.sql` (enables RLS and policies)

## Verification

After running migrations, verify:

1. All tables exist:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```

2. RLS is enabled:
   ```sql
   SELECT tablename, rowsecurity 
   FROM pg_tables 
   WHERE schemaname = 'public';
   ```

3. Policies exist:
   ```sql
   SELECT schemaname, tablename, policyname 
   FROM pg_policies 
   WHERE schemaname = 'public';
   ```

## Environment Variables

Make sure these are set in your `.env` file:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
VAULT_ENCRYPTION_KEY=your-32-byte-hex-encryption-key
```

## Generating Encryption Key

To generate a secure encryption key for the secrets vault:

```python
import secrets
key = secrets.token_bytes(32)
print(key.hex())  # Use this as VAULT_ENCRYPTION_KEY
```

