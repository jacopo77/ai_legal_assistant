# 🚀 Complete Deployment & Testing Guide

This guide walks you through deploying the full stack and testing end-to-end.

## 📋 Pre-Deployment Checklist

### Backend ✅
- [x] RAG system implemented
- [x] Supabase integration working
- [x] OpenAI integration configured
- [x] Streaming endpoint `/api/chat/stream` working
- [x] Health check endpoint `/healthz` working
- [x] Dockerfile configured
- [x] Railway.toml configured

### Frontend ✅
- [x] Next.js 14 app created
- [x] Chat UI built with streaming support
- [x] Citation rendering implemented
- [x] Error handling added
- [x] Environment variables configured
- [x] Dependencies installed

### Database ✅
- [x] Supabase project created
- [x] pgvector extension enabled
- [x] Tables created (documents, chunks)
- [x] Vector search function deployed
- [x] Test data ingested

---

## 🎯 Deployment Steps

### Step 1: Deploy Backend to Railway ⏳ IN PROGRESS

**Current Status:** Waiting for Railway platform incident to resolve

**Configuration Done:**
- ✅ Root directory set to `backend`
- ✅ Environment variables added:
  - `OPENAI_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `ALLOWED_ORIGIN`

**Next Actions:**
1. Wait for Railway deployment slowness to resolve
2. Click "Deploy" button when ready
3. Wait for build to complete (~2-3 minutes)
4. Get public URL from Settings → Networking

**Expected URL Format:**
```
https://fantastic-blessing.up.railway.app
```

**Testing Railway Deployment:**
```bash
# Test health endpoint
curl https://YOUR_RAILWAY_URL/healthz

# Expected response:
{"status":"ok"}

# Test database connection
curl https://YOUR_RAILWAY_URL/api/health/db

# Expected response:
{"status":"ok","database":"connected"}
```

---

### Step 2: Deploy Frontend to Vercel

**When to do this:** After Railway backend is deployed and tested

**Instructions:**

1. **Go to [vercel.com](https://vercel.com)**
   - Sign in with GitHub

2. **Create New Project**
   - Click "Add New..." → "Project"
   - Select `jacopo77/ai_legal_assistant` repository
   - Click "Import"

3. **Configure Project**
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** Click "Edit" → Enter `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

4. **Add Environment Variable**
   - Click "Environment Variables"
   - Add:
     ```
     Name: NEXT_PUBLIC_BACKEND_URL
     Value: https://YOUR_RAILWAY_URL
     ```
   - Replace `YOUR_RAILWAY_URL` with actual Railway URL

5. **Deploy**
   - Click "Deploy"
   - Wait ~2 minutes for build
   - Get Vercel URL (like `https://ai-legal-assistant.vercel.app`)

**Testing Vercel Deployment:**
1. Open Vercel URL in browser
2. Should see chat interface
3. Try asking a question
4. Check browser console for errors

---

### Step 3: Update CORS Settings

**Why:** Railway backend needs to allow requests from Vercel frontend

**Instructions:**

1. **Go to Railway Project** → `fantastic-blessing`

2. **Update Environment Variable:**
   - Find `ALLOWED_ORIGIN`
   - Change from `*` to your Vercel URL:
     ```
     ALLOWED_ORIGIN=https://your-app.vercel.app
     ```
   - Or keep as `*` for testing (less secure)

3. **Redeploy Backend:**
   - Railway auto-redeploys when variables change
   - Wait ~1 minute

---

### Step 4: Test End-to-End

**Full Stack Test:**

1. **Open Vercel URL** in browser

2. **Ask a Legal Question:**
   ```
   Question: What makes a contract valid?
   Jurisdiction: US Federal
   ```

3. **Expected Response:**
   ```
   A contract is valid if it contains:
   1. Offer - a proposal to enter into an agreement
   2. Acceptance - agreement to the terms
   3. Consideration - something of value exchanged
   
   [1] Contract Law Basics
   ```

4. **Check for Issues:**
   - ✅ Response streams in real-time (not all at once)
   - ✅ Citations appear as blue superscript numbers
   - ✅ No CORS errors in browser console
   - ✅ Multiple questions work in sequence

**If Errors Occur:**

