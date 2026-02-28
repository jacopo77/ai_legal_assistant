# Cloud Deployment Plan - AI Paralegal Assistant

## Current Setup (Local Development)

**What's Running Now:**
- ✅ Frontend: Next.js on `localhost:3003`
- ✅ Backend: FastAPI on `localhost:8000`
- ✅ n8n: Elestio (cloud-hosted, already in production)
- ⚠️ Database: Not running (need to add)

---

## Production Architecture (Container-Based)

```
┌─────────────────────────────────────────────────────┐
│                    USERS                            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────┐
│  Frontend (Vercel - Serverless Edge)                 │
│  - Next.js static/SSR                                │
│  - CDN cached globally                               │
│  - Cost: Free tier available                         │
└──────────────────┬───────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────┐
│  Backend API (Railway/Fly.io - Containerized)        │
│  - FastAPI in Docker container                       │
│  - Auto-scaling (1-10 instances)                     │
│  - Streaming support                                 │
│  - Cost: ~$5-20/month                                │
└──────────┬────────────────────┬──────────────────────┘
           │                    │
           ↓                    ↓
┌──────────────────┐  ┌─────────────────────────────┐
│  Database        │  │  n8n (Elestio)              │
│  (Supabase)      │  │  - Already deployed ✅      │
│  - PostgreSQL    │  │  - Workflow automation       │
│  - pgvector      │  │  - Document ingestion        │
│  - Auto backups  │  │  - Cost: Current plan        │
│  - Free tier!    │  └─────────────────────────────┘
└──────────────────┘
```

---

## Step-by-Step Deployment Plan

### **Phase 1: Database Setup (Do First)**

**Service: Supabase** (PostgreSQL with pgvector)

**Why Supabase:**
- ✅ Free tier (500MB database, 50K monthly active users)
- ✅ pgvector support (for embeddings)
- ✅ Automatic backups
- ✅ Built-in auth (if needed later)
- ✅ REST API included

**Steps:**
1. Sign up at https://supabase.com
2. Create new project (select closest region)
3. Enable pgvector extension
4. Get connection string
5. Update backend `.env` with DB_URL

**Estimated time:** 10 minutes
**Cost:** FREE (or $25/month for pro features)

---

### **Phase 2: Backend Deployment**

**Service: Railway** (Recommended) or Fly.io

**Why Railway:**
- ✅ Docker-native (uses your existing Dockerfile)
- ✅ Auto-deploys from GitHub
- ✅ Generous free tier ($5 credit/month)
- ✅ Built-in PostgreSQL (if not using Supabase)
- ✅ Automatic HTTPS
- ✅ Simple environment variables management

**Steps:**
1. Push code to GitHub (if not already)
2. Sign up at https://railway.app
3. Create new project from GitHub repo
4. Select `backend/` directory
5. Railway auto-detects Dockerfile
6. Add environment variables:
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (from Supabase)
   - `ALLOWED_ORIGIN` (your frontend URL)
7. Deploy!

**Result:** Get a URL like: `https://your-app.railway.app`

**Estimated time:** 15 minutes
**Cost:** FREE tier ($5/month credit) or ~$5-10/month after

---

### **Phase 3: Frontend Deployment**

**Service: Vercel** (Best for Next.js)

**Why Vercel:**
- ✅ Made by Next.js creators
- ✅ Automatic optimizations
- ✅ Global CDN
- ✅ Zero config needed
- ✅ Generous free tier
- ✅ Preview deployments for testing

**Steps:**
1. Sign up at https://vercel.com
2. Import from GitHub
3. Select `frontend/` directory
4. Add environment variable:
   - `NEXT_PUBLIC_BACKEND_URL` = your Railway URL
5. Deploy!

**Result:** Get URL like: `https://your-app.vercel.app`

**Estimated time:** 10 minutes
**Cost:** FREE (hobby tier)

---

### **Phase 4: Connect n8n**

**Update n8n Workflow:**

1. In Elestio n8n, edit "My workflow 9"
2. Update HTTP Request nodes to use: `https://your-app.railway.app/api/webhooks/n8n`
3. Activate workflow
4. Test!

**Estimated time:** 5 minutes
**Cost:** Already covered by existing Elestio subscription

---

## Complete Cost Breakdown

| Service | Purpose | Monthly Cost |
|---------|---------|--------------|
| Supabase | Database | **FREE** (or $25 for Pro) |
| Railway | Backend API | **$5-10** (after free credit) |
| Vercel | Frontend | **FREE** |
| Elestio | n8n workflows | **Current plan** |
| **TOTAL** | | **~$5-10/month** (or $30-35 with pro features) |

---

## Security Improvements for Production

### **1. Authentication**
- Add JWT-based auth to backend
- Protect webhook endpoint with API key
- Implement rate limiting per user

### **2. Environment Security**
- Never commit `.env` files
- Use Railway/Vercel secrets management
- Rotate API keys regularly

### **3. Data Protection**
- HTTPS everywhere (automatic with Railway/Vercel)
- Encrypt sensitive data at rest in Supabase
- PII redaction in logs

### **4. API Security**
- Rate limiting: 100 requests/minute per IP
- Input validation on all endpoints
- CORS restricted to your frontend domain only

### **5. Monitoring**
- Set up error tracking (Sentry)
- Log all webhook calls for audit
- Alert on unusual activity

---

## Migration Path

### **Now (Development):**
```
Local: Frontend + Backend
Cloud: n8n only
```

### **Phase 1 (Deploy Backend):**
```
Local: Frontend (for testing)
Cloud: Backend + Database + n8n
```

### **Phase 2 (Deploy Frontend):**
```
Local: Nothing (development only)
Cloud: Frontend + Backend + Database + n8n
```

### **Phase 3 (Optimize):**
```
Cloud: Everything
+ CDN caching
+ Auto-scaling
+ Monitoring
+ Backups
```

---

## Next Actions (In Order)

**1. Prepare for Deployment:**
- [ ] Test app thoroughly locally
- [ ] Fix any remaining UI issues
- [ ] Implement core RAG functionality
- [ ] Add basic error handling

**2. Set Up Database (Week 1):**
- [ ] Create Supabase account
- [ ] Enable pgvector
- [ ] Update backend to use cloud DB
- [ ] Test locally with cloud DB

**3. Deploy Backend (Week 1-2):**
- [ ] Push to GitHub
- [ ] Deploy to Railway
- [ ] Test all endpoints
- [ ] Update n8n workflows with Railway URL

**4. Deploy Frontend (Week 2):**
- [ ] Deploy to Vercel
- [ ] Test full flow
- [ ] Get custom domain (optional)
- [ ] Launch! 🚀

---

## Alternatives to Railway

| Service | Pros | Cons | Cost |
|---------|------|------|------|
| **Railway** | Easy, Docker-native, free tier | Limited free tier | $5-10/mo |
| **Fly.io** | Great performance, generous free tier | More complex setup | $0-5/mo |
| **Render** | Simple, free tier | Slower cold starts on free | $0-7/mo |
| **DigitalOcean App Platform** | Simple, predictable pricing | No free tier | $5-12/mo |
| **AWS ECS/Fargate** | Enterprise-grade, scalable | Complex, expensive | $15+/mo |

**Recommendation: Start with Railway** (easiest) or Fly.io (best free tier)

---

## Can We Stop ngrok Now?

Since you understand ngrok is temporary, should I:
- **A)** Stop ngrok now and plan proper deployment
- **B)** Keep it running just to finish testing your n8n workflow, then stop it

What would you like to do?

---

*Last updated: 2026-02-24*
*Focus: Container-based cloud deployment for scalability and security*
