# 🚀 Deploy NodeAI to Vercel (Complete Guide)

Deploy both frontend and backend to Vercel in one project!

---

## 📋 **WHAT YOU GET**

- **Frontend**: React app at `https://your-app.vercel.app`
- **Backend**: FastAPI at `https://your-app.vercel.app/api/*`
- **One domain**: No CORS issues!
- **Auto-deploy**: Push to GitHub = automatic deployment

---

## ⚙️ **PREREQUISITE: SUPABASE SETUP**

### **Step 1: Create Supabase Project**

1. Go to [supabase.com](https://supabase.com)
2. **New Project**
3. Name: `nodeai-production`
4. Database Password: (save this!)
5. Region: Choose closest to your users
6. **Create Project** (takes ~2 minutes)

### **Step 2: Get Supabase Credentials**

Once created, go to **Settings** → **API**:

Copy these 4 values:
```
Project URL: https://xxxxxxxxxxxxx.supabase.co
anon/public key: eyJhbG...
service_role key: eyJhbG...
```

Go to **Settings** → **Database**:

Copy this:
```
Connection string (URI): postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

**Save all these!** You'll need them in Step 5.

---

## 🚀 **VERCEL DEPLOYMENT**

### **Step 1: Push to GitHub**

```powershell
# Make sure you've committed the new files
git add .
git commit -m "Add Vercel deployment config"
git push
```

### **Step 2: Connect to Vercel**

1. Go to [vercel.com](https://vercel.com)
2. **Sign in with GitHub**
3. **Add New Project**
4. **Import** `Mettice/Node-AI`

### **Step 3: Configure Project**

On the import page:

**Framework Preset**: Other

**Root Directory**: `./` (leave as is)

**Build Settings**:
- Build Command: `cd frontend && npm install && npm run build`
- Output Directory: `frontend/dist`
- Install Command: `npm install`

### **Step 4: Environment Variables**

Click **"Environment Variables"** and add these:

#### **Frontend Variables**

```env
VITE_API_URL=/api
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

#### **Backend Variables**

```env
# Application
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=NodeAI
APP_VERSION=0.1.0

# Server
HOST=0.0.0.0
PORT=8000

# CORS - Same domain, use relative path
CORS_ORIGINS_STR=https://your-app.vercel.app
CORS_ALLOW_ALL_ORIGINS=false

# Security - GENERATE NEW KEYS
JWT_SECRET_KEY=<generate-random-32-chars>
VAULT_ENCRYPTION_KEY=<generate-random-hex>

# Supabase (from Step 1)
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
DATABASE_URL=postgresql://postgres:<password>@db.yourproject.supabase.co:5432/postgres

# Monitoring (Optional)
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# API Keys (Optional - users can add via UI)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# PINECONE_API_KEY=...
# COHERE_API_KEY=...
# VOYAGE_API_KEY=...
# GEMINI_API_KEY=...
```

**Important**: 
- Replace `<generate-random-32-chars>` with a secure key
- Replace `<password>` in DATABASE_URL with your Supabase password
- Update `CORS_ORIGINS_STR` after deployment with your actual Vercel URL

### **Step 5: Deploy!**

Click **"Deploy"**

Vercel will:
1. Clone your repo
2. Install dependencies
3. Build frontend
4. Deploy serverless functions
5. Give you a URL

**First deployment takes 2-3 minutes**

---

## ✅ **POST-DEPLOYMENT**

### **Step 1: Get Your URL**

Vercel gives you: `https://node-ai-xxx.vercel.app`

### **Step 2: Update CORS**

Go back to Vercel dashboard:
1. **Settings** → **Environment Variables**
2. Find `CORS_ORIGINS_STR`
3. Update to: `https://node-ai-xxx.vercel.app` (your actual URL)
4. **Save**
5. **Deployments** → **Redeploy** (click ⋯ on latest deployment)

### **Step 3: Test Backend**

Visit: `https://your-app.vercel.app/api/v1/health`

Expected response:
```json
{
  "status": "healthy",
  "app_name": "NodeAI",
  "version": "0.1.0"
}
```

### **Step 4: Test Frontend**

1. Visit `https://your-app.vercel.app`
2. Click **"Register"**
3. Create account
4. Check email for verification (Supabase sends it)
5. Login
6. Create a workflow
7. Execute workflow ✅

---

## 🔐 **GENERATE SECURE KEYS**

### **For JWT_SECRET_KEY and VAULT_ENCRYPTION_KEY**

**Option 1: Python** (in PowerShell with Python):
```python
python -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(32)); print('VAULT_ENCRYPTION_KEY:', secrets.token_hex(32))"
```

**Option 2: Online**
- Go to [1password.com/password-generator](https://1password.com/password-generator/)
- Length: 32 characters
- Include: Letters, numbers, symbols
- Generate two keys

---

## 📁 **FILE STORAGE ON VERCEL**

⚠️ **Important**: Vercel is **ephemeral** (files don't persist between deployments)

**For file uploads, you have 3 options:**

### **Option 1: Vercel Blob Storage** (Recommended)

```bash
npm i @vercel/blob
```

Update backend to use Vercel Blob for file storage.

### **Option 2: AWS S3**

```env
# Add to Vercel environment variables
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=nodeai-uploads
AWS_REGION=us-east-1
```

### **Option 3: Supabase Storage**

```env
# Add to Vercel environment variables
SUPABASE_STORAGE_BUCKET=uploads
```

**For now**: Files work but won't persist across redeployments. Add persistent storage before production.

---

## 🔄 **CONTINUOUS DEPLOYMENT**

Once set up, deployment is automatic:

```powershell
# Make changes
git add .
git commit -m "Add new feature"
git push

# Vercel automatically:
# 1. Detects push
# 2. Builds project
# 3. Deploys
# 4. Updates URL
```

**Preview Deployments**: 
- Create branch → Push → Get preview URL
- Test before merging to main

---

## 🌐 **CUSTOM DOMAIN** (Optional)

### **Step 1: Add Domain**

1. Vercel Dashboard → **Settings** → **Domains**
2. Add your domain: `app.yourdomain.com`

### **Step 2: Configure DNS**

Add these records to your DNS provider:

**Type**: `CNAME`  
**Name**: `app`  
**Value**: `cname.vercel-dns.com`

### **Step 3: Wait for SSL**

Vercel automatically provisions SSL (5-10 minutes)

### **Step 4: Update CORS**

Update `CORS_ORIGINS_STR` in Vercel to include your custom domain:

```env
CORS_ORIGINS_STR=https://app.yourdomain.com,https://node-ai-xxx.vercel.app
```

---

## 📊 **MONITORING**

### **Vercel Analytics**

Already included! View in dashboard:
- Page views
- Performance metrics
- Geography

### **Vercel Logs**

View real-time logs:
1. Dashboard → **Deployments**
2. Click deployment → **Logs**
3. See backend logs in real-time

### **Sentry** (Optional)

If you added SENTRY_DSN:
1. Go to [sentry.io](https://sentry.io)
2. View errors in real-time
3. Get alerts

---

## 🚨 **TROUBLESHOOTING**

### **Backend returns 404**

**Cause**: API routing not configured

**Fix**: Check `vercel.json` routes are correct:
```json
{
  "src": "/api/(.*)",
  "dest": "backend/vercel_app.py"
}
```

### **Frontend can't reach backend**

**Cause**: Wrong API URL

**Fix**: Ensure `VITE_API_URL=/api` (relative path)

### **Build fails**

**Cause**: Missing dependencies

**Fix**: 
1. Check `backend/requirements.txt` is complete
2. Check `frontend/package.json` is correct
3. View build logs for specific error

### **Database connection fails**

**Cause**: Wrong DATABASE_URL format

**Fix**: Format must be:
```
postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
```
- Replace `PASSWORD` with your actual password
- Replace `PROJECT` with your Supabase project ID

### **Cold starts are slow**

**Cause**: Serverless functions sleep when idle

**Fix**: 
- Vercel Pro has faster cold starts
- Use Vercel Edge Functions for instant start
- Or deploy backend to Railway separately

---

## 💰 **VERCEL PRICING**

### **Hobby (Free)**
- ✅ Perfect for beta testing
- ✅ 100GB bandwidth/month
- ✅ Unlimited deployments
- ✅ Automatic HTTPS
- ✅ Preview deployments
- ⚠️ Slower serverless cold starts

### **Pro ($20/month)**
- ✅ 1TB bandwidth
- ✅ Faster cold starts
- ✅ Analytics included
- ✅ Team features
- ✅ Priority support

**Recommendation**: Start with Hobby, upgrade to Pro when needed

---

## 🎯 **DEPLOYMENT CHECKLIST**

### **Before First Deploy**

- [ ] Supabase project created
- [ ] All credentials copied
- [ ] JWT secret generated
- [ ] Vault key generated
- [ ] Code pushed to GitHub

### **During Deploy**

- [ ] Project connected to Vercel
- [ ] Build settings configured
- [ ] All environment variables added
- [ ] Deploy button clicked

### **After Deploy**

- [ ] Health endpoint works
- [ ] Frontend loads
- [ ] Can register user
- [ ] Email verification works
- [ ] Can login
- [ ] Can create workflow
- [ ] Can execute workflow
- [ ] CORS updated with real URL
- [ ] Redeployed with new CORS

---

## 🎉 **SUCCESS!**

Your app is now live at:
- **App**: `https://your-app.vercel.app`
- **API**: `https://your-app.vercel.app/api/v1/*`
- **Health**: `https://your-app.vercel.app/api/v1/health`

---

## 📚 **NEXT STEPS**

1. **Add Custom Domain** (optional)
2. **Set up monitoring** (Sentry)
3. **Configure file storage** (Vercel Blob or S3)
4. **Invite beta testers**
5. **Collect feedback**
6. **Iterate and improve**

---

## 🆘 **NEED HELP?**

- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Issues**: https://github.com/Mettice/Node-AI/issues

---

**Happy Deploying!** 🚀

**Last Updated**: 2024-11-22  
**Version**: 1.0

