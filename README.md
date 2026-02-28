Paralegal Assistant (Python FastAPI + Next.js)
=============================================

Overview
--------
AI Paralegal Assistant: A FastAPI backend and Next.js/Tailwind frontend that delivers streaming, citation-backed answers to legal questions, filtered by jurisdiction. Documents are ingested via n8n webhooks, chunked, and embedded (OpenAI) for retrieval; SQLite powers local dev while Postgres + pgvector is ready for production. The UI implements a dark, glassy Stitch design with a clean form (question + jurisdiction) and analysis preview. Answers reference sources inline ([1], [2]) and the system is structured for auditability, future auth/compliance, and per-country pipelines. Docs include the Stitch prompt, API contract, and a living UI improvements log.

This repo contains:

- `backend/` FastAPI service: chat streaming, n8n ingest webhook, simple RAG (SQLite + OpenAI embeddings)
- `frontend/` Next.js app: minimal chat UI that streams responses from the backend

Prerequisites
-------------
- Python 3.10+
- Node 18+
- An OpenAI API key

Backend Setup
-------------
1) Create `backend/.env` from example and set your key:
```
cd backend
cp .env.example .env
```

2) Install and run:
```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3) Health check: `GET http://127.0.0.1:8000/healthz`

Frontend Setup
--------------
1) Create `frontend/.env.local` with your backend URL:
```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

2) Install and run:
```
cd ../frontend
npm install
npm run dev
```
Open http://localhost:3000

n8n Integration
---------------
Point n8n to POST `http://127.0.0.1:8000/api/webhooks/n8n` with a JSON body like:
```json
{
  "source": "gov_site",
  "url": "https://example.gov/law.pdf",
  "country": "Canada",
  "title": "Act 123",
  "text": "Extracted text content here",
  "metadata": { "year": 2021 }
}
```
Each call is stored and chunked with embeddings for retrieval.

Notes
-----
- This is a minimal, local-first setup for quick iteration.
- For production, migrate to Postgres + pgvector and add auth/audit logging.

Scaffold status
---------------
This commit scaffolds the project with:

- backend/ (FastAPI app, streaming endpoint, n8n ingest webhook, Dockerfile)
- frontend/ (Next.js + Tailwind minimal UI, streaming client, Dockerfile)
- docker-compose.yml to run backend, frontend, and Postgres for pgvector
- docs/ with Stitch prompt, API contract, and UI improvements log

Next steps
----------
1. Wire embeddings to OpenAI and implement vector store (SQLite dev / Postgres + pgvector production).
2. Implement streaming RAG with citation generation and audit logs.
3. Add authentication, rate limits, and compliance tooling.