| Error | Cause | Solution |
|-------|-------|----------|
| "Failed to connect to backend" | Backend down or wrong URL | Check Railway deployment, verify `NEXT_PUBLIC_BACKEND_URL` |
| "CORS policy" error | Backend doesn't allow frontend origin | Update `ALLOWED_ORIGIN` in Railway |
| "500 Internal Server Error" | Backend code issue | Check Railway logs |
| Empty response | Supabase connection issue | Test `/api/health/db` endpoint |
| No citations | No documents in database | Run document ingestion (Step 5) |

---

## 📊 Monitoring & Logs

### Railway Logs
1. Go to Railway project
2. Click "Deployments" tab
3. Click latest deployment
4. View logs in real-time

**Common Log Messages:**
```
✅ "Application startup complete" - Backend healthy
✅ "POST /api/chat/stream 200" - Chat request successful
❌ "Database connection failed" - Supabase issue
❌ "OpenAI API error" - API key or quota issue
```

### Vercel Logs
1. Go to Vercel project
2. Click "Deployments" tab
3. Click latest deployment
4. View function logs

---

## 🔧 Local Testing (Before Deployment)

### Backend Local Test

```bash
# Navigate to backend
cd backend

# Run backend
uvicorn app.main:app --reload --port 8000

# In another terminal, test endpoints:
curl http://localhost:8000/healthz
curl http://localhost:8000/api/health/db

# Test chat (streaming):
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"What is a contract?","country":"US"}'
```

### Frontend Local Test

```bash
# Navigate to frontend
cd frontend

# Ensure .env.local has:
# NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000

# Run frontend
npm run dev

# Open browser: http://localhost:3000
```

---

## 🎯 Quick Reference URLs

### Development (Local)
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:3000`
- Health Check: `http://127.0.0.1:8000/healthz`

### Production (Update after deployment)
- Backend: `https://fantastic-blessing.up.railway.app` ⏳
- Frontend: `https://your-app.vercel.app` ⏳
- Health Check: `https://fantastic-blessing.up.railway.app/healthz` ⏳

### Services
- Supabase: https://rxycqygjwuhzfwevmqdj.supabase.co
- Railway: https://railway.app/project/[your-project-id]
- Vercel: https://vercel.com/[your-username]/[project-name]
- GitHub: https://github.com/jacopo77/ai_legal_assistant

---

## 🐛 Troubleshooting

### Railway Deployment Fails

**Build Error: "No such file or directory"**
- Check root directory is set to `backend`
- Verify `requirements.txt` exists in `backend/`

**Runtime Error: "Module not found"**
- Check all dependencies in `requirements.txt`
- Verify Python version (should be 3.11)

**Health check fails**
- Check `PORT` environment variable (Railway sets automatically)
- Verify `uvicorn` command in `Dockerfile`

### Vercel Deployment Fails

**Build Error: "Cannot find module"**
- Run `npm install` locally to ensure `package.json` is correct
- Check `frontend/` folder structure

**Runtime Error: 404 on all pages**
- Verify root directory set to `frontend`
- Check `next.config.js` exists

### Connection Issues

**Backend can't reach Supabase**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Test locally first: `curl https://rxycqygjwuhzfwevmqdj.supabase.co`

**Frontend can't reach Backend**
- Check `NEXT_PUBLIC_BACKEND_URL` matches Railway URL
- Verify CORS settings in backend
- Check browser console for detailed error

---

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ Railway health check returns `{"status":"ok"}`
2. ✅ Vercel URL loads chat interface
3. ✅ Can ask a question and get a streamed response
4. ✅ Citations appear in the response
5. ✅ No errors in browser console
6. ✅ Backend logs show successful requests

---

## 📞 Support

If stuck:
1. Check logs in Railway and Vercel dashboards
2. Test endpoints individually using curl
3. Verify all environment variables are set correctly
4. Check GitHub repo for latest code

---

## 🎉 After Successful Deployment

Next steps:
1. ✅ Set up n8n + Firecrawl (Step 5 - automated document ingestion)
2. ✅ Add more legal documents to database
3. ✅ Test with real-world legal questions
4. ✅ Share URL with beta testers
5. ✅ Monitor usage and errors
6. ✅ Iterate based on feedback

**You're now live! 🚀**
