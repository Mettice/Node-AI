# 🚀 Quick Start: Deploy Everything to Vercel

## **What We're Doing**

Deploying **both** frontend and backend to Vercel:
- **Frontend**: Static React app (served from CDN)
- **Backend**: FastAPI as serverless functions (runs on-demand)

---

## **📋 Files Created**

✅ `api/index.py` - Backend serverless function entry point  
✅ `api/requirements.txt` - Python dependencies  
✅ `vercel.json` - Vercel configuration (handles routing)  
✅ `VERCEL_FULL_DEPLOYMENT.md` - Detailed guide  

---

## **🎯 Quick Steps**

### **1. Push to GitHub**

```powershell
git add .
git commit -m "Setup Vercel deployment: Frontend + Backend serverless functions"
git push
```

### **2. Deploy to Vercel**

1. Go to: https://vercel.com/new
2. **Import** repo: `Mettice/Node-AI`
3. **Configure**:
   - Framework: **Other**
   - Root Directory: **.** (root)
   - Build Command: (leave empty - handled by vercel.json)
   - Output Directory: (leave empty - handled by vercel.json)
4. Click **Deploy**

### **3. Add Environment Variables**

After first deployment, go to **Settings** → **Environment Variables**:

**Backend**:
```
DEBUG=false
CORS_ORIGINS_STR=https://your-app.vercel.app
JWT_SECRET_KEY=your-secret-key
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://...
```

**Frontend**:
```
VITE_API_URL=https://your-app.vercel.app
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### **4. Redeploy**

After adding env vars, **Redeploy** (Deployments → ... → Redeploy)

---

## **✅ How It Works**

- **`/api/*`** → Goes to `api/index.py` (serverless function)
- **`/*`** → Goes to frontend static files

---

## **📖 Full Guide**

See `VERCEL_FULL_DEPLOYMENT.md` for detailed instructions.

---

**Ready?** Push and deploy! 🚀

