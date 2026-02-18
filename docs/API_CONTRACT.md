API Contract — Paralegal Assistant
==================================

Overview
--------
Two primary integrations:
1) Frontend → Backend chat (streaming)
2) n8n → Backend ingest webhook (store text + metadata for retrieval)

1) Chat (streaming)
-------------------
- Endpoint: `POST /api/chat/stream`
- Content-Type: `application/json`
- Request:
```json
{ "question": "string", "country": "string|null" }
```
- Response: `text/plain` streamed chunks (concatenate to display).

2) Ingest (manual)
------------------
- Endpoint: `POST /api/webhooks/ingest`
- Content-Type: `application/json`
- Request:
```json
{
  "source": "string|null",
  "url": "string|null",
  "country": "string|null",
  "title": "string|null",
  "text": "string (required)",
  "metadata": { "any": "json" }
}
```
- Response:
```json
{ "status": "ok", "document_id": 123 }
```

3) Ingest (n8n generic)
-----------------------
- Endpoint: `POST /api/webhooks/n8n`
- Content-Type: `application/json`
- Request (same shape as manual ingest; `source` defaults to `"n8n"` if omitted):
```json
{
  "source": "n8n",
  "url": "https://example.gov/law.pdf",
  "country": "Canada",
  "title": "Act 123",
  "text": "Extracted text...",
  "metadata": { "year": 2021 }
}
```
- Response:
```json
{ "status": "ok", "document_id": 124 }
```

Notes
-----
- Backend runs at `http://127.0.0.1:8000` in dev; frontend uses `NEXT_PUBLIC_BACKEND_URL`.
- Retrieval uses SQLite + OpenAI embeddings for demo; plan to move to Postgres + pgvector.
- Country is optional; when provided, retrieval is filtered to that jurisdiction.

