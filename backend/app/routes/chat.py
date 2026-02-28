from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    jurisdiction: str | None = None


async def _fake_stream_answer(question: str):
    # Placeholder streaming generator; replace with model + RAG streaming.
    for part in [
        "Analyzing the question...",
        "Retrieving relevant documents...",
        "Synthesizing answer with citations [1], [2]...",
        "Final recommendation: consult a licensed attorney."
    ]:
        await asyncio.sleep(0.4)
        yield json.dumps({"delta": part}) + "\n\n"


@router.post("/stream")
async def stream_answer(req: ChatRequest):
    if not req.question:
        raise HTTPException(status_code=400, detail="question required")

    generator = _fake_stream_answer(req.question)
    return StreamingResponse(generator, media_type="text/event-stream")

