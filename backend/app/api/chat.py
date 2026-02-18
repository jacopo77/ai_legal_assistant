from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import ChatRequest
from ..services.rag import answer_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
def chat_stream(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    def generator():
        for chunk in answer_stream(req.question, req.country):
            yield chunk

    return StreamingResponse(generator(), media_type="text/plain; charset=utf-8")

