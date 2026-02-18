from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ..models.schemas import IngestRequest, N8nPayload
from ..services.rag import add_document

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/ingest")
def ingest(req: IngestRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    doc_id = add_document(
        source=req.source,
        url=req.url,
        country=req.country,
        title=req.title,
        text=req.text,
        metadata=req.metadata or {},
    )
    return {"status": "ok", "document_id": doc_id}


@router.post("/n8n")
def n8n_ingest(payload: N8nPayload):
    """
    Generic n8n webhook to upsert document text.
    Expect fields: text, url, title, country, source, metadata.
    """
    if not payload.text:
        raise HTTPException(status_code=400, detail="text is required")
    doc_id = add_document(
        source=payload.source or "n8n",
        url=payload.url,
        country=payload.country,
        title=payload.title,
        text=payload.text,
        metadata=payload.metadata or {},
    )
    return {"status": "ok", "document_id": doc_id}

