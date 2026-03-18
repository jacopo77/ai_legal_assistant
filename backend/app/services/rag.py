from __future__ import annotations

import json
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


_US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
}


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

    is_state = country and country.lower() in _US_STATE_NAMES
    if is_state:
        instructions = (
            f"You are a careful paralegal assistant. The user is asking about {country} state law. "
            f"The provided context contains federal regulations (eCFR, Federal Register) and court opinions that may be relevant. "
            "Answer using the provided sources where applicable, citing them inline like [1], [2]. "
            f"Where the federal sources do not directly cover {country}-specific law, clearly say so and direct the user to "
            f"the official {country} legislature website (e.g., for California: leginfo.legislature.ca.gov) "
            "to find the specific state statute. Do not fabricate state law citations."
        )
    else:
        instructions = (
            "You are a careful paralegal assistant. Use the provided official-source context snippets as your primary citations, "
            "citing them inline like [1], [2] where relevant. "
            "When the snippets reference the topic but do not fully answer the question (e.g. they contain implementing regulations "
            "rather than the statute itself), supplement with well-established general legal knowledge to give a complete, helpful answer. "
            "Clearly distinguish between what the retrieved snippets say and what is general legal knowledge. "
            "Do not fabricate citations or invent case names — only cite sources from the provided context."
        )
    return f"{instructions}\n\nQuestion{location}: {question}\n\nContext:\n{context}\n\nAnswer:"


def answer_stream(question: str, country: Optional[str], results: Optional[List[LiveResult]] = None) -> Generator[str, None, None]:
    if results is None:
        logger.info("Live retrieval for question: %r (jurisdiction: %r)", question, country)
        results = retrieve_live(question, jurisdiction=country, max_results=7)

    if not results:
        location = f" for {country}" if country else ""
        state_resources = {
            "texas": "https://www.sos.state.tx.us/corp/index.shtml",
            "california": "https://bizfileonline.sos.ca.gov",
            "new york": "https://www.dos.ny.gov/corps",
            "florida": "https://dos.myflorida.com/sunbiz",
        }
        state_url = state_resources.get(country.lower(), f"https://www.google.com/search?q={country}+official+legislature+website") if country else ""
        fallback_note = (
            f" Note: No official federal source citations were found for this {country} state law question. "
            f"For authoritative state statutes, visit your state's official legislature or secretary of state website"
            f"{': ' + state_url if state_url else ''}."
        ) if country and country.upper() not in ("US", "US FEDERAL") else (
            " Note: No official source citations were found. Please verify this information with a licensed attorney."
        )
        fallback_prompt = (
            f"You are a careful paralegal assistant. A user asked: {question}\n\n"
            f"No official source documents were retrieved. Answer from general legal knowledge, "
            f"clearly noting this is general information only and not verified against official sources. "
            f"Be specific and helpful. End with a note directing the user to official state resources."
            f"\n\nJurisdiction: {country or 'US Federal'}"
        )
        for chunk in stream_completion(
            "You produce concise, legally careful answers. Always note when answers are based on general knowledge rather than retrieved official sources.",
            fallback_prompt,
        ):
            yield chunk
        yield fallback_note
        return

    user_prompt = _build_prompt(question, country, results)
    system_prompt = "You produce concise, legally careful answers with inline citations."
    for chunk in stream_completion(system_prompt, user_prompt):
        yield chunk

    # Append source metadata so the frontend can render clickable citation links
    sources_payload = [
        {"n": i, "citation": r.citation, "url": r.url, "title": r.title}
        for i, r in enumerate(results, start=1)
        if r.url
    ]
    yield f"\n\nSOURCES_DATA:{json.dumps(sources_payload)}"

