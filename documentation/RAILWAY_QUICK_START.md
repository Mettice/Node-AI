# ⚡ Railway Quick Start (3 Steps)

## **1. Deploy to Railway**

1. Go to: https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select: `Mettice/Node-AI`
4. Done! Railway auto-detects Python ✅

## **2. Add Environment Variables**

Railway Dashboard → Variables → Add:

```
CORS_ORIGINS_STR=https://nodai-nu.vercel.app
JWT_SECRET_KEY=[your-existing-key]
VAULT_ENCRYPTION_KEY=[generate: python generate-vault-key.py]
SUPABASE_URL=[your-url]
SUPABASE_ANON_KEY=[your-key]
DATABASE_URL=[your-db-url]
```

## **3. Update Frontend**

Vercel Dashboard → Environment Variables → Update:

```
VITE_API_URL=https://your-backend.up.railway.app
```

Redeploy frontend.

---

**Done!** 🎉

