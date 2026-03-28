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
            "Answer using the provided context sources. "
            "You MUST cite every factual claim with a numbered marker [1], [2], etc. immediately after the claim — "
            "even if the source text already contains a statutory section number. "
            "Do not substitute inline statutory references (like '§ 92.056') for the required numbered markers. "
            "Do not fabricate citations or add information not found in the provided sources."
        )
    else:
        instructions = (
            "You are a careful paralegal assistant. Answer using ONLY the provided official-source context snippets. "
            "Cite every claim inline with [1], [2], etc. "
            "Do not use general knowledge or add information not found in the retrieved sources. "
            "If the context covers the topic partially, answer only what the sources support and note any gaps."
        )
    return f"{instructions}\n\nQuestion{location}: {question}\n\nContext:\n{context}\n\nAnswer:"


def answer_stream(question: str, country: Optional[str], results: Optional[List[LiveResult]] = None) -> Generator[str, None, None]:
    if results is None:
        logger.info("Live retrieval for question: %r (jurisdiction: %r)", question, country)
        results = retrieve_live(question, jurisdiction=country, max_results=7)

    if not results:
        is_state_jurisdiction = country and country.upper() not in ("US", "US FEDERAL")
        state_resources = {
            "alabama": "https://legislature.state.al.us",
            "alaska": "https://legislature.alaska.gov",
            "arizona": "https://www.azleg.gov",
            "arkansas": "https://www.arkleg.state.ar.us",
            "california": "https://leginfo.legislature.ca.gov",
            "colorado": "https://leg.colorado.gov",
            "connecticut": "https://www.cga.ct.gov",
            "delaware": "https://legis.delaware.gov",
            "florida": "https://www.leg.state.fl.us",
            "georgia": "https://www.legis.ga.gov",
            "hawaii": "https://www.capitol.hawaii.gov",
            "idaho": "https://legislature.idaho.gov",
            "illinois": "https://www.ilga.gov",
            "indiana": "https://iga.in.gov",
            "iowa": "https://www.legis.iowa.gov",
            "kansas": "https://www.kslegislature.org",
            "kentucky": "https://legislature.ky.gov",
            "louisiana": "https://www.legis.la.gov",
            "maine": "https://legislature.maine.gov",
            "maryland": "https://mgaleg.maryland.gov",
            "massachusetts": "https://malegislature.gov",
            "michigan": "https://www.legislature.mi.gov",
            "minnesota": "https://www.leg.state.mn.us",
            "mississippi": "https://www.legislature.ms.gov",
            "missouri": "https://www.moga.mo.gov",
            "montana": "https://leg.mt.gov",
            "nebraska": "https://nebraskalegislature.gov",
            "nevada": "https://www.leg.state.nv.us",
            "new hampshire": "https://www.gencourt.state.nh.us",
            "new jersey": "https://www.njleg.state.nj.us",
            "new mexico": "https://www.nmlegis.gov",
            "new york": "https://www.nysenate.gov",
            "north carolina": "https://www.ncleg.gov",
            "north dakota": "https://www.legis.nd.gov",
            "ohio": "https://www.legislature.ohio.gov",
            "oklahoma": "https://www.oklegislature.gov",
            "oregon": "https://www.oregonlegislature.gov",
            "pennsylvania": "https://www.legis.state.pa.us",
            "rhode island": "https://www.rilegislature.gov",
            "south carolina": "https://www.scstatehouse.gov",
            "south dakota": "https://sdlegislature.gov",
            "tennessee": "https://www.tn.gov/legislature",
            "texas": "https://statutes.capitol.texas.gov",
            "utah": "https://le.utah.gov",
            "vermont": "https://legislature.vermont.gov",
            "virginia": "https://law.lis.virginia.gov",
            "washington": "https://app.leg.wa.gov",
            "west virginia": "https://www.wvlegislature.gov",
            "wisconsin": "https://docs.legis.wisconsin.gov",
            "wyoming": "https://www.wyoleg.gov",
        }
        if is_state_jurisdiction:
            state_url = state_resources.get(country.lower(), "")
            resource_line = f"\n- **{country} Legislature:** {state_url}" if state_url else ""
            yield (
                f"I was unable to find verified official sources for this {country} state law question. "
                f"Rather than risk providing an inaccurate answer, I won't guess.\n\n"
                f"**To get an authoritative answer, please check:**{resource_line}\n"
                f"- **CourtListener** (state court opinions): https://www.courtlistener.com\n"
                f"- **A licensed {country} attorney** for advice specific to your situation"
            )
        else:
            yield (
                "I was unable to find verified official sources for this question. "
                "Rather than risk providing an inaccurate answer, I won't guess.\n\n"
                "**To get an authoritative answer, please check:**\n"
                "- **eCFR** (federal regulations): https://www.ecfr.gov\n"
                "- **Federal Register**: https://www.federalregister.gov\n"
                "- **Cornell LII** (US Code): https://www.law.cornell.edu/uscode\n"
                "- **A licensed attorney** for advice specific to your situation"
            )
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

