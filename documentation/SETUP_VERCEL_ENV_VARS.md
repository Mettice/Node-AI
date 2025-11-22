# 🔑 Setup Vercel Environment Variables

## **Problem**: Frontend can't connect to backend

The frontend is trying to connect to `http://localhost:8000` because `VITE_API_URL` is not set in Vercel.

---

## **✅ SOLUTION: Add Environment Variables**

### **Step 1: Get Your Backend URL**

1. Go to **Railway Dashboard** (or wherever your backend is deployed)
2. Find your backend service
3. Copy the **Public URL** (e.g., `https://nodeai-production.up.railway.app`)

### **Step 2: Add Environment Variables in Vercel**

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Click your **project**
3. Go to **Settings** → **Environment Variables**
4. Add these **3 variables**:

#### **Variable 1: Backend API URL**
```
Name: VITE_API_URL
Value: https://your-backend.up.railway.app
Environment: Production, Preview, Development (select all)
```

#### **Variable 2: Supabase URL**
```
Name: VITE_SUPABASE_URL
Value: https://yourproject.supabase.co
Environment: Production, Preview, Development (select all)
```

#### **Variable 3: Supabase Anon Key**
```
Name: VITE_SUPABASE_ANON_KEY
Value: your-supabase-anon-key-here
Environment: Production, Preview, Development (select all)
```

### **Step 3: Redeploy**

**IMPORTANT**: After adding environment variables, you **MUST** redeploy:

1. Go to **Deployments** tab
2. Click **...** on the latest deployment
3. Click **Redeploy**
4. Wait 2-3 minutes

**Why?** Environment variables are only available in **new builds**, not existing deployments.

---

## **🔍 How to Find Your Values**

### **Backend URL (Railway)**
1. Railway Dashboard → Your Service
2. **Settings** → **Networking**
3. Copy the **Public Domain** URL
   - Example: `https://nodeai-production.up.railway.app`

### **Supabase URL & Key**
1. Supabase Dashboard → Your Project
2. **Settings** → **API**
3. Copy:
   - **Project URL** → `VITE_SUPABASE_URL`
   - **anon/public key** → `VITE_SUPABASE_ANON_KEY`

---

## **✅ Verify It Works**

After redeploying:

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. The error should be gone ✅
3. You should see the login/register page
4. Check Browser Console (F12):
   - ✅ No "Network Error" messages
   - ✅ No "Failed to connect to API" errors

---

## **🚨 Common Issues**

### **Issue 1: Still showing localhost**

**Cause**: Didn't redeploy after adding env vars

**Fix**: 
- Go to Deployments → Redeploy
- Wait for new build to complete

### **Issue 2: CORS errors**

**Cause**: Backend CORS not configured for Vercel URL

**Fix**: 
- Railway Dashboard → Environment Variables
- Add/Update: `CORS_ORIGINS_STR=https://your-app.vercel.app`
- Redeploy backend

### **Issue 3: Supabase not configured warning**

**Cause**: `VITE_SUPABASE_URL` or `VITE_SUPABASE_ANON_KEY` missing

**Fix**: 
- Add both variables in Vercel
- Redeploy

---

## **📋 Quick Checklist**

- [ ] Backend deployed on Railway (or other platform)
- [ ] Backend URL copied
- [ ] Supabase project created
- [ ] Supabase URL and key copied
- [ ] All 3 env vars added in Vercel
- [ ] Environment set to "Production, Preview, Development" for all vars
- [ ] Redeployed after adding vars
- [ ] Frontend now connects successfully ✅

---

## **🎯 Expected Result**

After setup:

1. **Frontend loads** without connection errors
2. **Login/Register** pages work
3. **API calls** succeed
4. **Authentication** works
5. **Workflows** can be created and executed

---

**Need help?** Check:
- Vercel Build Logs (should show env vars are available)
- Browser Console (should show no connection errors)
- Network Tab (API calls should go to your Railway URL, not localhost)

