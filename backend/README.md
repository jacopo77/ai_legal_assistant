Paralegal Assistant - Backend (FastAPI)
======================================

Quickstart
----------

1) Create and fill `.env`:

```
cp .env.example .env
```

Set `OPENAI_API_KEY`.

2) Install deps and run:

```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3) Test health:

- GET http://localhost:8000/healthz

API
---

- POST `/api/chat/stream`

Request:

```json
{ "question": "What is X?", "country": "Canada" }
```

Response: streamed text/plain tokens (concatenate to form the answer).

- POST `/api/webhooks/ingest`

```json
{
  "source": "gov_site",
  "url": "https://example.gov/law.pdf",
  "country": "Canada",
  "title": "Act 123",
  "text": "Extracted text ...",
  "metadata": { "year": 2021 }
}
```

- POST `/api/webhooks/n8n`

Generic n8n ingest payload with fields `{ text, url, title, country, source, metadata }`.

Notes
-----
- By default SQLite is used for simplicity; embeddings stored as JSON for demo purposes.
- To use Postgres + pgvector:
  1. Start DB: `docker compose up -d db`
  2. Set `DB_URL` in `.env`, e.g. `postgresql+psycopg2://postgres:postgres@localhost:5432/paralegal`
  3. Restart the server. Tables and the `vector` extension will be created automatically.
