# Frontend Environment Variables Setup

## Issue: "Supabase not configured"

This error means Vite isn't reading the `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` from your `.env` file.

## Solution

### Step 1: Verify `.env` File Location

The `.env` file must be in the **project root** (same level as `frontend/` and `backend/`), NOT in the `frontend/` directory.

```
Nodeflow/
├── .env              ← HERE (root)
├── frontend/
├── backend/
└── ...
```

### Step 2: Verify Variables in `.env`

Make sure your root `.env` file has:

```env
# Frontend (Vite) - MUST start with VITE_
VITE_SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Important:** 
- Variables must start with `VITE_` for Vite to read them
- No spaces around the `=` sign
- No quotes needed (unless the value contains spaces)

### Step 3: Restart Vite Dev Server

**Vite only reads `.env` files when it starts!**

1. **Stop the Vite dev server:**
   - Press `Ctrl+C` in the terminal where it's running

2. **Restart it:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Check the browser console:**
   - Open DevTools (F12)
   - Look for the debug log: `Supabase Config: {...}`
   - It should show your URL and key (partially masked)

### Step 4: Verify It's Working

After restarting, you should see in the browser console:
```
Supabase Config: {
  url: "https://etvmoholebueqakplpqr.supabase.co...",
  key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  allEnv: ["VITE_SUPABASE_URL", "VITE_SUPABASE_ANON_KEY"]
}
```

And the "Supabase not configured" error should disappear.

## Troubleshooting

### Still seeing "Supabase not configured"?

1. **Check browser console:**
   - Open DevTools (F12)
   - Look at the console logs
   - Check what `Supabase Config` shows

2. **Verify `.env` file:**
   - Make sure it's in the root directory
   - Make sure variables start with `VITE_`
   - Make sure there are no typos

3. **Check Vite is reading it:**
   - In browser console, type: `import.meta.env.VITE_SUPABASE_URL`
   - It should show your URL (not `undefined`)

4. **Clear browser cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Variables not showing in console?

If `import.meta.env.VITE_SUPABASE_URL` is `undefined`:

1. **Check file location:** `.env` must be in project root
2. **Check variable names:** Must start with `VITE_`
3. **Restart Vite:** Stop and start the dev server
4. **Check for typos:** Variable names are case-sensitive

## Quick Checklist

- [ ] `.env` file is in project root (not in `frontend/`)
- [ ] Variables start with `VITE_`
- [ ] No spaces around `=` in `.env`
- [ ] Vite dev server restarted after adding variables
- [ ] Browser console shows `Supabase Config` with values
- [ ] No "Supabase not configured" error

## Example `.env` File

```env
# Backend
SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres

# Frontend (Vite) - MUST start with VITE_
VITE_SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

