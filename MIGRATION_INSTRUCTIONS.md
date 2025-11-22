# Database Migration Instructions

## Step 1: Access Supabase SQL Editor

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select your project: `etvmoholebueqakplpqr`
3. Navigate to **SQL Editor** in the left sidebar
4. Click **New Query**

## Step 2: Run Migration 001 - Initial Schema

1. Open `backend/migrations/001_initial_schema.sql` in your code editor
2. Copy the entire contents
3. Paste into the Supabase SQL Editor
4. Click **Run** (or press Ctrl+Enter)

This will create all the tables:
- `profiles`
- `workflows`
- `api_keys`
- `usage_logs`
- `deployments`
- `knowledge_bases`
- `webhooks`
- `workflow_shares`
- `secrets_vault`
- `secret_access_log`

## Step 3: Run Migration 002 - Row Level Security

1. Open `backend/migrations/002_row_level_security.sql` in your code editor
2. Copy the entire contents
3. Paste into the Supabase SQL Editor
4. Click **Run** (or press Ctrl+Enter)

This will:
- Enable Row Level Security (RLS) on all tables
- Create security policies for user isolation

## Step 4: Verify Tables Were Created

Run this query in the SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

You should see all 10 tables listed.

## Step 5: Verify RLS is Enabled

Run this query:

```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

All tables should have `rowsecurity = true`.

## Step 6: Fix DATABASE_URL

Your current DATABASE_URL has a typo in the hostname. Update it in your `.env` file:

**Current (incorrect):**
```
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebuekplpqr.supabase.co:5432/postgres
```

**Should be (correct):**
```
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres
```

Note: The hostname should match your Supabase URL: `etvmoholebueqakplpqr` (not `etvmoholebuekplpqr`)

## Step 7: Get Correct DATABASE_URL from Supabase

1. Go to **Settings** → **Database** in your Supabase dashboard
2. Scroll to **Connection string** section
3. Select **URI** tab
4. Copy the connection string
5. Replace `[YOUR-PASSWORD]` with your actual password: `Fonkem140988`
6. Update your `.env` file

## Troubleshooting

### "could not translate host name" error

This means the hostname is incorrect. Double-check:
- The hostname in DATABASE_URL matches your Supabase project
- It starts with `db.` (not just the project name)
- No typos in the hostname

### Tables not appearing

- Make sure you ran both migration files
- Check for errors in the SQL Editor
- Verify you're in the correct project

### RLS policies not working

- Make sure migration 002 ran successfully
- Check that `rowsecurity = true` for all tables
- Verify policies exist: `SELECT * FROM pg_policies WHERE schemaname = 'public';`

