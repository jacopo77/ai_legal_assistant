from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import ChatRequest
from ..services.rag import answer_stream
from ..services.live_retrieval import retrieve_live
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
def chat_stream(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    logger.warning("CHAT: starting retrieve_live for %r / jurisdiction=%r", req.question, req.country)
    try:
        results = retrieve_live(req.question, jurisdiction=req.country, max_results=7)
        logger.warning("CHAT: retrieve_live returned %d result(s)", len(results))
    except Exception as exc:
        logger.warning("CHAT: retrieve_live raised exception: %s", exc)
        results = []

    def generator():
        for chunk in answer_stream(req.question, req.country, results=results):
            yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Retrieval-Count": str(len(results))},
    )

