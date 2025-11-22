# Quick Fixes for Current Issues

## Issue 1: DATABASE_URL Hostname Typo

**Error:**
```
could not translate host name "db.etvmoholebuekplpqr.supabase.co" to address
```

**Problem:** Your DATABASE_URL has a typo. It's missing an 'a' in the hostname.

**Fix:** Update your `.env` file:

**Current (WRONG):**
```
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebuekplpqr.supabase.co:5432/postgres
```

**Should be (CORRECT):**
```
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres
```

Note: `etvmoholebuekplpqr` → `etvmoholebueqakplpqr` (added 'a' after 'q')

**Or get the correct URL from Supabase:**
1. Go to Supabase Dashboard → Settings → Database
2. Copy the **Connection string** (URI format)
3. Replace `[YOUR-PASSWORD]` with `Fonkem140988`
4. Update your `.env` file

---

## Issue 2: Frontend "Supabase not configured"

**Error:**
```
Supabase not configured. Authentication disabled.
```

**Problem:** Vite needs to be restarted to read new environment variables.

**Fix:**
1. Stop the Vite dev server (Ctrl+C)
2. Restart it: `npm run dev` (in the `frontend` directory)
3. Vite only reads `.env` files on startup

**Verify:** Check that your `.env` file in the **root** has:
```env
VITE_SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

---

## Issue 3: Access Login Page

**Solution:** Navigate to:
- **Login:** http://localhost:5173/login
- **Register:** http://localhost:5173/register
- **Home:** http://localhost:5173/

The app will automatically redirect to `/login` if authentication is required.

---

## Issue 4: Create Database Tables

**You need to run the migrations in Supabase:**

1. **Go to Supabase Dashboard:**
   - https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor:**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run Migration 001:**
   - Open `backend/migrations/001_initial_schema.sql`
   - Copy all contents
   - Paste into SQL Editor
   - Click "Run" (or Ctrl+Enter)

4. **Run Migration 002:**
   - Open `backend/migrations/002_row_level_security.sql`
   - Copy all contents
   - Paste into SQL Editor
   - Click "Run"

5. **Verify:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```
   
   You should see 10 tables.

---

## Summary Checklist

- [ ] Fix DATABASE_URL hostname typo in `.env`
- [ ] Restart Vite dev server (to read VITE_ variables)
- [ ] Run migrations in Supabase SQL Editor
- [ ] Restart backend server (to pick up DATABASE_URL fix)
- [ ] Access login page at http://localhost:5173/login

---

## After Fixes

Once everything is fixed, you should see:
- ✅ Backend: "Database connection pool initialized successfully"
- ✅ Frontend: No "Supabase not configured" warning
- ✅ Login page accessible at `/login`
- ✅ Can register and login users

