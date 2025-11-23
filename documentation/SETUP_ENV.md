# Environment Variables Setup

## Location

All environment variables should be in the **root `.env` file** (not in `backend/.env` or `frontend/.env`).

## Required Variables

### General Settings
```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (Vite)
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Backend
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
VAULT_ENCRYPTION_KEY=your-32-byte-hex-encryption-key
```

## Important Notes

### DATABASE_URL Format

The `DATABASE_URL` must be complete and include:
- Protocol: `postgresql://`
- Username: `postgres`
- Password: `[your-password]`
- Host: `db.xxx.supabase.co` (note the `db.` prefix)
- Port: `:5432`
- Database: `/postgres`

**Complete format:**
```
postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres
```

### Getting DATABASE_URL from Supabase

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database**
3. Find **Connection string** section
4. Copy the **URI** connection string
5. Replace `[YOUR-PASSWORD]` with your actual database password

### Vault Encryption Key

Generate a secure encryption key:

```python
import secrets
key = secrets.token_bytes(32)
print(key.hex())  # Use this as VAULT_ENCRYPTION_KEY
```

Or using command line:
```bash
python -c "import secrets; print(secrets.token_bytes(32).hex())"
```

## Verification

### Backend
Check the startup logs. You should see:
```
INFO - Supabase client initialized successfully
INFO - Database connection pool initialized successfully
```

If you see:
```
WARNING - DATABASE_URL not set...
```
Then the `DATABASE_URL` is not being read correctly.

### Frontend
The frontend reads `VITE_*` variables from the root `.env` file automatically when using Vite.

## Troubleshooting

### DATABASE_URL not being read

1. **Check the format**: Make sure it's complete with port and database name
2. **Check location**: Ensure `.env` is in the project root (same level as `backend/` and `frontend/`)
3. **Restart server**: After changing `.env`, restart the backend server
4. **Check for typos**: Variable name must be exactly `DATABASE_URL`

### Frontend can't read VITE_ variables

1. **Check prefix**: Frontend variables must start with `VITE_`
2. **Restart dev server**: Vite only reads `.env` on startup
3. **Check location**: `.env` must be in project root

## Security

⚠️ **Never commit `.env` to git!**

Make sure `.env` is in `.gitignore`:
```
.env
.env.local
.env.*.local
```

