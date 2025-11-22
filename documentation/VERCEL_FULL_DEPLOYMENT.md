# 🚀 Deploy Everything to Vercel (Frontend + Backend)

## **Setup: Both Frontend and Backend on Vercel**

This guide shows you how to deploy **both** frontend and backend to Vercel using serverless functions.

---

## **📁 Project Structure**

```
Node-AI/
├── frontend/          # React app (static site)
├── backend/           # FastAPI app (serverless functions)
├── api/               # Vercel serverless entry point
│   ├── index.py       # FastAPI handler
│   └── requirements.txt
└── vercel.json        # Vercel configuration
```

---

## **✅ Step 1: Verify Files**

Make sure these files exist:

- ✅ `api/index.py` - Serverless function entry point
- ✅ `api/requirements.txt` - Python dependencies hint
- ✅ `vercel.json` - Vercel configuration
- ✅ `frontend/vercel.json` - Frontend config (optional, can delete)

---

## **✅ Step 2: Configure Vercel**

1. Go to **Vercel Dashboard**: https://vercel.com/new
2. **Import** your GitHub repo: `Mettice/Node-AI`
3. **Configure**:
   - **Framework Preset**: `Other` (we're using custom config)
   - **Root Directory**: `.` (root)
   - **Build Command**: (leave empty, handled by vercel.json)
   - **Output Directory**: (leave empty, handled by vercel.json)

---

## **✅ Step 3: Add Environment Variables**

Go to **Settings** → **Environment Variables** and add:

### **Backend Variables**
```env
# App
DEBUG=false
LOG_LEVEL=INFO

# CORS - UPDATE WITH YOUR VERCEL URL AFTER DEPLOYMENT
CORS_ORIGINS_STR=https://your-app.vercel.app

# Security
JWT_SECRET_KEY=your-generated-secret-key
VAULT_ENCRYPTION_KEY=your-generated-encryption-key

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.yourproject.supabase.co:5432/postgres
```

### **Frontend Variables**
```env
# API URL - UPDATE AFTER FIRST DEPLOYMENT
VITE_API_URL=https://your-app.vercel.app

# Supabase
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Important**: 
- Set `VITE_API_URL` to your Vercel URL **after** first deployment
- Set `CORS_ORIGINS_STR` to your Vercel URL **after** first deployment

---

## **✅ Step 4: Deploy**

1. Click **Deploy**
2. Wait 3-5 minutes (first build takes longer)
3. Copy your deployment URL: `https://your-app.vercel.app`

---

## **✅ Step 5: Update Environment Variables**

After first deployment:

1. Go to **Settings** → **Environment Variables**
2. Update:
   - `VITE_API_URL` = `https://your-app.vercel.app`
   - `CORS_ORIGINS_STR` = `https://your-app.vercel.app`
3. **Redeploy** (Deployments → ... → Redeploy)

---

## **✅ Step 6: Verify**

### **Test Backend**
Visit: `https://your-app.vercel.app/api/v1/health`

Expected:
```json
{
  "status": "healthy",
  "app_name": "NodeAI"
}
```

### **Test Frontend**
Visit: `https://your-app.vercel.app`

Expected:
- ✅ No connection errors
- ✅ Login/Register page loads
- ✅ Can create workflows

---

## **🔍 How It Works**

### **Routing**
- `/api/*` → Serverless function (`api/index.py`)
- `/*` → Frontend static files (`frontend/dist`)

### **Build Process**
1. **Frontend**: Builds React app to `frontend/dist`
2. **Backend**: Packages Python dependencies
3. **Deploy**: Uploads both to Vercel

### **Runtime**
- **Frontend**: Served as static files (CDN)
- **Backend**: Runs as serverless functions (on-demand)

---

## **⚠️ Important Notes**

### **Serverless Function Limits**
- **Free tier**: 10 seconds max execution time
- **Pro tier**: 60 seconds max execution time
- **Cold starts**: First request may be slower (~1-2s)

### **Long-Running Workflows**
If your workflows take longer than 10 seconds:
- Consider **Option 2** (Railway backend)
- Or upgrade to Vercel Pro ($20/month)

### **File Storage**
- Vercel serverless functions are **stateless**
- File uploads should go to:
  - Supabase Storage
  - AWS S3
  - Or other cloud storage

---

## **🚨 Troubleshooting**

### **404 on `/api/*` routes**
- Check `vercel.json` has correct routing
- Verify `api/index.py` exists
- Check build logs for Python errors

### **CORS errors**
- Update `CORS_ORIGINS_STR` with your Vercel URL
- Redeploy after updating

### **Function timeout**
- Workflow took >10 seconds (free tier limit)
- Consider splitting into smaller steps
- Or use Railway backend

### **Import errors**
- Check `api/index.py` path setup
- Verify `backend/requirements.txt` has all dependencies

---

## **📊 Cost**

### **Free Tier**
- ✅ 100GB bandwidth/month
- ✅ 100 serverless function invocations/day
- ✅ 10s function timeout
- ✅ Perfect for beta testing

### **Pro Tier** ($20/month)
- ✅ Unlimited bandwidth
- ✅ Unlimited invocations
- ✅ 60s function timeout
- ✅ Better for production

---

## **🎯 Next Steps**

1. **Deploy** using steps above
2. **Test** all features
3. **Monitor** function execution times
4. **Upgrade** to Pro if needed (or switch to Railway)

---

**Ready to deploy?** Follow the steps above! 🚀

