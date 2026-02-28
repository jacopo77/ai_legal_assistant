# Complete Supabase Setup for AI Legal Assistant

✅ **Your Project:** `Sustainable Life Project` (ai-legal-assistant)

---

## STEP 1: Enable pgvector Extension

1. In Supabase, go to **Database** → **Extensions** (left sidebar)
2. In the search box at the top, type: **`vector`**
3. Find **"pgvector"** in the results
4. Click the **toggle/enable button** next to it
5. Wait a few seconds for it to activate

**Why?** This allows storing vector embeddings for semantic search.

---

## STEP 2: Get Your Connection String

### Option A: Project Settings → Database
1. Click **"Project Settings"** (gear icon) in the left sidebar
2. Click **"Database"**
3. Look for **"Connection string"** section
4. Click the **"URI"** tab
5. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
6. **Replace `[YOUR-PASSWORD]`** with your actual database password

### Option B: SQL Editor Method
1. Go to **SQL Editor** in left sidebar
2. Run this query:
   ```sql
   SELECT current_database();
   ```
3. Then manually construct:
   ```
   postgresql://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
   - Find your project URL in **Settings** → **General** → **Reference ID**

---

## STEP 3: Update Backend .env File

Add this line to `backend/.env`:

```env
# Supabase Database (for production)
DB_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

**Your current `.env` will look like:**
```env
# Backend configuration
ENVIRONMENT=development
HOST=127.0.0.1
PORT=8000
ALLOWED_ORIGIN=http://localhost:3000

# OpenAI (required for embeddings and chat)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-small

# SQLite DB path (for local testing)
DB_PATH=app/data/app.db

# Supabase Database (for cloud/production)
DB_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

---

## STEP 4: Create Database Schema

Once `DB_URL` is set, we need to create the tables. Run this in Supabase:

1. Go to **SQL Editor** in Supabase
2. Click **"New Query"**
3. Paste this SQL:

```sql
-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT,
    url TEXT,
    country TEXT,
    title TEXT,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small produces 1536 dimensions
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast vector similarity search
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for country filtering
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);
CREATE INDEX IF NOT EXISTS documents_country_idx ON documents(country);
```

4. Click **"Run"** or press `Ctrl+Enter`
5. You should see: ✅ **"Success. No rows returned"**

---

## STEP 5: Test Connection from Backend

From your project folder:

```powershell
cd "C:\Users\David Bartlett\ai_legal_assistant\backend"

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DB_URL_HERE'); print('✅ Connected!'); engine.dispose()"
```

**Expected output:** `✅ Connected!`

---

## STEP 6: Test Document Ingestion

Start your backend:

```powershell
cd "C:\Users\David Bartlett\ai_legal_assistant\backend"
python -m uvicorn app.main:app --reload --port 8000
```

Test the webhook (in another terminal):

```powershell
curl -X POST http://localhost:8000/api/webhooks/n8n `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Test legal document about contracts",
    "title": "Contract Law Test",
    "url": "https://example.com/test",
    "country": "US",
    "source": "test",
    "metadata": {}
  }'
```

**Expected response:**
```json
{"status":"ok","document_id":1}
```

---

## STEP 7: Verify Data in Supabase

1. Go to **Database** → **Tables** in Supabase
2. You should see:
   - **documents** table (1 row)
   - **chunks** table (N rows with embeddings)
3. Click on **chunks** table
4. You should see the `embedding` column with vector data

---

## How It Works Now:

```
n8n (Elestio) 
    ↓ webhook
Backend (local/Railway)
    ↓ stores
Supabase (documents + embeddings)
    ↓ retrieves
User asks question
    ↓ searches
Supabase finds similar chunks
    ↓ returns
Backend sends to OpenAI
    ↓ streams
User gets answer
```

---

## Next Steps After Setup:

- [ ] Enable pgvector extension
- [ ] Get connection string
- [ ] Update `backend/.env` with `DB_URL`
- [ ] Run SQL schema in Supabase
- [ ] Test backend connection
- [ ] Test document ingestion
- [ ] Verify data in Supabase
- [ ] Deploy backend to Railway (later)
- [ ] Update n8n webhook URL to Railway (later)

---

## Troubleshooting:

**"relation 'documents' does not exist"**
→ Run the SQL schema (Step 4)

**"extension 'vector' does not exist"**
→ Enable pgvector extension (Step 1)

**"password authentication failed"**
→ Check your database password in the connection string

**"no pg_hba.conf entry"**
→ Your IP might be blocked. Go to Settings → Database → Network Restrictions → "Allow all"

---

**Start with Step 1 and work through each step. Let me know when you complete each one!**
