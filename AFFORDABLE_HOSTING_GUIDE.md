# Affordable Hosting Guide for API-Assistant

**Perfect for:** Students, hobbyists, small projects, MVP/prototypes
**Budget:** $0 - $25/month
**Last Updated:** 2026-01-04

This guide covers affordable hosting options with generous free tiers and simple deployment.

---

## 🆓 Free Tier Comparison

| Platform | Free Tier | Best For | Limitations |
|----------|-----------|----------|-------------|
| **Vercel** | Unlimited deployments | Frontend (Next.js) | No backend support |
| **Railway** | $5 free credit/month | Full-stack (backend+frontend) | Credit-based, ~500 hours |
| **Render** | Free tier | Backend + static frontend | Spins down after 15min idle |
| **Fly.io** | 3 VMs free | Backend with DB | 256MB RAM limit |
| **Supabase** | Free PostgreSQL | Database only | 500MB limit |
| **Cloudflare Pages** | Unlimited | Frontend only | No backend |

---

## 🏆 Recommended Setup (FREE)

### **Best Free Combo: Vercel (Frontend) + Railway (Backend)**

**Total Cost:** $0 - $5/month
**Pros:**
- Vercel: Blazing fast Next.js hosting
- Railway: Simple backend deployment with persistent storage
- Both have excellent DX (developer experience)
- Auto-deploy from GitHub

**Cons:**
- Railway free credit runs out after ~500 hours/month
- Need to manage two platforms

---

## Option 1: Vercel (Frontend) + Railway (Backend)

### A. Deploy Backend to Railway

#### 🎯 Quick Overview

**What we'll do:**
1. Create Railway account → Get $5 free credit
2. Connect GitHub repo or use CLI → Deploy backend
3. Configure start command → `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`
4. Add environment variables → API keys, secrets, LLM config
5. Add persistent volume → `/app/data` for ChromaDB storage
6. Get public URL → Test backend is live

**Time required:** 15-20 minutes
**Cost:** Free (uses $5 credit, ~500 hours/month)

---

#### Prerequisites

Before deploying, ensure you have:
- ✅ `requirements.txt` file in your project root
- ✅ Your code pushed to GitHub (for Method 1) or committed locally (for Method 2)
- ✅ Python 3.11+ specified (Railway will auto-detect)

---

#### Method 1: Deploy from GitHub (Recommended - Easier)

**Step 1: Create Railway Account**
1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Sign up with GitHub (recommended for easier deployment)
4. You'll get **$5 free credit** to start with

**Step 2: Push Your Code to GitHub (if not already)**
```bash
cd /home/user/Api-Assistant

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

**Step 3: Create New Railway Project from GitHub**
1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select your repository (e.g., `YOUR_USERNAME/Api-Assistant`)
5. Railway will detect it's a Python project

**Step 4: Configure Service Settings**
1. Railway will create a service automatically
2. Click on the service card to open it
3. Go to **"Settings"** tab (inside the service)
4. Under **"Deploy"** section:
   - **Root Directory:** Leave as `/` (or set to backend folder if you have one)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`
5. Under **"Networking"**:
   - Click **"Generate Domain"** to get a public URL
   - Copy this URL (e.g., `https://api-assistant-backend-production-xxxx.up.railway.app`)

---

#### Method 2: Deploy via Railway CLI (Alternative)

**Step 1: Install Railway CLI**
```bash
npm i -g @railway/cli
```

**Step 2: Login and Initialize**
```bash
cd /home/user/Api-Assistant

# Login to Railway
railway login

# Create new project
railway init
# Enter project name: api-assistant-backend
# This creates a new project and links your local directory
```

**Step 3: Generate Domain**
```bash
# Generate a public domain for your service
railway domain
# Copy the generated URL
```

---

**Step 5: Configure Environment Variables**

1. In Railway dashboard, click on your backend service
2. Click the **"Variables"** tab
3. Click **"New Variable"**
4. Add the following variables one by one:

```bash
# CRITICAL
SECRET_KEY=<generate-new-secret>
API_KEYS=<generate-new-keys>
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
REQUIRE_AUTH=true

# LLM
GROQ_API_KEY=<your-groq-key>
LLM_PROVIDER=groq
GROQ_REASONING_MODEL=llama-3.3-70b-versatile
GROQ_CODE_MODEL=llama-3.3-70b-versatile
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ChromaDB
CHROMA_PERSIST_DIR=/app/data/chroma_db
CHROMA_COLLECTION_NAME=api_docs

# App Settings
DEBUG=false
LOG_LEVEL=INFO
```

