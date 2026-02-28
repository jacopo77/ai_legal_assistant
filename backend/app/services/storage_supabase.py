from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from ..core.settings import get_settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client  # type: ignore

        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in backend/.env. "
                "Get the service_role key from Supabase → Project Settings → API."
            )
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("✅ Supabase REST client initialised (%s)", settings.supabase_url)
    return _client


def save_document(
    *,
    source: Optional[str],
    url: Optional[str],
    country: Optional[str],
    title: Optional[str],
    content: str,
    metadata: Dict[str, Any],
) -> int:
    client = _get_client()
    result = (
        client.table("documents")
        .insert(
            {
                "source": source,
                "url": url,
                "country": country,
                "title": title,
                "content": content,
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    doc_id = int(result.data[0]["id"])
    logger.info("Document %d inserted into Supabase documents table.", doc_id)
    return doc_id


def save_chunks(document_id: int, chunks: Iterable[tuple[str, List[float]]]) -> None:
    client = _get_client()
    rows = [
        {
            "document_id": document_id,
            "text": text,
            # pgvector expects the embedding as a string "[0.1, 0.2, ...]"
            "embedding": str(embedding),
        }
        for text, embedding in chunks
    ]
    if rows:
        client.table("chunks").insert(rows).execute()
        logger.info("Inserted %d chunks for document %d.", len(rows), document_id)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: Optional[str]
    url: Optional[str]
    title: Optional[str]


def retrieve_similar(
    query_embedding: List[float], *, country: Optional[str], k: int = 6
) -> List[RetrievedChunk]:
    """
    Calls the match_chunks PostgreSQL function via Supabase RPC.
    That function must exist in your Supabase database — see
    docs/SUPABASE_VECTOR_FUNCTION.sql for the CREATE FUNCTION statement.
    """
    client = _get_client()
    params: Dict[str, Any] = {
        "query_embedding": str(query_embedding),
        "match_count": k,
    }
    if country:
        params["filter_country"] = country

    result = client.rpc("match_chunks", params).execute()
    return [
        RetrievedChunk(
            text=row["text"],
            score=float(row["score"]),
            source=row.get("source"),
            url=row.get("url"),
            title=row.get("title"),
        )
        for row in (result.data or [])
    ]
