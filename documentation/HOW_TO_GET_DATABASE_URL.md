# How to Get DATABASE_URL from Supabase

## Where to Find It

The **API Settings** page (shown in your screenshot) shows the REST API URL, but for the database connection, you need the **Database Settings**.

### Step-by-Step:

1. **In Supabase Dashboard:**
   - Go to your project: `etvmoholebueqakplpqr`
   - Click **Settings** (gear icon) in the left sidebar
   - Click **Database** (not "API")

2. **On the Database Settings page:**
   - Scroll down to **Connection string** section
   - You'll see different connection string formats
   - Select the **URI** tab (not "Connection pooling" or "Session mode")

3. **Copy the Connection String:**
   - It will look like:
     ```
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
     ```
   - OR (direct connection):
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
     ```

4. **Replace `[YOUR-PASSWORD]`:**
   - Replace `[YOUR-PASSWORD]` with your actual database password
   - Your password is: `Fonkem140988`

5. **Final DATABASE_URL should be:**
   ```
   postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres
   ```

## Important Notes

### Direct Connection vs Pooled Connection

**Direct Connection (Recommended for our use):**
```
postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
```
- Port: `5432`
- Host: `db.xxx.supabase.co`
- Use this for our connection pool

**Pooled Connection (Alternative):**
```
postgresql://postgres.xxx:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```
- Port: `6543`
- Host: `aws-0-[region].pooler.supabase.com`
- For connection pooling (we're using our own pool)

### Your Current Issue

Your DATABASE_URL has a typo:
- ❌ **Wrong:** `db.etvmoholebuekplpqr` (missing 'a')
- ✅ **Correct:** `db.etvmoholebueqakplpqr` (has 'a')

The hostname should match your Project URL:
- Project URL: `https://etvmoholebueqakplpqr.supabase.co`
- Database host: `db.etvmoholebueqakplpqr.supabase.co`

## How to Validate

### Option 1: Test in Supabase SQL Editor
1. Go to **SQL Editor** in Supabase
2. Run a simple query:
   ```sql
   SELECT version();
   ```
3. If it works, your database is accessible

### Option 2: Test Connection from Backend
After updating your `.env` file, restart the backend and check logs:
- ✅ **Success:** `Database connection pool initialized successfully`
- ❌ **Error:** Check the error message for details

### Option 3: Use psql (if installed)
```bash
psql "postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres"
```

If it connects, the URL is correct.

## Quick Fix

Update your `.env` file:

```env
# Current (WRONG - has typo)
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebuekplpqr.supabase.co:5432/postgres

# Should be (CORRECT)
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres
```

**Change:** `etvmoholebuekplpqr` → `etvmoholebueqakplpqr` (add 'a' after 'q')

## Summary

1. **API Settings** (your screenshot) = REST API URL (for frontend)
2. **Database Settings** = Connection string (for backend DATABASE_URL)
3. Go to: **Settings → Database → Connection string → URI tab**
4. Copy and replace `[YOUR-PASSWORD]` with `Fonkem140988`
5. Make sure hostname matches your project URL (with `db.` prefix)

