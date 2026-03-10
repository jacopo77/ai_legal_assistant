# 🚀 Vercel Deployment - Step by Step

## Prerequisites
- ✅ Railway backend deployed and working
- ✅ Railway public URL obtained
- ✅ GitHub account
- ✅ Vercel account (sign up at vercel.com with GitHub)

---

## Step-by-Step Instructions

### 1. Go to Vercel
Open: https://vercel.com

### 2. Sign In
- Click "Sign In" (top right)
- Choose "Continue with GitHub"
- Authorize Vercel to access your GitHub

### 3. Create New Project
- Click "Add New..." dropdown (top right)
- Select "Project"

### 4. Import Repository
- You'll see a list of your GitHub repos
- Find `ai_legal_assistant`
- Click "Import"

### 5. Configure Project

**Framework Preset:**
- Should auto-detect as "Next.js" ✓

**Root Directory:**
- Click "Edit" next to Root Directory
- Enter: `frontend`
- Click "Continue"

**Build Settings:**
- Build Command: `npm run build` (default, leave as is)
- Output Directory: `.next` (default, leave as is)
- Install Command: `npm install` (default, leave as is)

### 6. Add Environment Variable

**CRITICAL STEP:**

Click "Environment Variables" section

Add the following:

```
Name:  NEXT_PUBLIC_BACKEND_URL
Value: https://YOUR_RAILWAY_URL
```

**Replace `YOUR_RAILWAY_URL` with your actual Railway URL!**

Example: `https://fantastic-blessing.up.railway.app`

⚠️ **DO NOT include a trailing slash!**

### 7. Deploy

- Click "Deploy" button
- Wait 2-3 minutes for build to complete
- Watch the logs (optional but satisfying!)

### 8. Get Your Vercel URL

Once deployed:
- You'll see "Congratulations! 🎉"
- Your URL will be displayed (e.g., `https://ai-legal-assistant.vercel.app`)
- Click "Visit" to open your app

---

## Post-Deployment

### Update Railway CORS (Optional but Recommended)

1. Go back to Railway project
2. Click "Variables" tab
3. Find `ALLOWED_ORIGIN`
4. Update value to your Vercel URL:
   ```
   https://your-vercel-app.vercel.app
   ```
5. Or keep as `*` for testing (less secure but works)

### Test Your App

1. Open your Vercel URL
2. Ask a question: "What makes a contract valid?"
3. Select jurisdiction: "US Federal"
4. Click "Ask AI Paralegal"
5. Watch the response stream in! ✨

---

## Troubleshooting

### Build Fails
- Check that root directory is set to `frontend`
- Verify `package.json` exists in `frontend/` folder
- Check build logs for specific error

### App Loads but Can't Connect to Backend
- Verify `NEXT_PUBLIC_BACKEND_URL` is set correctly
- Check no trailing slash in URL
- Test Railway URL directly: `https://your-railway-url/healthz`

### CORS Error
- Update Railway `ALLOWED_ORIGIN` to include Vercel URL
- Or set to `*` temporarily for testing

### Empty Responses
- Check Railway logs for errors
- Verify Supabase connection in Railway
- Test backend: `curl https://your-railway-url/api/health/db`

---

## Success Checklist

- [ ] Vercel deployment successful
- [ ] Frontend loads without errors
- [ ] Can ask a question
- [ ] Response streams in real-time
- [ ] No CORS errors in browser console
- [ ] Citations appear (if documents are ingested)

---

## Next: Run Full Stack Test

Once both are deployed:

```bash
python scripts/test_stack.py https://your-railway-url https://your-vercel-url
```

This will validate:
- ✅ Backend health
- ✅ Database connection
- ✅ Chat functionality
- ✅ CORS configuration

---

**🎉 Once complete, your AI Legal Assistant will be LIVE!**
