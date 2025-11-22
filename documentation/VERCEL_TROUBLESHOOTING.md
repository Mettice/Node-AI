# 🔧 Vercel Deployment Troubleshooting

## ❌ "Deployed but not serving"

### **Common Issues & Fixes**

---

## 1. ✅ **SPA Routing (Most Common)**

**Problem**: Routes like `/workflows` return 404

**Fix**: Already added `rewrites` to `frontend/vercel.json` ✅

If still not working, check Vercel dashboard:
- Settings → General → Framework Preset: **Vite**
- Settings → General → Root Directory: **frontend**

---

## 2. 🔑 **Missing Environment Variables**

**Problem**: App loads but API calls fail

**Required Variables** (Vercel Dashboard → Settings → Environment Variables):

```env
VITE_API_URL=https://your-backend.up.railway.app
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**How to add**:
1. Go to Vercel Dashboard
2. Select your project
3. Settings → Environment Variables
4. Add each variable
5. **Redeploy** (Deployments → ... → Redeploy)

---

## 3. 📁 **Wrong Root Directory**

**Problem**: Build fails or can't find files

**Fix**:
1. Vercel Dashboard → Settings → General
2. **Root Directory**: `frontend`
3. Save → Redeploy

---

## 4. 🏗️ **Build Configuration**

**Check** (Vercel Dashboard → Settings → General):

- **Framework Preset**: `Vite`
- **Build Command**: `npm run build` (or leave empty, auto-detected)
- **Output Directory**: `dist`
- **Install Command**: `npm install` (or leave empty)

---

## 5. 🌐 **CORS Issues**

**Problem**: API calls blocked by CORS

**Fix**: Update backend CORS to include your Vercel URL:

```env
# In Railway (backend) environment variables:
CORS_ORIGINS_STR=https://your-app.vercel.app
```

---

## 6. 🔍 **Check Build Logs**

1. Vercel Dashboard → Deployments
2. Click on latest deployment
3. Check **Build Logs** tab
4. Look for errors

**Common errors**:
- `Module not found` → Missing dependencies
- `Environment variable not found` → Add env vars
- `Build failed` → Check TypeScript errors

---

## 7. 🧪 **Test Locally First**

Before deploying, test the build locally:

```powershell
cd frontend
npm install
npm run build
npm run preview  # Test production build
```

If this works, Vercel should work too.

---

## 8. 🔄 **Force Redeploy**

Sometimes Vercel needs a fresh build:

1. Vercel Dashboard → Deployments
2. Click **...** on latest deployment
3. **Redeploy**
4. Wait 2-3 minutes

---

## 9. 📊 **Check Deployment Status**

**Healthy deployment shows**:
- ✅ Status: **Ready**
- ✅ Build: **Success**
- ✅ Runtime: **Node.js 20.x**

**Unhealthy shows**:
- ❌ Status: **Error**
- ❌ Build: **Failed**
- Check logs for details

---

## 10. 🎯 **Quick Diagnostic Checklist**

Run through this checklist:

- [ ] Root Directory set to `frontend`?
- [ ] Framework Preset set to `Vite`?
- [ ] Environment variables added?
- [ ] Build logs show success?
- [ ] Deployment status is "Ready"?
- [ ] Can access `https://your-app.vercel.app`?
- [ ] Browser console shows no errors?
- [ ] Network tab shows API calls (even if failing)?

---

## 🚨 **Still Not Working?**

### **Get More Info**

1. **Browser Console** (F12):
   - Check for JavaScript errors
   - Check Network tab for failed requests

2. **Vercel Logs**:
   - Dashboard → Deployments → Latest → Functions Logs
   - Look for runtime errors

3. **Test API Directly**:
   - Visit: `https://your-backend.up.railway.app/api/v1/health`
   - Should return: `{"status": "healthy"}`

4. **Check Environment Variables**:
   - Vercel Dashboard → Settings → Environment Variables
   - Make sure all `VITE_*` variables are set
   - **Important**: Redeploy after adding env vars!

---

## ✅ **Expected Working State**

When everything works:

1. **Frontend URL**: `https://your-app.vercel.app`
   - ✅ Loads without errors
   - ✅ Shows login/register page
   - ✅ Can navigate to `/workflows`

2. **Backend URL**: `https://your-backend.up.railway.app/api/v1/health`
   - ✅ Returns: `{"status": "healthy"}`

3. **Integration**:
   - ✅ Frontend can call backend API
   - ✅ No CORS errors in console
   - ✅ Authentication works

---

## 📞 **Need Help?**

Share these details:
1. Vercel deployment URL
2. Build logs (screenshot)
3. Browser console errors (screenshot)
4. Network tab (failed requests)

This will help diagnose the issue quickly! 🔍

