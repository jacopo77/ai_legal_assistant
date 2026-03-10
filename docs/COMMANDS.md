# 🎮 Quick Command Reference

Quick reference for common development and deployment tasks.

---

## 🏃 Running Locally

### Backend

```bash
# Navigate to backend
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run with logs
uvicorn app.main:app --reload --port 8000 --log-level debug
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

---

## 🧪 Testing

### Test Backend Locally

```bash
# Health check
curl http://localhost:8000/healthz

# Database check
curl http://localhost:8000/api/health/db

# Test chat (replace with your question)
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"What is a contract?","country":"US"}'
```

### Test Production Backend

```bash
# Health check
curl https://your-railway-url.railway.app/healthz

# Database check
curl https://your-railway-url.railway.app/api/health/db
```

### Run Automated Test Suite

```bash
# Test local backend
python scripts/test_stack.py http://127.0.0.1:8000

# Test production backend
python scripts/test_stack.py https://your-railway-url.railway.app

# Test production backend + frontend (checks CORS)
python scripts/test_stack.py https://your-railway-url.railway.app https://your-vercel-url.vercel.app
```

---

## 🚀 Deployment

### Deploy Backend to Railway

```bash
# 1. Commit changes
git add .
git commit -m "Update backend"
git push origin main

# 2. Railway auto-deploys from GitHub
# 3. Monitor deployment in Railway dashboard
```

**Manual deployment in Railway:**
1. Go to Railway project
2. Click "Deployments" tab
3. Click "Deploy Now"

### Deploy Frontend to Vercel

```bash
# 1. Commit changes
git add .
git commit -m "Update frontend"
git push origin main

# 2. Vercel auto-deploys from GitHub
# 3. Monitor deployment in Vercel dashboard
```

**Manual deployment via Vercel CLI:**

```bash
# Install Vercel CLI (first time only)
npm install -g vercel

# Navigate to frontend
cd frontend

# Deploy
vercel

# Deploy to production
vercel --prod
```

---

## 🗄️ Database Operations

### Connect to Supabase

```bash
# Using psql (if direct connection works)
psql "postgresql://postgres:m6Yac0TeusUHE8jv@db.rxycqygjwuhzfwevmqdj.supabase.co:5432/postgres"
```

### Query Documents

```sql
-- List all documents
SELECT id, title, url, country, created_at 
FROM documents 
ORDER BY created_at DESC 
LIMIT 10;

-- Count chunks
SELECT COUNT(*) FROM chunks;

-- Search for specific document
SELECT * FROM documents WHERE title ILIKE '%contract%';
```

### Test Vector Search

```sql
-- Test match_chunks function
SELECT * FROM match_chunks(
  query_embedding := array_fill(0.0, ARRAY[1536])::vector,
  match_threshold := 0.0,
  match_count := 5,
  filter_country := 'US'
);
```

---

## 🔑 Environment Variables

### Backend (.env)

```bash
# Required
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJhbGc...

# Optional
ALLOWED_ORIGIN=*
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-small
```

### Frontend (.env.local)

```bash
# Development
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000

# Production
NEXT_PUBLIC_BACKEND_URL=https://your-railway-url.railway.app
```

---

## 🐛 Debugging

### View Railway Logs

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Follow logs in real-time
railway logs --follow
```

### View Vercel Logs

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# View logs
vercel logs

# View production logs
vercel logs --prod
```

### Check Frontend Console Errors

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors in red
4. Check Network tab for failed requests

### Check Backend Logs Locally

```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug

# Watch for specific errors
uvicorn app.main:app --reload | grep ERROR
```

---

## 📦 Package Management

### Backend (Python)

```bash
# Install new package
pip install package-name

# Add to requirements.txt
pip freeze > requirements.txt

# Or manually add to requirements.txt:
echo "package-name>=1.0.0" >> requirements.txt
```

### Frontend (npm)

```bash
# Install new package
npm install package-name

# Install dev dependency
npm install --save-dev package-name

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

---

## 🔄 Git Workflow

### Commit Changes

```bash
# Check status
git status

# Add all changes
git add .

# Commit with message
git commit -m "Your message here"

# Push to GitHub
git push origin main
```

### Create Branch

```bash
# Create and switch to new branch
git checkout -b feature/new-feature

# Push branch to GitHub
git push -u origin feature/new-feature
```

### Undo Changes

```bash
# Discard changes in file
git checkout -- filename

# Discard all changes
git reset --hard HEAD

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

---

## 🏥 Health Checks

### Quick Health Check Script

```bash
#!/bin/bash
# Save as check_health.sh

BACKEND_URL=${1:-http://localhost:8000}

echo "Checking $BACKEND_URL..."
curl -s "$BACKEND_URL/healthz" | python -m json.tool
```

**Usage:**
```bash
chmod +x check_health.sh
./check_health.sh
./check_health.sh https://your-app.railway.app
```

---

## 🔧 Maintenance

### Update Dependencies

```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

### Clear Caches

```bash
# Frontend - clear Next.js cache
cd frontend
rm -rf .next
npm run build

# Backend - clear Python cache
cd backend
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Reset Local Database (if using SQLite for dev)

```bash
cd backend
rm -f app/data/app.db
python scripts/init_db.py  # if you have this script
```

---

## 📊 Monitoring

### Check Railway Resource Usage

```bash
# Using Railway CLI
railway status

# View metrics in dashboard
open https://railway.app/project/your-project-id
```

### Check Vercel Analytics

```bash
# View in dashboard
open https://vercel.com/your-username/your-project/analytics
```

---

## 🎯 Quick Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for port conflicts
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### Frontend won't start

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+

# Try different port
PORT=3001 npm run dev
```

### Can't connect to backend from frontend

```bash
# Check backend is running
curl http://localhost:8000/healthz

# Check CORS settings
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/chat/stream -v

# Check .env.local
cat frontend/.env.local
```

---

## 🎓 Learning Resources

### FastAPI Docs
- https://fastapi.tiangolo.com/

### Next.js Docs
- https://nextjs.org/docs

### Railway Docs
- https://docs.railway.app/

### Vercel Docs
- https://vercel.com/docs

### Supabase Docs
- https://supabase.com/docs

---

## 🆘 Emergency Commands

### Kill Process on Port

```bash
# Mac/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Force Redeploy

```bash
# Railway
railway up --detach

# Vercel
vercel --force --prod
```

### Rollback Deployment

**Railway:**
1. Go to Deployments tab
2. Find previous working deployment
3. Click "Redeploy"

**Vercel:**
1. Go to Deployments tab
2. Find previous working deployment
3. Click "..." → "Promote to Production"

---

**Need help?** Check the logs first, then consult the troubleshooting guide in `docs/DEPLOYMENT_GUIDE.md`
