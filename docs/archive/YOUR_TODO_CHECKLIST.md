# YOUR TO-DO CHECKLIST FOR DEPLOYMENT

**Project:** API-Assistant
**Status:** ✅ Critical fixes completed, ready for deployment
**Your Action Required:** Follow this checklist step-by-step

---

## ✅ COMPLETED (Already Done by AI)

- [x] Fixed CORS security vulnerability
- [x] Removed hardcoded SECRET_KEY from repository
- [x] Implemented API key authentication
- [x] Fixed BM25 performance bottleneck
- [x] Fixed frontend type mismatches
- [x] Added API key support to frontend
- [x] Created deployment guides

---

## 🔴 CRITICAL: Do This FIRST (Before Any Deployment)

### Step 1: Generate Your Secrets

**A. Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
**Copy the output** (it will look like: `a1b2c3d4e5f6...`)
**Save it** - you'll need it in Step 3

**B. Generate API Keys:**
```bash
# Generate your first API key
python -c "import secrets; print(f'api-key-{secrets.token_urlsafe(32)}')"
```
**Copy the output** (it will look like: `api-key-AbC123XyZ...`)
**Save it** - you'll need it in Step 3 and Step 4

Generate 2-3 keys:
- One for your frontend
- One for testing
- One for mobile/future use

---

## 📝 Step 2: Choose Your Hosting Platform

Pick ONE option below based on your budget:

### Option A: FREE (Recommended for Start)
**Platform:** Vercel (Frontend) + Railway (Backend)
**Cost:** $0/month (Railway gives $5 free credit = ~500 hours)
**Best for:** Testing, learning, hobby projects
**Guide:** See `AFFORDABLE_HOSTING_GUIDE.md` → Option 1

### Option B: LOW COST ($7/month)
**Platform:** Render (Backend + Frontend)
**Cost:** $7/month for always-on backend
**Best for:** Small production apps
**Guide:** See `AFFORDABLE_HOSTING_GUIDE.md` → Option 2

### Option C: FULL CONTROL ($6-12/month)
**Platform:** DigitalOcean Droplet
**Cost:** $6-12/month
**Best for:** Full control, learning DevOps
**Guide:** See `PRODUCTION_INTERNET_DEPLOYMENT.md` → Docker Deployment

**My Choice:** _________________ (write it down)

---

## 🚀 Step 3: Configure Environment Variables

### A. Update Backend .env File

**Location:** `/home/user/Api-Assistant/.env`

```bash
# Open the file and update these lines:

# 1. PASTE YOUR SECRET_KEY FROM STEP 1A
SECRET_KEY=PASTE_YOUR_GENERATED_SECRET_HERE

# 2. SET YOUR CORS ORIGINS
# For Vercel: https://your-app-name.vercel.app
# For Render: https://your-app-name.onrender.com
# For custom domain: https://yourdomain.com
ALLOWED_ORIGINS=PASTE_YOUR_FRONTEND_URL_HERE

# 3. ENABLE AUTHENTICATION (CRITICAL!)
REQUIRE_AUTH=true

# 4. PASTE YOUR API KEYS FROM STEP 1B (comma-separated if multiple)
API_KEYS=PASTE_YOUR_API_KEYS_HERE

# 5. ADD YOUR GROQ API KEY (get free at console.groq.com)
GROQ_API_KEY=PASTE_YOUR_GROQ_KEY_HERE
```

**Save the file!**

### B. Create Frontend .env.local File

**Location:** `/home/user/Api-Assistant/frontend/.env.local`

Create this file with:
```bash
# 1. YOUR BACKEND URL
# Railway: https://your-app.up.railway.app
# Render: https://your-backend.onrender.com
# Custom: https://api.yourdomain.com
NEXT_PUBLIC_API_URL=PASTE_YOUR_BACKEND_URL_HERE

# 2. YOUR API KEY (from Step 1B)
NEXT_PUBLIC_API_KEY=PASTE_ONE_OF_YOUR_API_KEYS_HERE
```

**Save the file!**

---

## 🧪 Step 4: Test Locally (IMPORTANT!)

Before deploying to the internet, test everything works locally:

### A. Start Backend

```bash
cd /home/user/Api-Assistant

# Activate virtual environment (if using one)
# source venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt

# Start server
uvicorn src.api.app:app --reload
```

**Expected:** Server starts on `http://localhost:8000`
**Test:** Open http://localhost:8000/health in browser
**Should see:** `{"status": "healthy", ...}`

### B. Start Frontend

**Open a NEW terminal:**

```bash
cd /home/user/Api-Assistant/frontend

# Install dependencies if needed
npm install

# Start dev server
npm run dev
```

**Expected:** Server starts on `http://localhost:3000`
**Test:** Open http://localhost:3000 in browser
**Should see:** API Assistant interface

### C. Test Authentication

In your browser:
1. Go to http://localhost:3000
2. Try uploading a test document
3. Try searching
4. Check browser console (F12) for errors

**Expected:**
- ✅ No "401 Unauthorized" errors
- ✅ No "CORS" errors
- ✅ Documents upload successfully
- ✅ Search works

