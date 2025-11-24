# Deployment Configuration

## Railway Backend Environment Variables

The following environment variables must be set in the Railway dashboard for the backend to work with the Vercel frontend:

### Required for CORS Fix
```
DEBUG=False
CORS_ORIGINS_STR=https://nodai-pi.vercel.app,http://localhost:5173,http://localhost:3000
```

### Database Configuration
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here
DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres
```

### API Keys
```
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-api-key-here
```

### Server Configuration
```
HOST=0.0.0.0
PORT=8000
```

## Issue Identified

The "Network Error: No response from server" issue is caused by **TWO configuration problems**:

### 1. Backend CORS Misconfiguration
- **Wrong Environment Variable**: The backend expects `CORS_ORIGINS_STR` but Railway may have `CORS_ORIGINS`
- **Missing Production URL**: The Vercel frontend URL `https://nodai-pi.vercel.app` was not included in allowed origins
- **Debug Mode**: In production with `DEBUG=False`, CORS origins list defaults to empty `[]` if not explicitly configured

### 2. Frontend API URL Misconfiguration
- **Missing Backend URL**: The frontend uses `VITE_API_URL` environment variable but it's not set for production
- **Default Localhost**: Without `VITE_API_URL`, frontend defaults to `http://localhost:8000` instead of the actual backend

### 3. Deployment Architecture Confusion
- **Two Backend Options**: The project has both Vercel serverless backend (`api/index.py`) and Railway backend (`backend/main.py`)
- **URL Mismatch**: The frontend may be configured for one but trying to reach the other

## Fix Options

### Option 1: Use Railway Backend (Recommended if you want the full FastAPI features)

**Railway Backend Environment Variables:**
- `DEBUG=False` (for production mode)
- `CORS_ORIGINS_STR=https://nodai-pi.vercel.app,http://localhost:5173,http://localhost:3000`

**Vercel Frontend Environment Variables:**
- `VITE_API_URL=https://your-railway-backend-url.railway.app` (get actual URL from Railway dashboard)

### Option 2: Use Vercel Serverless Backend (Simpler deployment, all in Vercel)

**Vercel Environment Variables (for both frontend and backend):**
- `DEBUG=False`
- `CORS_ORIGINS_STR=https://nodai-pi.vercel.app,http://localhost:5173,http://localhost:3000`  
- `VITE_API_URL=https://nodai-pi.vercel.app/api` (uses the same domain with /api prefix)
- (Plus all the database and API key variables from Railway list above)

**Recommended**: Try Option 2 first since it keeps everything in Vercel and simpler to manage.

After setting environment variables:
- **Option 1**: Redeploy Railway backend, then redeploy Vercel frontend
- **Option 2**: Just redeploy Vercel (handles both frontend and backend)

## Verification

After deployment, test by:
1. Opening browser dev tools on https://nodai-pi.vercel.app
2. Try creating a workflow or uploading a file
3. Check if CORS errors are gone from the network tab
4. Backend should respond successfully to frontend API calls

## Database Migration Status

The RLS policies have been fixed with migrations `004_fix_service_role_rls.sql` and `005_check_and_fix_rls.sql`. These need to be applied to the Supabase database to allow service role operations.