**Step 6: Add Volume for Persistent Storage**

⚠️ **CRITICAL**: Without a volume, all uploaded documents will be lost on every redeploy!

**Via Railway Dashboard:**
1. Go to your Railway dashboard (not Project Settings)
2. Click on your **backend service** (the FastAPI app)
3. Click the **"Settings"** tab (inside the service)
4. Scroll down to **"Volumes"** section
5. Click **"+ New Volume"** or **"Add Volume"**
6. Configure:
   - Mount path: `/app/data`
   - Size: 1GB (free tier)
7. Click "Add" - Railway will automatically redeploy

**Via Railway CLI (Alternative):**
```bash
railway volume add --mount-path /app/data --size 1
```

**Without Volume:**
- Default: ~10GB ephemeral (temporary) storage
- Data is **deleted on every deployment/restart**
- Not suitable for production use

**Step 7: Deploy Your Application**

**If using GitHub method:**
- Railway automatically deploys when you connect the repo
- Every git push to main branch will trigger auto-deployment
- Go to **"Deployments"** tab to see build logs
- Wait for deployment to complete (status: "Success")

**If using CLI method:**
```bash
# Add Procfile (if not exists)
echo "web: uvicorn src.api.app:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
railway up

# Check deployment status
railway status
```

**Step 8: Get Your Backend URL**

1. Go to your service in Railway dashboard
2. Click **"Settings"** tab
3. Under **"Networking"**, you'll see your public domain
4. Copy the URL (e.g., `https://api-assistant-backend-production-xxxx.up.railway.app`)
5. Test it by visiting: `https://your-url.railway.app/health`
   - Should return: `{"status": "healthy"}`

**Your Railway backend is now live! 🎉**

---

#### Railway UI Navigation Guide

**Understanding Railway's Structure:**
```
Railway Dashboard
├── Projects (top level)
│   └── Your Project (e.g., "api-assistant-backend")
│       └── Services (your deployed apps)
│           └── Backend Service ← Click here to configure
│               ├── Deployments tab (view build logs)
│               ├── Variables tab (environment variables)
│               ├── Metrics tab (CPU, RAM usage)
│               ├── Logs tab (runtime logs)
│               └── Settings tab (volumes, networking, commands)
│                   ├── Deploy section (build/start commands)
│                   ├── Networking section (generate domain)
│                   └── Volumes section (persistent storage)
```

**Important:**
- ⚠️ **Project Settings** (gear icon in sidebar) ≠ **Service Settings**
- Always click on your **service card/box** first, then access settings inside it
- Volumes are in **Service Settings**, not Project Settings

---

#### Common Railway Deployment Issues

**Issue 1: "Build failed" or "Deploy failed"**
- **Solution:** Check "Deployments" tab → Click failed deployment → View logs
- Common causes:
  - Missing `requirements.txt`
  - Wrong start command
  - Missing environment variables

**Issue 2: "Application failed to respond"**
- **Solution:** Ensure start command uses `--port $PORT` (Railway sets PORT variable)
- Correct: `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`
- Wrong: `uvicorn src.api.app:app --port 8000`

**Issue 3: "Can't find Volumes option"**
- **Solution:**
  1. Click on your **service** (the box/card with your app name)
  2. Inside the service, click **"Settings"** tab
  3. Scroll down to **"Volumes"** section
  - If still not visible, use CLI: `railway volume add --mount-path /app/data --size 1`

**Issue 4: "No public URL/domain"**
- **Solution:** Go to service Settings → Networking → Click "Generate Domain"

**Issue 5: "Environment variables not working"**
- **Solution:** After adding variables, Railway auto-redeploys. Wait for new deployment to finish.

---

### B. Deploy Frontend to Vercel

**1. Install Vercel CLI**
```bash
npm i -g vercel
```

**2. Deploy**
```bash
cd frontend

# Login
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: api-assistant
# - Directory: ./ (current)
# - Override settings? No
```

**3. Configure Environment Variables**

