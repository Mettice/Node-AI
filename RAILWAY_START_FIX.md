# 🔧 Fix Railway Import Error

## **Problem**

```
ModuleNotFoundError: No module named 'backend.core'
```

Railway is running from `backend/` directory, but code imports `backend.*`.

---

## **✅ Solution: Change Start Command**

### **Option 1: Run from Project Root (Recommended)**

1. Railway Dashboard → Settings
2. **Root Directory**: Leave **EMPTY** (or set to `.`)
3. **Start Command**:
   ```
   cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. **Save** → Redeploy

### **Option 2: Keep Root Directory as `backend`**

1. Railway Dashboard → Settings
2. **Root Directory**: `backend` (keep as is)
3. **Start Command**:
   ```
   PYTHONPATH=/app uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. **Save** → Redeploy

---

## **🎯 I Recommend Option 1**

**Root Directory**: Empty (`.`)
**Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

This way:
- Railway sees the whole project
- Can find `backend/requirements.txt`
- Start command changes to backend directory
- Imports work correctly ✅

---

**Try Option 1 - it should work!** 🚀

