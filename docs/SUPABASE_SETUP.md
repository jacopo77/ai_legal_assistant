# Supabase Database Setup Guide

## Step 1: Create/Access Your Supabase Project

1. Go to https://supabase.com and log in
2. Either:
   - **Create a new project** for the paralegal app, OR
   - **Select an existing project** you want to use

3. **Project Settings:**
   - Name: `ai-paralegal-assistant` (or your choice)
   - Database Password: (set a strong password and save it!)
   - Region: Choose closest to your users (e.g., US East, US West, Europe)

---

## Step 2: Enable pgvector Extension

1. In your Supabase project, go to **Database** → **Extensions**
2. Search for **"vector"** or **"pgvector"**
3. Click **Enable** next to "pgvector"
4. Wait for it to activate (should be instant)

---

## Step 3: Get Connection String

1. In your Supabase project, go to **Settings** → **Database**
2. Scroll down to **Connection String** section
3. Select **URI** tab (not Transaction or Session)
4. You'll see something like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Copy this string (replace `[YOUR-PASSWORD]` with your actual password)

---

## Step 4: Update Backend Configuration

**Add to `backend/.env`:**
```
DB_URL=postgresql://postgres:YOUR-PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

**Note:** Keep both DB_PATH (for local dev) and DB_URL (for cloud)

---

## Step 5: Test Connection

Run this command to test the connection:
```bash
cd backend
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DB_URL'); print('✅ Connected!'); engine.dispose()"
```

---

## What We'll Store in Supabase

**Tables:**
- `documents` - Ingested legal documents from n8n
- `chunks` - Document chunks with embeddings (vector column)
- `queries` - User question history
- `citations` - Tracked citations and sources

**pgvector Usage:**
- Store OpenAI embeddings (1536 dimensions)
- Fast similarity search for RAG
- Find relevant legal documents for user questions

---

## Security Notes

✅ **Connection is encrypted** (SSL by default)
✅ **Row Level Security** available (enable later for multi-user)
✅ **Automatic backups** (daily on free tier)
✅ **IP restrictions** (can whitelist Railway/Fly.io IPs)

---

## Next Steps After Database Setup

1. Update backend code to use Supabase (not SQLite)
2. Deploy backend to Railway with Supabase connection
3. Test webhook from n8n → Railway backend → Supabase storage
4. Deploy frontend to Vercel

---

*Follow these steps and let me know when you have the connection string!*
