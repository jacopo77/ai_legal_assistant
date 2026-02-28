from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()


class N8NPayload(BaseModel):
    source: str
    url: str | None = None
    country: str | None = None
    title: str | None = None
    text: str
    metadata: Dict[str, Any] | None = None


@router.post("/n8n")
async def n8n_ingest(payload: N8NPayload, background_tasks: BackgroundTasks):
    """
    Receive ingested document text from n8n. This enqueues chunking + embedding work.
    """
    if not payload.text:
        raise HTTPException(status_code=400, detail="text is required")

    # In production this would push to a jobs queue or background worker.
    background_tasks.add_task(_store_and_process, payload.dict())
    return {"status": "accepted"}


def _store_and_process(doc: dict):
    # Placeholder: store raw doc, chunk text, create embeddings, save to DB.
    # We'll implement the helpers in app.core.*
    print("Processing document:", doc.get("title") or doc.get("url"))

