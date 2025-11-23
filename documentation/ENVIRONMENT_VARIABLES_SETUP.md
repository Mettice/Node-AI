# 🔑 Environment Variables Setup

## **✅ Build Successful!**

Now you need to add environment variables in **Railway** (backend) and **Vercel** (frontend).

---

## **🚂 RAILWAY (Backend) Environment Variables**

Go to: Railway Dashboard → Your Service → **Variables** tab

### **Required Variables:**

```env
# App Configuration
DEBUG=false
LOG_LEVEL=INFO
PORT=8000

# CORS - UPDATE WITH YOUR VERCEL FRONTEND URL
CORS_ORIGINS_STR=https://nodai-nu.vercel.app

# Security Keys
JWT_SECRET_KEY=your-existing-jwt-secret-key-from-vercel
VAULT_ENCRYPTION_KEY=generate-new-one-or-use-existing

# Supabase
SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:Fonkem140988@db.etvmoholebueqakplpqr.supabase.co:5432/postgres
```

### **Optional Variables:**

```env
# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn-if-you-have-one
SENTRY_ENVIRONMENT=production
```

---

## **🎨 VERCEL (Frontend) Environment Variables**

Go to: Vercel Dashboard → Your Project → Settings → **Environment Variables**

### **Required Variables:**

```env
# Backend API URL - UPDATE WITH YOUR RAILWAY URL
VITE_API_URL=https://your-backend.up.railway.app

# Supabase
VITE_SUPABASE_URL=https://etvmoholebueqakplpqr.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

---

## **📋 Step-by-Step**

### **Step 1: Get Your Railway Backend URL**

1. Railway Dashboard → Your Service
2. Click **"Settings"** tab
3. Scroll to **"Domains"** or **"Networking"**
4. Copy the **Public URL** (e.g., `https://nodeai-production.up.railway.app`)

### **Step 2: Add Railway Variables**

1. Railway Dashboard → **Variables** tab
2. Click **"New Variable"**
3. Add each variable from the list above
4. **Important**: Update `CORS_ORIGINS_STR` with your Vercel URL

### **Step 3: Add Vercel Variables**

1. Vercel Dashboard → Settings → **Environment Variables**
2. Click **"Add New"**
3. Add:
   - `VITE_API_URL` = Your Railway URL (from Step 1)
   - `VITE_SUPABASE_URL` = Your Supabase URL
   - `VITE_SUPABASE_ANON_KEY` = Your Supabase anon key

### **Step 4: Generate Vault Encryption Key (if needed)**

If you don't have `VAULT_ENCRYPTION_KEY`:

```powershell
python generate-vault-key.py
```

Copy the output and add it to Railway variables.

---

## **🔄 After Adding Variables**

### **Railway:**
- Variables are applied immediately
- Service will auto-redeploy if needed

### **Vercel:**
- **IMPORTANT**: After adding variables, you **MUST** redeploy
- Go to **Deployments** → Click **"..."** → **"Redeploy"**

---

## **✅ Verify It Works**

### **1. Test Backend**

Visit: `https://your-backend.up.railway.app/api/v1/health`

**Expected**:
```json
{
  "status": "healthy",
  "app_name": "NodeAI",
  "version": "0.1.0"
}
```

### **2. Test Frontend**

Visit: `https://nodai-nu.vercel.app`

**Expected**:
- ✅ No "Failed to connect" error
- ✅ Login/Register page loads
- ✅ Can create workflows

---

## **🔐 Security Notes**

### **Keep Secret** (Backend only):
- `JWT_SECRET_KEY`
- `VAULT_ENCRYPTION_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

### **Safe to Expose** (Frontend - public):
- `VITE_*` variables (included in frontend bundle)
- `VITE_SUPABASE_ANON_KEY` (designed to be public)
- `VITE_API_URL` (just a URL)

---

## **📝 Quick Checklist**

- [ ] Railway backend URL copied
- [ ] Railway variables added (all required ones)
- [ ] Vercel `VITE_API_URL` set to Railway URL
- [ ] Vercel Supabase variables added
- [ ] Vercel redeployed after adding variables
- [ ] Backend health endpoint works
- [ ] Frontend connects successfully ✅

---

**Add the variables and you're done!** 🎉

