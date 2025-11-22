# 🚀 NodeAI Deployment Guide

Complete guide for deploying NodeAI to production.

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Backend Deployment Options](#backend-deployment-options)
4. [GitHub Setup](#github-setup)
5. [Environment Configuration](#environment-configuration)
6. [Post-Deployment](#post-deployment)

---

## 🔧 PREREQUISITES

- [ ] GitHub account
- [ ] Vercel account (for frontend)
- [ ] Supabase project (for auth & database)
- [ ] Sentry account (for error monitoring)
- [ ] Domain name (optional but recommended)

---

## 🎨 FRONTEND DEPLOYMENT (VERCEL)

### **Why Vercel?**
✅ Perfect for React/Vite apps  
✅ Free tier available  
✅ Automatic HTTPS  
✅ Global CDN  
✅ Auto-deploys from GitHub  

### **Step 1: Prepare Frontend**

```bash
# Test build locally first
cd frontend
npm install
npm run build

# Verify build works
npm run preview
```

### **Step 2: Deploy to Vercel**

#### **Option A: Via Vercel CLI** (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: nodeai (or your choice)
# - Directory: ./
# - Override settings? No
```

#### **Option B: Via Vercel Dashboard**

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import from GitHub: `Mettice/Node-AI`
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables (see below)
6. Click "Deploy"

### **Step 3: Frontend Environment Variables**

Add these in Vercel dashboard (Settings → Environment Variables):

```env
# API URL - CHANGE AFTER BACKEND DEPLOYMENT
VITE_API_URL=https://your-backend-url.com

# Supabase (same as backend)
VITE_SUPABASE_URL=https://yourproject.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### **Step 4: Configure Custom Domain** (Optional)

1. Go to Vercel dashboard → Settings → Domains
2. Add your domain: `app.your-domain.com`
3. Follow DNS configuration instructions
4. Wait for SSL certificate (automatic)

---

## 🖥️ BACKEND DEPLOYMENT OPTIONS

### **RECOMMENDED: Railway** 🚂

**Why Railway?**
- ✅ Easiest Python deployment
- ✅ Free $5/month credit
- ✅ Auto-scaling
- ✅ Built-in PostgreSQL (if needed)
- ✅ Deploy from GitHub
- ✅ Automatic HTTPS

#### **Deploy to Railway:**

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **Create New Project** → "Deploy from GitHub repo"
4. **Select**: `Mettice/Node-AI`
5. **Configure**:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. **Add Environment Variables** (see below)
7. **Deploy!**

Railway will give you a URL like: `https://your-app.up.railway.app`

---

### **ALTERNATIVE 1: Render** 🎨

**Why Render?**
- ✅ Free tier available
- ✅ Good for Python
- ✅ Auto-deploy from GitHub

#### **Deploy to Render:**

1. **Go to [render.com](https://render.com)**
2. **New Web Service** → Connect GitHub repo
3. **Configure**:
   - **Name**: nodeai-backend
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables**
5. **Create Web Service**

Free tier URL: `https://nodeai-backend.onrender.com`

---

### **ALTERNATIVE 2: DigitalOcean App Platform** 🌊

**Why DigitalOcean?**
- ✅ $5/month basic plan
- ✅ Reliable infrastructure
- ✅ Easy scaling

#### **Deploy to DigitalOcean:**

1. **Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)**
2. **Apps** → **Create App**
3. **GitHub** → Select `Mettice/Node-AI`
4. **Configure Component**:
   - **Type**: Web Service
   - **Source Directory**: `/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn backend.main:app --host 0.0.0.0 --port 8080`
5. **Environment Variables** (add all)
6. **Launch App**

---

### **ALTERNATIVE 3: Self-Hosted (VPS)** 🖥️

**For**: Ubuntu/Debian server

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Clone repo
git clone https://github.com/Mettice/Node-AI.git
cd Node-AI/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see below)
nano .env

# Run with Gunicorn
pip install gunicorn
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Set up systemd service (optional but recommended)
sudo nano /etc/systemd/system/nodeai.service
```

**systemd service file**:
```ini
[Unit]
Description=NodeAI Backend
After=network.target

[Service]
Type=notify
User=your-user
WorkingDirectory=/path/to/Node-AI/backend
Environment="PATH=/path/to/Node-AI/backend/venv/bin"
ExecStart=/path/to/Node-AI/backend/venv/bin/gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl enable nodeai
sudo systemctl start nodeai
```

---

## 🔐 ENVIRONMENT CONFIGURATION

### **Backend Environment Variables**

Add these to your deployment platform:

```env
# Application
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=NodeAI
APP_VERSION=0.1.0

# Server
HOST=0.0.0.0
PORT=8000

# CORS - ADD YOUR VERCEL URL
CORS_ORIGINS_STR=https://your-vercel-app.vercel.app,https://app.your-domain.com
CORS_ALLOW_ALL_ORIGINS=false

# Security - GENERATE NEW KEYS
JWT_SECRET_KEY=CHANGE-THIS-TO-A-RANDOM-32-CHAR-STRING
VAULT_ENCRYPTION_KEY=CHANGE-THIS-TO-A-HEX-STRING

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.yourproject.supabase.co:5432/postgres

# Monitoring
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Optional: API Keys (users can add via UI)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### **Generate Secure Keys**

```python
# Generate JWT Secret
import secrets
print(secrets.token_urlsafe(32))

# Generate Encryption Key
print(secrets.token_hex(32))
```

Or online: [1Password Generator](https://1password.com/password-generator/)

---

## 🐙 GITHUB SETUP

### **Step 1: Initialize Git** (if not done)

```powershell
# Navigate to project root
cd C:\Users\efuet\Nodeflow

# Initialize git
git init

# Add remote
git remote add origin https://github.com/Mettice/Node-AI.git

# Create main branch
git branch -M main
```

### **Step 2: Commit and Push**

```powershell
# Add all files (gitignore will exclude sensitive data)
git add .

# Commit
git commit -m "Initial commit: NodeAI v0.1.0 - Beta ready"

# Push
git push -u origin main
```

### **Step 3: Verify**

Check https://github.com/Mettice/Node-AI - your code should be there!

---

## 🧪 POST-DEPLOYMENT TESTING

### **1. Backend Health Check**

```bash
curl https://your-backend-url.com/api/v1/health

# Expected:
{
  "status": "healthy",
  "app_name": "NodeAI",
  "version": "0.1.0"
}
```

### **2. Frontend Check**

Visit your Vercel URL and verify:
- [ ] Page loads
- [ ] Can reach login page
- [ ] No console errors

### **3. Full Flow Test**

1. Register new user
2. Verify email
3. Login
4. Create workflow
5. Execute workflow
6. Check results

---

## 🔄 CONTINUOUS DEPLOYMENT

### **Automatic Deploys**

Both Vercel and Railway auto-deploy on git push:

```powershell
# Make changes
git add .
git commit -m "Add new feature"
git push

# Vercel: Deploys frontend automatically
# Railway: Deploys backend automatically
```

### **Preview Deployments**

Create a branch for testing:

```powershell
git checkout -b feature/new-feature
git push origin feature/new-feature

# Vercel creates preview URL automatically
# Test before merging to main
```

---

## 📊 RECOMMENDED ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│                    Users                            │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│          Vercel (Frontend)                           │
│  https://your-app.vercel.app                         │
│  - React + Vite                                      │
│  - Global CDN                                        │
│  - Auto HTTPS                                        │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│       Railway/Render (Backend)                       │
│  https://your-api.railway.app                        │
│  - FastAPI                                           │
│  - Python 3.11+                                      │
│  - Auto-scaling                                      │
└──────┬───────────────────────────────────────────────┘
       │
       ├──────────────────────┬───────────────────────┐
       ▼                      ▼                       ▼
┌────────────┐      ┌──────────────┐      ┌──────────────┐
│  Supabase  │      │    Sentry    │      │   AI APIs    │
│  Auth/DB   │      │  Monitoring  │      │ OpenAI, etc  │
└────────────┘      └──────────────┘      └──────────────┘
```

---

## 💰 COST ESTIMATE

### **Free Tier** (Perfect for Beta)

- **Vercel**: Free (100GB bandwidth/month)
- **Railway**: $5/month credit (covers ~500MB RAM)
- **Supabase**: Free (500MB database, 50,000 auth users)
- **Sentry**: Free (5,000 errors/month)

**Total**: ~$0-5/month for beta testing

### **Production** (After Beta)

- **Vercel Pro**: $20/month (more bandwidth)
- **Railway**: $5-20/month (depends on usage)
- **Supabase Pro**: $25/month (8GB database)
- **Sentry**: $26/month (50,000 errors/month)

**Total**: ~$76-91/month for production

---

## 🎯 DEPLOYMENT CHECKLIST

### **Before First Deploy**

- [x] `.gitignore` files created
- [ ] Environment variables prepared
- [ ] Supabase project created
- [ ] Sentry project created
- [ ] Test build locally (frontend & backend)

### **Deploy Frontend**

- [ ] Push to GitHub
- [ ] Connect Vercel to GitHub repo
- [ ] Configure build settings
- [ ] Add environment variables
- [ ] Deploy and test

### **Deploy Backend**

- [ ] Choose platform (Railway recommended)
- [ ] Connect to GitHub
- [ ] Configure build command
- [ ] Add ALL environment variables
- [ ] Deploy and test health endpoint

### **Connect Frontend to Backend**

- [ ] Update `VITE_API_URL` in Vercel
- [ ] Update `CORS_ORIGINS_STR` in backend
- [ ] Redeploy both
- [ ] Test end-to-end

### **Final Checks**

- [ ] User registration works
- [ ] Login works
- [ ] Workflow creation works
- [ ] Workflow execution works
- [ ] No errors in Sentry
- [ ] SSL certificates active (HTTPS)

---

## 🚨 TROUBLESHOOTING

### **Frontend can't reach backend**

1. Check `VITE_API_URL` is correct
2. Check backend CORS settings
3. Check backend is running (health endpoint)

### **Backend deployment fails**

1. Check all environment variables are set
2. Check build logs for errors
3. Verify `requirements.txt` is correct
4. Check Python version (3.11+ required)

### **Database connection fails**

1. Verify `DATABASE_URL` format
2. Check Supabase project is active
3. Test connection with Supabase dashboard

---

## 🎉 SUCCESS!

Once deployed, your URLs will be:

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-api.railway.app`
- **API Docs**: `https://your-api.railway.app/docs` (only if DEBUG=true)

Share the frontend URL with beta testers and start collecting feedback!

---

## 📚 ADDITIONAL RESOURCES

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

**Need help?** Check the deployment audit: `DEPLOYMENT_READINESS_AUDIT.md`

**Last Updated**: 2024-11-22  
**Version**: 1.0

