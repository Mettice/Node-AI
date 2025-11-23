# ⚡ Quick Deploy Reference

**Super fast deployment guide for NodeAI**

---

## 🎯 TL;DR

1. **Frontend** → Vercel (free, auto-deploy)
2. **Backend** → Railway (easiest, $5 credit)
3. **Database/Auth** → Supabase (free tier)

---

## 📋 STEP-BY-STEP (10 minutes)

### **1. Push to GitHub** (2 min)

```powershell
# Run the deployment script
.\deploy-to-github.ps1

# Or manually:
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/Mettice/Node-AI.git
git push -u origin main
```

---

### **2. Deploy Frontend to Vercel** (3 min)

1. Go to [vercel.com](https://vercel.com) → Sign in with GitHub
2. **New Project** → Import `Mettice/Node-AI`
3. **Settings**:
   - Root Directory: `frontend`
   - Framework: Vite
   - Build: `npm run build`
   - Output: `dist`
4. **Environment Variables**:
   ```
   VITE_API_URL=https://your-backend.railway.app
   VITE_SUPABASE_URL=https://yourproject.supabase.co
   VITE_SUPABASE_ANON_KEY=your-key
   ```
5. **Deploy** ✅

**Your frontend URL**: `https://your-app.vercel.app`

---

### **3. Deploy Backend to Railway** (3 min)

1. Go to [railway.app](https://railway.app) → Sign in with GitHub
2. **New Project** → **Deploy from GitHub**
3. Select `Mettice/Node-AI`
4. **Settings**:
   - Root: `backend`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Variables** → Add all from template below
6. **Deploy** ✅

**Your backend URL**: `https://your-app.up.railway.app`

---

### **4. Setup Supabase** (2 min)

1. Go to [supabase.com](https://supabase.com) → New project
2. Copy:
   - Project URL
   - Anon key
   - Service role key
   - Database URL
3. Add to Railway environment variables ✅

---

## 🔑 ENVIRONMENT VARIABLES TEMPLATE

### **Backend (Railway)**

```env
# App
DEBUG=false
LOG_LEVEL=INFO

# CORS - REPLACE WITH YOUR VERCEL URL
CORS_ORIGINS_STR=https://your-app.vercel.app

# Security - GENERATE NEW KEYS
JWT_SECRET_KEY=<generate-random-32-chars>
VAULT_ENCRYPTION_KEY=<generate-random-hex>

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-key>
DATABASE_URL=postgresql://postgres:<password>@db.yourproject.supabase.co:5432/postgres

# Sentry (optional)
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
```

### **Frontend (Vercel)**

```env
VITE_API_URL=https://your-backend.railway.app
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

---

## 🔐 GENERATE SECURE KEYS

### **Option 1: Python**

```python
import secrets

# JWT Secret
print("JWT_SECRET_KEY:", secrets.token_urlsafe(32))

# Encryption Key
print("VAULT_ENCRYPTION_KEY:", secrets.token_hex(32))
```

### **Option 2: Online**

Use: [1Password Generator](https://1password.com/password-generator/)
- Length: 32 characters
- Include: Letters, numbers, symbols

---

## ✅ POST-DEPLOY CHECKLIST

### **Test Backend**

```bash
curl https://your-backend.railway.app/api/v1/health
```

Expected:
```json
{
  "status": "healthy",
  "app_name": "NodeAI"
}
```

### **Test Frontend**

1. Visit `https://your-app.vercel.app`
2. Register account
3. Check email for verification
4. Login
5. Create workflow
6. Execute workflow

---

## 🚨 COMMON ISSUES

### **Frontend can't reach backend**

❌ **Error**: Network error, CORS error

✅ **Fix**:
1. Update `VITE_API_URL` in Vercel
2. Update `CORS_ORIGINS_STR` in Railway
3. Redeploy both

### **Backend won't start**

❌ **Error**: Application error

✅ **Fix**:
1. Check all environment variables are set
2. Check Railway logs for errors
3. Verify DATABASE_URL format

### **Can't login**

❌ **Error**: Authentication failed

✅ **Fix**:
1. Check Supabase project is active
2. Verify SUPABASE_URL and keys match
3. Check Railway logs for auth errors

---

## 💰 COST

### **Beta Testing** (Free/Cheap)

- Vercel: **$0** (free tier)
- Railway: **$5/month** (includes $5 credit)
- Supabase: **$0** (free tier)
- Sentry: **$0** (free tier)

**Total: ~$5/month** (or free with Railway credit)

### **Production** (After Beta)

- Vercel Pro: $20/month
- Railway: $20/month
- Supabase Pro: $25/month
- Sentry: $26/month

**Total: ~$91/month**

---

## 🔗 USEFUL LINKS

- **Your Frontend**: `https://your-app.vercel.app`
- **Your Backend**: `https://your-backend.railway.app`
- **API Docs**: `https://your-backend.railway.app/docs` (if DEBUG=true)
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Railway Dashboard**: https://railway.app/dashboard
- **Supabase Dashboard**: https://supabase.com/dashboard

---

## 📚 MORE INFO

- Full guide: `DEPLOYMENT_GUIDE.md`
- Security audit: `DEPLOYMENT_READINESS_AUDIT.md`
- Beta checklist: `BETA_DEPLOYMENT_CHECKLIST.md`

---

**That's it! You're deployed! 🎉**

Need help? Open an issue on GitHub.