In Vercel dashboard (https://vercel.com):
- Go to your project
- Settings → Environment Variables
- Add:

```bash
NEXT_PUBLIC_API_URL=https://your-railway-backend.up.railway.app
NEXT_PUBLIC_API_KEY=<your-generated-api-key>
```

**4. Redeploy**
```bash
vercel --prod
```

**Vercel will give you:** `https://your-app.vercel.app`

### C. Update Backend CORS

Update Railway environment variables:
```bash
ALLOWED_ORIGINS=https://your-app.vercel.app
```

Redeploy Railway backend.

---

## Option 2: Render (All-in-One)

**Cost:** Free (with limitations)
**Pros:** Simple, one platform for everything
**Cons:** Free tier spins down after 15min inactivity (slow cold starts)

### Deploy to Render

**1. Create account:** https://render.com

**2. New Web Service**
- Dashboard → "New" → "Web Service"
- Connect GitHub repository
- Name: `api-assistant-backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`

**3. Environment Variables**

Add in Render dashboard:
```bash
SECRET_KEY=<generate-new>
API_KEYS=<generate-new>
ALLOWED_ORIGINS=https://your-app.onrender.com
REQUIRE_AUTH=true
GROQ_API_KEY=<your-key>
PYTHON_VERSION=3.11.0
```

**4. Add Persistent Disk**

- Settings → "Disks"
- Mount path: `/app/data`
- Size: 1GB (free)

**5. Deploy Frontend**

- New → "Static Site"
- Connect same repository
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/out`

**Environment Variables:**
```bash
NEXT_PUBLIC_API_URL=https://api-assistant-backend.onrender.com
NEXT_PUBLIC_API_KEY=<your-api-key>
```

**Your URLs:**
- Backend: `https://api-assistant-backend.onrender.com`
- Frontend: `https://your-app.onrender.com`

---

## Option 3: Fly.io (Full Control)

**Cost:** Free tier (3 VMs, 256MB RAM each)
**Pros:** More control, doesn't spin down
**Cons:** More complex setup

### Deploy to Fly.io

**1. Install flyctl**
```bash
curl -L https://fly.io/install.sh | sh
```

**2. Login**
```bash
flyctl auth login
```

**3. Launch App**
```bash
cd /home/user/Api-Assistant

# Create fly.toml
flyctl launch --name api-assistant

# Follow prompts:
# - Copy configuration? No
# - Would you like to set up a PostgreSQL database? No
# - Would you like to deploy now? No
```

**4. Configure fly.toml**

Edit `fly.toml`:
```toml
app = "api-assistant"

[build]
  builder = "paketobuildpacks/builder:base"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[mounts]
  source = "chroma_data"
  destination = "/app/data"

[env]
  PORT = "8000"
```

**5. Set Secrets**
```bash
flyctl secrets set SECRET_KEY="your-secret"
flyctl secrets set API_KEYS="your-keys"
flyctl secrets set GROQ_API_KEY="your-groq-key"
flyctl secrets set ALLOWED_ORIGINS="https://your-frontend.vercel.app"
flyctl secrets set REQUIRE_AUTH="true"
```

**6. Create Volume**
```bash
flyctl volumes create chroma_data --size 1
```

**7. Deploy**
```bash
flyctl deploy
```

**Your URL:** `https://api-assistant.fly.dev`

Deploy frontend to Vercel (same as Option 1B).

---

## Option 4: Docker + Cloud Run (Google Cloud)

**Cost:** Free tier = 2 million requests/month
**Pros:** Serverless, scales to zero
**Cons:** Requires Google Cloud account

### Deploy to Cloud Run

**1. Build Docker Image**
```bash
cd /home/user/Api-Assistant

# Build
docker build -t gcr.io/YOUR_PROJECT_ID/api-assistant .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/api-assistant
```

**2. Deploy**
```bash
gcloud run deploy api-assistant \
  --image gcr.io/YOUR_PROJECT_ID/api-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY="your-secret",API_KEYS="your-keys",REQUIRE_AUTH="true"
```

---

## Cost Estimates

### Free Tier Limits

| Platform | Compute | Storage | Bandwidth | Limitations |
|----------|---------|---------|-----------|-------------|
| **Vercel** | Unlimited | 100GB | 100GB/month | Frontend only |
| **Railway** | $5 credit | 1GB | Unlimited | ~500 hours/month |
| **Render** | 750 hours | 1GB | 100GB/month | Spins down idle |
| **Fly.io** | 3 VMs | 3GB total | 160GB/month | 256MB RAM each |

### Paid Tier (When You Outgrow Free)

| Platform | Monthly Cost | What You Get |
|----------|--------------|--------------|
| **Railway** | $5/month | ~500 hours, more resources |
| **Render** | $7/month | Always-on, 0.5GB RAM |
| **Fly.io** | $1.94/VM | 256MB RAM VMs |
| **DigitalOcean** | $4-6/month | Basic Droplet |

---

## Recommended Path by Budget

### $0/month (Free)
**Best:** Vercel (Frontend) + Railway (Backend)
- Railway free credit covers most hobby usage
- Vercel handles frontend perfectly

### $5-10/month
**Best:** Railway ($5) + Vercel (Free)
- Always-on backend
- Fast frontend
- Simple management

### $10-20/month
**Best:** Render ($7 backend) + Vercel (Free) + Render ($7 frontend)
- Professional setup
- Always-on
- Custom domains included

### $20+/month
**Best:** DigitalOcean Droplet ($6) + Cloudflare (Free CDN)
- Full control
- VPS for backend + frontend
- Can run everything on one server

---

## Setup Checklist

### Before Deploying

- [ ] Generate unique SECRET_KEY
- [ ] Generate API keys for authentication
- [ ] Get Groq API key (free at groq.com)
- [ ] Choose hosting platform
- [ ] Create accounts (Railway, Vercel, etc.)

### Backend Deployment

- [ ] Set environment variables
- [ ] Configure persistent storage for ChromaDB
- [ ] Set REQUIRE_AUTH=true
- [ ] Set ALLOWED_ORIGINS to frontend URL
- [ ] Deploy and test `/health` endpoint

### Frontend Deployment

- [ ] Set NEXT_PUBLIC_API_URL to backend URL
- [ ] Set NEXT_PUBLIC_API_KEY
- [ ] Deploy
- [ ] Test authentication works

### Post-Deployment

- [ ] Test document upload
- [ ] Test search functionality
- [ ] Test chat functionality
- [ ] Check backend logs for errors
- [ ] Set up custom domain (optional)

---

## Troubleshooting

### "API key required" Error

**Problem:** Frontend can't reach backend
**Solution:**
1. Check NEXT_PUBLIC_API_KEY is set in Vercel/frontend
2. Verify API key matches backend API_KEYS
3. Check browser console for 401/403 errors

### "CORS Error"

**Problem:** Backend rejecting frontend requests
**Solution:**
1. Check backend ALLOWED_ORIGINS includes frontend URL
2. Must include https:// prefix
3. No trailing slash
4. Redeploy backend after changing

### Backend "Cold Start" Slow (Render)

**Problem:** First request takes 30+ seconds
**Solution:**
- Upgrade to paid tier ($7/month) for always-on
- OR switch to Railway (doesn't spin down)
- OR use Fly.io (doesn't spin down)

### Out of Railway Credits

**Problem:** App stops after 500 hours
**Solution:**
1. Upgrade to $5/month plan
2. OR switch to Render free tier (with spin-down)
3. OR use Fly.io free tier (3 VMs)

---

## Custom Domain Setup

### With Cloudflare (Free SSL)

**1. Add Domain to Cloudflare**
- cloudflare.com → Add Site
- Follow DNS setup

**2. Configure DNS**

Backend (Railway/Render):
```
Type: CNAME
Name: api
Target: your-backend.railway.app
Proxy: ✅ Proxied (for free SSL)
```

Frontend (Vercel):
```
Type: CNAME
Name: @
Target: cname.vercel-dns.com
Proxy: ❌ DNS Only (Vercel handles SSL)
```

**3. Update Environment Variables**

Backend:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Frontend:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Performance Tips

### 1. Enable Caching

Add to backend (if using Railway/Render):
```python
# Cache search results for 5 minutes
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query, params):
    # search logic
```

### 2. Use CDN

- Vercel: Built-in CDN ✅
- Cloudflare: Free CDN ✅
- Railway: No CDN (add Cloudflare proxy)

### 3. Optimize Cold Starts (Render)

Create `Dockerfile` with health check:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Keep warm
HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Summary

**For Most Users:**
1. **Start with:** Vercel (Frontend) + Railway (Backend)
2. **Cost:** $0/month initially
3. **Upgrade when:** You exceed Railway free credit
4. **Upgrade to:** Railway $5/month

**For Always-On:**
1. **Use:** Render ($7 backend) + Vercel (free frontend)
2. **Cost:** $7/month
3. **Benefit:** No cold starts, professional

**For Full Control:**
1. **Use:** DigitalOcean Droplet ($6/month)
2. **Deploy:** Docker Compose (backend + frontend)
3. **Add:** Cloudflare for free SSL/CDN

---

## Next Steps

1. Review `PRODUCTION_INTERNET_DEPLOYMENT.md` for security setup
2. Follow platform-specific instructions above
3. Test thoroughly before sharing publicly
4. Monitor usage to stay within free tiers
5. Upgrade when needed for better performance

**Need help?** Check troubleshooting section or platform documentation.
