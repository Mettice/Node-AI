# Complete Database Setup for Production

## ⚠️ CRITICAL: Run This in Production

This script ensures **ALL** tables, indexes, RLS policies, and relationships are properly created in your Supabase database.

## How to Run

1. **Open Supabase SQL Editor**
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Create a new query

2. **Copy and Run the Complete Setup Script**
   - Open `000_COMPLETE_DATABASE_SETUP.sql`
   - Copy the entire contents
   - Paste into the SQL Editor
   - Click "Run" or press `Ctrl+Enter`

3. **Verify Setup**
   - The script includes verification queries at the end
   - Check the results to ensure:
     - All tables exist
     - RLS is enabled on all tables
     - All policies are created
     - All indexes are created

## What This Script Does

### 1. Creates All Required Tables
- ✅ `profiles` - User profiles with settings
- ✅ `workflows` - Workflow definitions
- ✅ `secrets_vault` - **CRITICAL** - Encrypted API keys storage
- ✅ `traces` - Observability traces
- ✅ `spans` - Observability spans
- ✅ `api_keys` - NodAI API keys
- ✅ `deployments` - Workflow deployments
- ✅ `knowledge_bases` - Knowledge base storage

### 2. Creates All Indexes
- Performance indexes on all foreign keys
- Composite indexes for common queries
- GIN indexes for JSONB columns

### 3. Enables Row Level Security (RLS)
- RLS enabled on ALL tables
- Ensures multi-tenant data isolation

### 4. Creates RLS Policies
- **Service Role Access**: Allows backend to access all data
- **User Access**: Users can only access their own data
- **Admin Access**: Admins can view all data (for support)

### 5. Critical: Secrets Vault RLS
The `secrets_vault` table has special RLS policies that:
- ✅ Allow service role to INSERT/SELECT/UPDATE/DELETE (for backend operations)
- ✅ Allow users to manage their own secrets
- ✅ Allow admins to view all secrets (for support)

## Verification Queries

After running the script, run these to verify:

```sql
-- 1. Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans', 'api_keys', 'deployments', 'knowledge_bases')
ORDER BY table_name;

-- 2. Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans', 'api_keys', 'deployments', 'knowledge_bases')
ORDER BY tablename;

-- 3. Check secrets_vault policies (CRITICAL)
SELECT policyname, cmd, permissive, roles, qual, with_check
FROM pg_policies 
WHERE tablename = 'secrets_vault'
ORDER BY policyname;

-- 4. Check indexes exist
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('profiles', 'workflows', 'secrets_vault', 'traces', 'spans')
ORDER BY tablename, indexname;
```

## Expected Results

### Tables Check
Should return 8 rows:
- profiles
- workflows
- secrets_vault
- traces
- spans
- api_keys
- deployments
- knowledge_bases

### RLS Check
All tables should have `rowsecurity = true`

### Secrets Vault Policies
Should have 4 policies:
- `secrets_insert_policy`
- `secrets_select_policy`
- `secrets_update_policy`
- `secrets_delete_policy`

### Indexes Check
Should show multiple indexes for each table (at least 2-3 per table)

## Troubleshooting

### If secrets_vault policies are missing:
```sql
-- Re-run just the secrets_vault RLS section from the script
```

### If RLS is blocking service role:
```sql
-- Check that service role policies exist:
SELECT * FROM pg_policies WHERE tablename = 'secrets_vault' AND roles = '{service_role}';
```

### If tables are missing:
```sql
-- Check if migrations ran:
SELECT * FROM information_schema.tables WHERE table_schema = 'public';
```

## Important Notes

1. **Service Role Key**: Your backend uses the Supabase service role key, which bypasses RLS. This is required for backend operations.

2. **User JWT**: When users authenticate, their JWT contains their user ID, which RLS uses to filter data.

3. **Secrets Vault**: The most critical table - ensure RLS policies allow service role access, otherwise secrets won't work.

4. **Foreign Keys**: All foreign key relationships are properly set up with CASCADE deletes where appropriate.

## After Running

1. ✅ Verify all tables exist
2. ✅ Verify RLS is enabled
3. ✅ Verify secrets_vault policies exist
4. ✅ Test creating a secret via the UI
5. ✅ Test retrieving a secret via the API

If all checks pass, your database is properly configured! 🎉

