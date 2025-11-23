# 🔧 Fix Backend Connection Issue

## **Problem**: Frontend can't connect to backend API

The frontend is trying to call `/api/v1/health` but getting no response.

---

## **🔍 Diagnosis Steps**

### **1. Test Backend Directly**

Open your browser and visit:
```
https://nodai-nu.vercel.app/api/v1/health
```

**Expected**: JSON response like:
```json
{
  "status": "healthy",
  "app_name": "NodeAI",
  "version": "0.1.0"
}
```

**If you get 404 or error**: The serverless function isn't working.

---

## **✅ Fixes Applied**

### **1. Updated `vercel.json`**
- Added proper `builds` configuration
- Added `routes` for API and frontend
- Added `rewrites` for SPA routing

### **2. Updated `api/index.py`**
- Simplified handler export
- Proper path setup

---

## **🚀 Next Steps**

### **Step 1: Push Changes**

```powershell
git add .
git commit -m "Fix Vercel serverless function configuration"
git push
```

### **Step 2: Check Vercel Build Logs**

1. Go to Vercel Dashboard
2. Deployments → Latest deployment
3. Check **Build Logs**:
   - ✅ Should see "Building Python function"
   - ✅ Should see "Installing dependencies"
   - ❌ If errors, check Python version and dependencies

### **Step 3: Check Function Logs**

1. Vercel Dashboard → Deployments → Latest
2. Click **Functions** tab
3. Check for errors

### **Step 4: Test Backend Endpoint**

Visit: `https://nodai-nu.vercel.app/api/v1/health`

**If still not working**, check:

1. **Python Runtime**:
   - Vercel Dashboard → Settings → Functions
   - Python Version should be `3.9` or `3.11`

2. **Dependencies**:
   - Check if `backend/requirements.txt` is being read
   - May need to copy dependencies to `api/requirements.txt`

3. **Path Issues**:
   - Check if `backend/main.py` can be imported
   - Check if all dependencies are available

---

## **🔧 Alternative: Check if Function is Deployed**

1. Vercel Dashboard → Your Project
2. **Functions** tab (left sidebar)
3. Should see: `api/index.py`
4. Click it → Check logs for errors

---

## **📋 Common Issues**

### **Issue 1: Function Not Found (404)**

**Cause**: Vercel isn't detecting `api/index.py`

**Fix**:
- Make sure `api/index.py` exists
- Make sure `vercel.json` has correct `builds` config
- Redeploy

### **Issue 2: Import Errors**

**Cause**: Python can't find `backend` module

**Fix**:
- Check `sys.path` in `api/index.py`
- Make sure project structure is correct

### **Issue 3: Missing Dependencies**

**Cause**: Dependencies not installed

**Fix**:
- Add all dependencies to `api/requirements.txt`
- Or ensure `backend/requirements.txt` is being read

---

## **🧪 Test Locally First (Optional)**

To test if the serverless function works locally:

```powershell
# Install Vercel CLI
npm i -g vercel

# Test locally
vercel dev
```

Then visit: `http://localhost:3000/api/v1/health`

---

## **✅ Expected Result**

After fixes:
1. ✅ Build succeeds
2. ✅ Function appears in Vercel Functions tab
3. ✅ `https://nodai-nu.vercel.app/api/v1/health` returns JSON
4. ✅ Frontend connects successfully

---

**Push the changes and check the build logs!** 🚀

