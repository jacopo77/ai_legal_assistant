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

    # Run each retrieval source sequentially (no threading) to avoid any
    # ThreadPoolExecutor issues in the Railway/FastAPI environment
    from ..services.live_retrieval import fetch_ecfr, fetch_federal_register, fetch_courtlistener_federal, fetch_courtlistener, fetch_uscode, _US_STATES
    from typing import List
    from ..services.live_retrieval import LiveResult

    question = req.question
    country = req.country
    is_state = (
        country is not None
        and country.upper() not in ("US", "US FEDERAL")
        and country.lower() in _US_STATES
    )
    query = f"{question} {country}" if is_state else question

    combined: List[LiveResult] = []
    seen = set()

    def add(items):
        for r in items:
            key = r.citation or r.url or r.text[:80]
            if key not in seen:
                seen.add(key)
                combined.append(r)

    logger.info("Sequential retrieval starting for: %r (jurisdiction: %r)", question, country)
    ecfr_r, fr_r, cl_r, us_r = [], [], [], []
    try:
        ecfr_r = fetch_ecfr(query, 3)
        logger.info("eCFR returned %d", len(ecfr_r))
        add(ecfr_r)
    except Exception as e:
        logger.warning("eCFR failed: %s", e)
    try:
        fr_r = fetch_federal_register(query, 2)
        logger.info("FR returned %d", len(fr_r))
        add(fr_r)
    except Exception as e:
        logger.warning("Federal Register failed: %s", e)
    try:
        if is_state:
            cl_r = fetch_courtlistener(question, country, 3)
        else:
            cl_r = fetch_courtlistener_federal(question, 3)
        logger.info("CourtListener returned %d", len(cl_r))
        add(cl_r)
    except Exception as e:
        logger.warning("CourtListener failed: %s", e)
    try:
        us_r = fetch_uscode(question, 2)
        logger.info("GovInfo returned %d", len(us_r))
        add(us_r)
    except Exception as e:
        logger.warning("GovInfo failed: %s", e)

    results = combined[:7]
    logger.info("Sequential retrieval complete: ecfr=%d fr=%d cl=%d us=%d combined=%d",
                len(ecfr_r), len(fr_r), len(cl_r), len(us_r), len(results))

    def generator():
        for chunk in answer_stream(req.question, req.country, results=results):
            yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Retrieval-Count": str(len(results))},
    )

