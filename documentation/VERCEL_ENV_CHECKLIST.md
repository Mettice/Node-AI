# ✅ Vercel Environment Variables Checklist

## **Current Status Review**

Based on your Vercel settings, here's what needs to be fixed:

---

## **🔴 Issues to Fix**

### **1. Remove Trailing Slashes**

**Problem**: URLs have trailing slashes (`/`) which can cause routing issues.

**Fix**:
- ❌ `VITE_API_URL`: `https://nodai-nu.vercel.app/`
- ✅ `VITE_API_URL`: `https://nodai-nu.vercel.app`

- ❌ `CORS_ORIGINS_STR`: `https://nodai-nu.vercel.app/`
- ✅ `CORS_ORIGINS_STR`: `https://nodai-nu.vercel.app`

**How to fix**:
1. Vercel Dashboard → Settings → Environment Variables
2. Edit `VITE_API_URL` → Remove trailing `/`
3. Edit `CORS_ORIGINS_STR` → Remove trailing `/`
4. Save → Redeploy

---

### **2. Add Missing VAULT_ENCRYPTION_KEY**

**Problem**: `VAULT_ENCRYPTION_KEY` is missing (needed for secrets vault).

**How to generate**:

**Option A: Using Python script** (recommended)
```powershell
python generate-vault-key.py
```

**Option B: Using Python directly**
```powershell
python -c "import secrets; print(secrets.token_bytes(32).hex())"
```

**Option C: Using PowerShell**
```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[System.BitConverter]::ToString($bytes).Replace('-', '').ToLower()
```

**Then add to Vercel**:
- Key: `VAULT_ENCRYPTION_KEY`
- Value: `[generated-64-character-hex-string]`
- Environment: Production, Preview, Development (all)

---

## **✅ What's Already Correct**

- ✅ `SUPABASE_URL` - Correct
- ✅ `SUPABASE_ANON_KEY` - Correct
- ✅ `DATABASE_URL` - Correct
- ✅ `DEBUG` - Set to `false` (correct for production)
- ✅ `JWT_SECRET_KEY` - Has value (good!)
- ✅ `VITE_SUPABASE_URL` - Correct
- ✅ `VITE_SUPABASE_ANON_KEY` - Correct

---

## **⚠️ About the Warnings**

The warnings about `VITE_*` keys are **NORMAL** and **SAFE**:

- `VITE_*` variables are **meant to be public** (included in frontend bundle)
- `VITE_SUPABASE_ANON_KEY` is **safe to expose** (it's designed to be public)
- `VITE_API_URL` is **safe to expose** (it's just a URL)

**You can ignore these warnings** ✅

---

## **📋 Complete Checklist**

### **Backend Variables** (Required)
- [x] `SUPABASE_URL` ✅
- [x] `SUPABASE_ANON_KEY` ✅
- [x] `DATABASE_URL` ✅
- [x] `DEBUG` ✅ (set to `false`)
- [x] `JWT_SECRET_KEY` ✅
- [ ] `VAULT_ENCRYPTION_KEY` ❌ **MISSING - ADD THIS**
- [ ] `CORS_ORIGINS_STR` ⚠️ **FIX: Remove trailing slash**

### **Frontend Variables** (Required)
- [ ] `VITE_API_URL` ⚠️ **FIX: Remove trailing slash**
- [x] `VITE_SUPABASE_URL` ✅
- [x] `VITE_SUPABASE_ANON_KEY` ✅

### **Optional Variables** (Nice to have)
- [ ] `LOG_LEVEL` (defaults to `INFO` if not set)
- [ ] `SENTRY_DSN` (for error tracking)
- [ ] `SENTRY_ENVIRONMENT` (defaults to `development`)

---

## **🚀 After Fixing**

1. **Save** all environment variable changes
2. **Redeploy** (Deployments → ... → Redeploy)
3. **Test**:
   - Visit: `https://nodai-nu.vercel.app`
   - Should load without errors ✅
   - Try creating a workflow ✅
   - Try saving API keys to vault ✅

---

## **🔐 Security Notes**

### **Keep Secret** (Never expose):
- `JWT_SECRET_KEY` ✅
- `VAULT_ENCRYPTION_KEY` ✅ (when you add it)
- `SUPABASE_SERVICE_ROLE_KEY` (if you add it)
- `DATABASE_URL` ✅

### **Safe to Expose** (Public):
- `VITE_*` variables (included in frontend bundle)
- `VITE_SUPABASE_ANON_KEY` (designed to be public)
- `VITE_API_URL` (just a URL)

---

## **📝 Quick Fix Steps**

1. **Generate vault key**:
   ```powershell
   python generate-vault-key.py
   ```

2. **Add to Vercel**:
   - Key: `VAULT_ENCRYPTION_KEY`
   - Value: `[copy from script output]`

3. **Fix trailing slashes**:
   - Edit `VITE_API_URL` → Remove `/` at end
   - Edit `CORS_ORIGINS_STR` → Remove `/` at end

4. **Redeploy**:
   - Deployments → ... → Redeploy

5. **Test** ✅

---

**Ready?** Run `python generate-vault-key.py` and add it to Vercel! 🔑