**If you see errors:**
- Check Step 3 (environment variables)
- Make sure .env has correct API_KEYS
- Make sure frontend/.env.local has same API key

---

## 🌐 Step 5: Deploy to Internet

Follow the guide for your chosen platform from Step 2:

### For Railway + Vercel (FREE):

**5A. Deploy Backend to Railway:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd /home/user/Api-Assistant
railway init
# Name it: api-assistant-backend

# Deploy
railway up

# Get your URL
railway domain
# Copy this URL! You'll need it below.
```

**5B. Set Railway Environment Variables:**

Go to https://railway.app → Your Project → Variables

Add ALL variables from your .env file:
- SECRET_KEY=your-generated-secret
- API_KEYS=your-generated-keys
- REQUIRE_AUTH=true
- ALLOWED_ORIGINS=https://your-vercel-app.vercel.app (update after deploying frontend)
- GROQ_API_KEY=your-groq-key
- All other variables from .env

**5C. Add Railway Volume:**
- Settings → Volumes → New Volume
- Mount path: `/app/data`
- Size: 1GB

**5D. Deploy Frontend to Vercel:**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Follow prompts, then:
vercel --prod
```

**5E. Update CORS:**

Go back to Railway → Variables → Update:
```
ALLOWED_ORIGINS=https://your-actual-vercel-url.vercel.app
```

Redeploy Railway.

### For Render:

See `AFFORDABLE_HOSTING_GUIDE.md` → Option 2 (step-by-step instructions)

### For DigitalOcean:

See `PRODUCTION_INTERNET_DEPLOYMENT.md` → Docker Deployment section

---

## ✅ Step 6: Verify Deployment

### A. Test Backend
```bash
# Replace with your actual backend URL
curl https://your-backend-url.railway.app/health
```
**Expected:** `{"status": "healthy", ...}`

### B. Test Authentication
```bash
# Should FAIL (no API key)
curl -X POST https://your-backend-url/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected: 401 Unauthorized ✅ (this is good!)

# Should SUCCEED (with API key)
curl -X POST https://your-backend-url/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "test"}'

# Expected: 200 OK with results ✅
```

### C. Test Frontend

1. Open your frontend URL in browser
2. Upload a document
3. Search for something
4. Use chat feature
5. Check browser console (F12) for errors

**Expected:**
- ✅ No errors
- ✅ Everything works
- ✅ API key authentication working

---

## 🎉 Step 7: You're Live!

### Share Your App
- Frontend URL: https://your-app.vercel.app
- Backend API: https://your-backend.railway.app

### Monitor Usage

**Railway:**
- Dashboard shows hours used
- Free tier = $5 credit = ~500 hours/month
- Monitor at: https://railway.app

**Vercel:**
- Free tier = unlimited
- Dashboard: https://vercel.com/dashboard

### Next Steps

- [ ] Add custom domain (optional)
- [ ] Set up monitoring/alerts (optional)
- [ ] Import your API documentation
- [ ] Share with users!

---

## 🆘 Troubleshooting Quick Fixes

### "API key required" Error

**Problem:** Frontend not sending API key

**Fix:**
1. Check `frontend/.env.local` has `NEXT_PUBLIC_API_KEY=your-key`
2. Restart frontend dev server: `npm run dev`
3. Or redeploy to Vercel

### "CORS Error"

**Problem:** Backend rejecting frontend

**Fix:**
1. Check backend `ALLOWED_ORIGINS` includes full frontend URL
2. Must have `https://` prefix
3. No trailing slash
4. Redeploy backend

### Railway App Not Starting

**Problem:** Environment variables not set

**Fix:**
1. Go to Railway dashboard
2. Variables tab
3. Add ALL variables from .env
4. Redeploy

### Search Not Working

**Problem:** ChromaDB not persisting

**Fix:**
1. Check Railway has Volume mounted at `/app/data`
2. Check `CHROMA_PERSIST_DIR=/app/data/chroma_db`
3. Redeploy

---

## 📚 Reference Documents

- **AFFORDABLE_HOSTING_GUIDE.md** - Detailed hosting instructions
- **PRODUCTION_INTERNET_DEPLOYMENT.md** - Production security guide
- **PROJECT_AUDIT_REPORT.md** - Full project analysis
- **CRITICAL_FIXES_GUIDE.md** - Technical fix details

---

## ✅ Final Checklist

Before going public:

- [ ] Generated unique SECRET_KEY
- [ ] Generated API keys
- [ ] Updated backend .env with secrets
- [ ] Updated frontend .env.local with API key
- [ ] Tested locally (Step 4)
- [ ] Deployed backend (Step 5)
- [ ] Deployed frontend (Step 5)
- [ ] Updated CORS settings (Step 5E)
- [ ] Verified deployment works (Step 6)
- [ ] Tested with real documents
- [ ] No errors in browser console
- [ ] Ready to share! 🎉

---

**Questions?** Check troubleshooting section above or reference guides!

**Good luck! 🚀**
