from __future__ import annotations

import logging
from typing import Generator, List, Optional

from .embeddings import embed_texts
from .llm import stream_completion
from ..core.settings import get_settings
from .storage import save_document as save_document_sqlite
from .storage import save_chunks as save_chunks_sqlite
from .storage import retrieve_similar as retrieve_similar_sqlite
from .storage import RetrievedChunk as RetrievedChunkSqlite
from .live_retrieval import LiveResult, retrieve_live

logger = logging.getLogger(__name__)

# --- Supabase REST client (preferred: works over HTTPS, bypasses DNS issues) ---
try:
    from .storage_supabase import save_document as save_document_sb  # type: ignore
    from .storage_supabase import save_chunks as save_chunks_sb  # type: ignore
    from .storage_supabase import retrieve_similar as retrieve_similar_sb  # type: ignore
    _sb_import_ok = True
except Exception as _sb_import_err:
    save_document_sb = None  # type: ignore
    save_chunks_sb = None  # type: ignore
    retrieve_similar_sb = None  # type: ignore
    _sb_import_ok = False
    logger.warning("storage_supabase import failed: %s", _sb_import_err)

# --- Direct Postgres fallback (blocked by Cisco Umbrella on some networks) ---
try:
    from .storage_pg import save_document as save_document_pg  # type: ignore
    from .storage_pg import save_chunks as save_chunks_pg  # type: ignore
    from .storage_pg import retrieve_similar as retrieve_similar_pg  # type: ignore
    _pg_import_ok = True
except Exception as _pg_import_err:
    save_document_pg = None  # type: ignore
    save_chunks_pg = None  # type: ignore
    retrieve_similar_pg = None  # type: ignore
    _pg_import_ok = False
    logger.warning("storage_pg import failed: %s", _pg_import_err)


def _storage_mode() -> str:
    """Returns 'supabase', 'postgres', or 'sqlite' based on available config."""
    settings = get_settings()
    if _sb_import_ok and settings.supabase_url and settings.supabase_key and settings.supabase_key != "YOUR_SERVICE_ROLE_KEY_HERE":
        return "supabase"
    if _pg_import_ok and settings.db_url:
        return "postgres"
    return "sqlite"


def add_document(*, source: Optional[str], url: Optional[str], country: Optional[str], title: Optional[str], text: str, metadata: dict) -> int:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    logger.info("Generating embeddings for %d chunk(s)...", len(parts))
    embeddings = embed_texts(parts)

    mode = _storage_mode()

    if mode == "supabase":
        logger.info("Saving document via Supabase REST API...")
        try:
            doc_id = save_document_sb(source=source, url=url, country=country, title=title, content=text, metadata=metadata)  # type: ignore
            save_chunks_sb(doc_id, list(zip(parts, embeddings)))  # type: ignore
            logger.info("✅ Document %d saved to Supabase via REST (%d chunks).", doc_id, len(parts))
            return doc_id
        except Exception as exc:
            logger.error("❌ Supabase REST save failed: %s", exc)
            raise

    elif mode == "postgres":
        logger.info("Saving document via direct Postgres connection...")
        try:
            doc_id = save_document_pg(source=source, url=url, country=country, title=title, content=text, metadata=metadata)  # type: ignore
            save_chunks_pg(doc_id, list(zip(parts, embeddings)))  # type: ignore
            logger.info("✅ Document %d saved to Postgres (%d chunks).", doc_id, len(parts))
            return doc_id
        except Exception as exc:
            logger.error(
                "❌ Postgres save failed: %s\n"
                "   Hit GET /api/health/db for diagnostics.",
                exc,
            )
            raise

    else:
        logger.info("No cloud DB configured — saving to local SQLite...")
        doc_id = save_document_sqlite(source=source, url=url, country=country, title=title, content=text, metadata=metadata)
        save_chunks_sqlite(doc_id, list(zip(parts, embeddings)))
        logger.info("✅ Document %d saved to SQLite (%d chunks).", doc_id, len(parts))
        return doc_id


def _build_prompt(question: str, country: Optional[str], results: List[LiveResult]) -> str:
    context_lines: List[str] = []
    for idx, r in enumerate(results, start=1):
        meta_parts = []
        if r.citation:
            meta_parts.append(r.citation)
        if r.title and r.title not in (r.citation or ""):
            meta_parts.append(r.title)
        meta_parts.append(r.authority)
        if r.url:
            meta_parts.append(r.url)
        meta_str = " — ".join(meta_parts)
        context_lines.append(f"[{idx}] {r.text}\n{meta_str}")

    context = "\n\n".join(context_lines) if context_lines else "No relevant context found."
    location = f" for {country}" if country else ""
    instructions = (
        "You are a careful paralegal assistant. Answer strictly using the provided official-source context snippets. "
        "Cite sources inline like [1], [2] where relevant. "
        "If the snippets do not provide enough coverage to answer confidently, say so clearly. "
        "Do not make up legal claims not supported by the provided context."
    )
    return f"{instructions}\n\nQuestion{location}: {question}\n\nContext:\n{context}\n\nAnswer:"


def answer_stream(question: str, country: Optional[str]) -> Generator[str, None, None]:
    logger.info("Live retrieval for question: %r (jurisdiction: %r)", question, country)
    results = retrieve_live(question, jurisdiction=country, max_results=7)

    if not results:
        location = f" for {country}" if country else ""
        yield (
            f"I was unable to retrieve relevant results from official federal sources{location} "
            "for that question. Please try rephrasing or check back shortly."
        )
        return

    user_prompt = _build_prompt(question, country, results)
    system_prompt = "You produce concise, legally careful answers with inline citations."
    for chunk in stream_completion(system_prompt, user_prompt):
        yield chunk

