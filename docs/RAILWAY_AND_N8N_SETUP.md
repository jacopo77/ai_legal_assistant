# Railway Deployment + n8n Firecrawl Setup

---

## PART 1 — Deploy Backend to Railway

### Step 1: Push code to GitHub

Make sure your latest code is pushed:
```powershell
cd "C:\Users\David Bartlett\ai_legal_assistant"
git add .
git commit -m "Add Railway config and Supabase REST support"
git push
```

### Step 2: Create Railway project

1. Go to **[railway.app](https://railway.app)** → Sign up / Log in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `ai_legal_assistant` repository
5. Railway will detect the `backend/` folder — set **Root Directory** to `backend`
6. Click **Deploy**

### Step 3: Add environment variables in Railway

In your Railway project → **Variables** tab, add these:

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | your OpenAI key |
| `SUPABASE_URL` | `https://rxycqygjwuhzfwevmqdj.supabase.co` |
| `SUPABASE_KEY` | your `sb_secret_...` key |
| `ALLOWED_ORIGIN` | `*` (for now; restrict to your Vercel URL later) |
| `ENVIRONMENT` | `production` |

> Railway sets `PORT` automatically — do NOT add it manually.

### Step 4: Get your Railway URL

After deploy succeeds, Railway gives you a URL like:
```
https://ai-legal-assistant-production.up.railway.app
```

Test it:
```
https://YOUR_RAILWAY_URL.up.railway.app/healthz         → {"status":"ok"}
https://YOUR_RAILWAY_URL.up.railway.app/api/health/db   → active_backend: supabase_rest
```

---

## PART 2 — Set Up n8n Firecrawl Workflow

### Step 1: Import the workflow

1. Open your **Elestio n8n** dashboard
2. Go to **Workflows** → click **"+"** → **"Import from file"**
3. Upload `docs/n8n_firecrawl_workflow.json`

### Step 2: Configure the Config node

Open the imported workflow and edit the **"Config"** node:

| Field | Value |
|-------|-------|
| `firecrawl_api_key` | Your Firecrawl API key (from firecrawl.dev → Dashboard) |
| `backend_url` | Your Railway URL (e.g. `https://your-app.up.railway.app`) |
| `country` | The jurisdiction for these docs (e.g. `AU`, `US`, `UK`) |
| `urls` | Array of legal URLs to scrape (see examples below) |

### Step 3: Add URLs to scrape

Edit the `urls` array in the Config node. Examples:

```json
[
  "https://www.legislation.gov.au/current",
  "https://www.austlii.edu.au/au/legis/cth/consol_act/",
  "https://www.comlaw.gov.au/"
]
```

For US legal sources:
```json
[
  "https://www.law.cornell.edu/uscode/text",
  "https://www.govinfo.gov/",
  "https://uscode.house.gov/"
]
```

### Step 4: Test the workflow

1. Click **"Test workflow"** (or the Manual Trigger node → Execute)
2. Watch each node execute
3. Check the **"Log Result"** node output — you should see:
   ```
   ✅ Ingested: [Page Title] → document_id 2
   ```
4. Verify in **Supabase → Table Editor → documents** that new rows appeared

### Step 5: Schedule it (optional)

To run automatically:
1. Replace the **Manual Trigger** with a **Schedule Trigger** node
2. Set it to run weekly (or as needed)
3. Activate the workflow toggle

---

## PART 3 — How the Pipeline Works

```
Firecrawl scrapes URL
      ↓ returns clean markdown + metadata
n8n formats payload
      ↓ { text, title, url, country, source:"firecrawl" }
Backend /api/webhooks/n8n
      ↓ generates OpenAI embeddings
Supabase documents + chunks tables
      ↓ stored with vector embeddings
User asks question
      ↓ vector similarity search
LLM generates cited answer
```

---

## Troubleshooting

**Firecrawl node fails**
→ Check your API key in the Config node
→ Firecrawl free tier: 500 pages/month

**Backend returns 422**
→ The `text` field is empty — the page may be JS-rendered. Try a different URL or add `"waitFor": 2000` to the Firecrawl request body.

**document_id not incrementing**
→ Check Railway logs for embedding errors (OpenAI API key)

**Vector search returns nothing**
→ Data is ingested but no queries have been run yet — this is normal until you ask a question via the frontend
