# 🚂 Deploy Backend to Railway (Simple & Reliable)

## **Why Railway?**
- ✅ **Simple**: Just connect GitHub and deploy
- ✅ **No serverless limits**: No 10-second timeouts
- ✅ **Always-on**: No cold starts
- ✅ **Perfect for FastAPI**: Designed for Python apps
- ✅ **$5/month**: Includes $5 credit (essentially free for beta)

---

## **🚀 Quick Setup (5 minutes)**

### **Step 1: Create Railway Account**

1. Go to: https://railway.app
2. Click **"Start a New Project"**
3. Sign up with GitHub (easiest)

### **Step 2: Deploy from GitHub**

1. Click **"Deploy from GitHub repo"**
2. Select: `Mettice/Node-AI`
3. Railway will auto-detect it's a Python project ✅

### **Step 3: Configure Settings**

Railway Dashboard → Your Service → **Settings**:

- **Root Directory**: Leave empty (or set to `backend`)
- **Start Command**: 
  ```
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```
- **Python Version**: `3.11` or `3.12`

### **Step 4: Add Environment Variables**

Railway Dashboard → Your Service → **Variables** tab:

Add these (copy from your Vercel env vars):

```env
# App
DEBUG=false
LOG_LEVEL=INFO

# Server
PORT=8000

# CORS - UPDATE WITH YOUR VERCEL FRONTEND URL
CORS_ORIGINS_STR=https://nodai-nu.vercel.app

# Security
JWT_SECRET_KEY=[your-existing-jwt-secret]
VAULT_ENCRYPTION_KEY=[generate-new-one-or-use-existing]

# Supabase
SUPABASE_URL=[your-supabase-url]
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]
DATABASE_URL=[your-database-url]
```

### **Step 5: Deploy**

1. Railway will **auto-deploy** when you push to GitHub
2. Or click **"Deploy"** button
3. Wait 2-3 minutes
4. Copy the **Public URL** (e.g., `https://nodeai-production.up.railway.app`)

---

## **🔗 Connect Frontend to Railway Backend**

### **Update Vercel Environment Variables**

1. Vercel Dashboard → Settings → Environment Variables
2. Update `VITE_API_URL`:
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```
3. **Redeploy** frontend

### **Update Railway CORS**

1. Railway Dashboard → Variables
2. Update `CORS_ORIGINS_STR`:
   ```
   CORS_ORIGINS_STR=https://nodai-nu.vercel.app
   ```
3. Railway will **auto-redeploy**

---

## **✅ Test**

1. **Backend**: `https://your-backend.up.railway.app/api/v1/health`
   - Should return: `{"status": "healthy"}`

2. **Frontend**: `https://nodai-nu.vercel.app`
   - Should connect to backend ✅
   - No more connection errors ✅

---

## **💰 Cost**

- **Railway**: $5/month (includes $5 credit = **FREE** for beta)
- **Vercel**: Free (frontend)
- **Total**: **$0/month** for beta testing

---

## **🎯 That's It!**

No more:
- ❌ Serverless function crashes
- ❌ 10-second timeouts
- ❌ Cold starts
- ❌ Complex configurations

Just:
- ✅ Simple deployment
- ✅ Always-on backend
- ✅ Reliable FastAPI hosting

---

**Ready?** Go to Railway and deploy! 🚂

