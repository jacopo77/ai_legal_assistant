from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_OPENSTATES_TIMEOUT = 25.0

# US state names (lowercase) used to detect state jurisdictions
_US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
}


@dataclass
class LiveResult:
    text: str
    title: str
    url: str
    citation: Optional[str]
    authority: str
    source: str


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_ecfr(query: str, max_results: int = 4) -> List[LiveResult]:
    """Search the eCFR for regulation sections matching the query."""
    # Fetch extra results to allow deduplication to still yield max_results unique hits
    fetch_count = max_results * 3
    url = (
        f"https://www.ecfr.gov/api/search/v1/results"
        f"?query={quote_plus(query)}&per_page={fetch_count}"
    )
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("eCFR search failed: %s", exc)
        return []

    results: List[LiveResult] = []
    for item in data.get("results", []):
        hierarchy = item.get("hierarchy", {})
        headings = item.get("hierarchy_headings", {})
        title_num = hierarchy.get("title", "")
        part = hierarchy.get("part", "")
        section = hierarchy.get("section", "")

        if section:
            citation = f"{title_num} C.F.R. § {section}"
            source_url = f"https://www.ecfr.gov/current/title-{title_num}/part-{part}/section-{section}"
        elif part:
            citation = f"{title_num} C.F.R. Part {part}"
            source_url = f"https://www.ecfr.gov/current/title-{title_num}/part-{part}"
        else:
            citation = f"{title_num} C.F.R."
            source_url = f"https://www.ecfr.gov/current/title-{title_num}"

        excerpt = _strip_html(item.get("full_text_excerpt", ""))
        title_label = _strip_html(
            headings.get("section") or headings.get("part") or headings.get("chapter") or ""
        )
        chapter_label = _strip_html(headings.get("chapter") or "")

        if not excerpt:
            continue

        display_title = title_label or citation
        if chapter_label and chapter_label not in display_title:
            display_title = f"{chapter_label} — {display_title}"

        results.append(
            LiveResult(
                text=excerpt,
                title=display_title,
                url=source_url,
                citation=citation,
                authority="Electronic Code of Federal Regulations (eCFR) / Government Publishing Office",
                source="ecfr",
            )
        )

    logger.warning("eCFR returned %d result(s) for query: %r", len(results), query)
    return results


def _fetch_fr_fulltext(body_html_url: str, query: str, max_chars: int = 800) -> str:
    """Fetch the most relevant excerpt from a Federal Register document's full HTML body."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(body_html_url)
            r.raise_for_status()
    except Exception as exc:
        logger.debug("FR full-text fetch failed for %s: %s", body_html_url, exc)
        return ""

    text = re.sub(r"<[^>]+>", " ", r.text)
    text = re.sub(r"\s+", " ", text).strip()

    # Find the most relevant passage using keyword overlap with the query
    query_words = set(re.findall(r"\w+", query.lower())) - {"the", "a", "an", "of", "in", "is", "what", "are", "under"}
    best_idx = 0
    best_score = 0
    window = 600
    for i in range(0, len(text) - window, 100):
        chunk = text[i : i + window].lower()
        score = sum(1 for w in query_words if w in chunk)
        if score > best_score:
            best_score = score
            best_idx = i

    excerpt = text[best_idx : best_idx + max_chars].strip()
    return excerpt if best_score > 0 else ""


def fetch_federal_register(query: str, max_results: int = 3) -> List[LiveResult]:
    """Search the Federal Register API for documents matching the query."""
    url = (
        f"https://www.federalregister.gov/api/v1/documents.json"
        f"?conditions[term]={quote_plus(query)}"
        f"&per_page={max_results}"
        f"&order=relevance"
        f"&fields[]=title&fields[]=abstract&fields[]=html_url&fields[]=citation"
        f"&fields[]=type&fields[]=body_html_url"
    )
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("Federal Register search failed: %s", exc)
        return []

    results: List[LiveResult] = []
    items = data.get("results", [])
    for idx, item in enumerate(items):
        abstract = (item.get("abstract") or "").strip()
        title = (item.get("title") or "").strip()
        if not abstract and not title:
            continue

        # For the top result, also fetch full text to surface specific figures/details
        full_excerpt = ""
        if idx == 0:
            body_url = item.get("body_html_url", "")
            if body_url:
                full_excerpt = _fetch_fr_fulltext(body_url, query, max_chars=1200)

        if full_excerpt:
            text = f"Title: {title}\n\nKey text: {full_excerpt}"
        elif abstract:
            text = f"Title: {title}\n\nAbstract: {abstract}"
        else:
            text = f"Title: {title}"

        results.append(
            LiveResult(
                text=text,
                title=title,
                url=item.get("html_url", ""),
                citation=item.get("citation"),
                authority="National Archives and Records Administration — Federal Register",
                source="federal_register",
            )
        )

    logger.warning("Federal Register returned %d result(s) for query: %r", len(results), query)
    return results


def fetch_openstates(query: str, state: str, max_results: int = 3) -> List[LiveResult]:
    """Search the OpenStates v3 API for state bills matching the query."""
    api_key = os.environ.get("OPENSTATES_API_KEY", "").strip()
    if not api_key:
        logger.warning("OPENSTATES_API_KEY not set — skipping state legislation search")
        return []

    params = {
        "jurisdiction": state,
        "q": query,
        "per_page": max_results,
        "include": "abstracts",
    }
    try:
        with httpx.Client(timeout=_OPENSTATES_TIMEOUT, headers={"X-API-KEY": api_key}) as client:
            r = client.get("https://v3.openstates.org/bills", params=params)
            logger.info(
                "OpenStates request URL: %s | status: %d",
                r.url,
                r.status_code,
            )
            if r.status_code == 401:
                logger.error("OpenStates API key rejected (401). Verify key at open.pluralpolicy.com")
                return []
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("OpenStates HTTP error for %r: %s", state, exc)
        return []
    except Exception as exc:
        logger.warning("OpenStates search failed for %r: %s", state, exc)
        return []

    results: List[LiveResult] = []
    for item in data.get("results", []):
        identifier = item.get("identifier", "")
        title = (item.get("title") or "").strip()
        openstates_url = item.get("openstates_url", "")

        abstracts = item.get("abstracts", [])
        abstract_text = abstracts[0].get("abstract", "").strip() if abstracts else ""

        if not title:
            continue

        text = f"Title: {title}"
        if abstract_text:
            text += f"\n\nAbstract: {abstract_text}"

        citation = f"{state} — {identifier}" if identifier else state

        results.append(
            LiveResult(
                text=text,
                title=title,
                url=openstates_url,
                citation=citation,
                authority=f"{state} Legislature via OpenStates",
                source="openstates",
            )
        )

    logger.info("OpenStates returned %d result(s) for %r / query: %r", len(results), state, query)
    return results


# Maps full US state names to CourtListener jurisdiction codes.
# Each state has at least one supreme court code; appellate codes added where useful.
_CL_JURISDICTION: dict = {
    "alabama": "ala",
    "alaska": "alaska",
    "arizona": "ariz",
    "arkansas": "ark",
    "california": "cal",
    "colorado": "colo",
    "connecticut": "conn",
    "delaware": "del",
    "florida": "fla",
    "georgia": "ga",
    "hawaii": "haw",
    "idaho": "idaho",
    "illinois": "ill",
    "indiana": "ind",
    "iowa": "iowa",
    "kansas": "kan",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "mass",
    "michigan": "mich",
    "minnesota": "minn",
    "mississippi": "miss",
    "missouri": "mo",
    "montana": "mont",
    "nebraska": "neb",
    "nevada": "nev",
    "new hampshire": "nh",
    "new jersey": "nj",
    "new mexico": "nm",
    "new york": "ny",
    "north carolina": "nc",
    "north dakota": "nd",
    "ohio": "ohio",
    "oklahoma": "okla",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhode island": "ri",
    "south carolina": "sc",
    "south dakota": "sd",
    "tennessee": "tenn",
    "texas": "tex",
    "utah": "utah",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wash",
    "west virginia": "wva",
    "wisconsin": "wis",
    "wyoming": "wyo",
}


def fetch_courtlistener(query: str, state: str, max_results: int = 3) -> List[LiveResult]:
    """Search CourtListener for state court opinions relevant to the query.

    CourtListener (Free Law Project) is a free, public API — no key required.
    State court opinions cite and apply enacted statutes, giving us indirect
    coverage of state law even when no statute database API is available.
    """
    jx_code = _CL_JURISDICTION.get(state.lower(), "")
    # State name is included in the search query; court filter is omitted so
    # CourtListener's own relevance ranking selects the best opinions.
    court_param = ""

    # Build the CourtListener query from the user's question.
    # Strip common question words, keep the substantive legal terms.
    _STOPWORDS = r"\b(what|are|the|is|a|an|of|in|for|how|does|do|under|have|has|been|that|this|those|these|regarding|about|related|law|rules|rule|rights|right|i|can|my|your|their|its|will|would|should|could|when|where|which)\b"
    search_q = re.sub(_STOPWORDS, "", query.lower())
    search_q = re.sub(r"[?!.,]", "", search_q)
    search_q = re.sub(r"\s+", " ", search_q).strip()

    # When tenant-related, add "landlord" to disambiguate from unrelated uses
    # of terms like "security" (e.g. security companies, national security).
    if "tenant" in search_q and "landlord" not in search_q:
        search_q = f"landlord {search_q}"

    if state.lower() not in search_q:
        search_q = f"{search_q} {state}"

    # Fetch a large page so we can filter for results with substantive snippets.
    # Good snippets appear further down CourtListener's ranking for specific topics,
    # so fetching 20 candidates and picking the best is more reliable than top-3.
    params: dict = {
        "q": search_q,
        "type": "o",
        "stat_Precedential": "on",
        "order_by": "score desc",
        "page_size": 20,
    }
    if court_param:
        params["court"] = court_param.strip()

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(
                "https://www.courtlistener.com/api/rest/v4/search/",
                params=params,
                headers={"User-Agent": "LegalSearchHub/1.0"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("CourtListener search failed for %r: %s", state, exc)
        return []

    # Patterns that indicate a snippet is just a filing header, not legal substance
    _HEADER_PATTERNS = re.compile(
        r"^(Filed \d|CERTIFIED FOR|IN THE COURT OF|APPELLATE DIVISION|COURT OF APPEAL|"
        r"SUPERIOR COURT|OSCN Found|J-A\d+)",
        re.IGNORECASE,
    )

    substantive: List[LiveResult] = []
    with_header: List[LiveResult] = []

    for item in data.get("results", []):
        case_name = (item.get("caseName") or item.get("case_name") or "").strip()
        citation_list = item.get("citation", [])
        citation_str = citation_list[0] if citation_list else None
        absolute_url = item.get("absolute_url", "")
        cl_url = f"https://www.courtlistener.com{absolute_url}" if absolute_url else ""

        # Snippet is nested inside the opinions array in CourtListener v4
        snippet = ""
        opinions = item.get("opinions") or []
        if opinions and isinstance(opinions, list):
            raw = opinions[0].get("snippet", "") or ""
            snippet = _strip_html(raw).strip()
            snippet = re.sub(r"\s+", " ", snippet)

        if not case_name:
            continue

        text = f"Case: {case_name}"
        if snippet:
            text += f"\n\nExcerpt: {snippet}"

        result = LiveResult(
            text=text,
            title=case_name,
            url=cl_url,
            citation=citation_str or case_name,
            authority=f"{state} Courts via CourtListener (Free Law Project)",
            source="courtlistener",
        )

        # Prefer results with substantive snippet text over bare headers
        if snippet and not _HEADER_PATTERNS.match(snippet):
            substantive.append(result)
        else:
            with_header.append(result)

    # Return substantive results first, filling up to max_results with header-only ones
    combined = (substantive + with_header)[:max_results]

    logger.info(
        "CourtListener: %d substantive + %d header-only results for %r / query: %r",
        len(substantive), len(with_header), state, search_q,
    )
    return combined


def fetch_uscode(query: str, max_results: int = 3) -> List[LiveResult]:
    """Search the US Code via the GovInfo API (Government Publishing Office).

    Covers all titles of the United States Code — contracts, labor, civil rights,
    criminal law, tax, immigration, etc. Requires GOVINFO_API_KEY env var (free).
    Falls back gracefully if key is not set.
    """
    api_key = os.environ.get("GOVINFO_API_KEY", "").strip()
    if not api_key:
        logger.warning("GOVINFO_API_KEY not set — skipping US Code search")
        return []

    body = {
        "query": query,
        "pageSize": max_results * 2,
        "offsetMark": "*",
        "collections": ["USCODE"],
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.post(
                "https://api.govinfo.gov/search",
                json=body,
                params={"api_key": api_key},
                headers={"User-Agent": "LegalSearchHub/1.0"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("GovInfo US Code search failed: %s", exc)
        return []

    results: List[LiveResult] = []
    for item in (data.get("results") or []):
        title = item.get("title", "").strip()
        package_id = item.get("packageId", "")
        granule_id = item.get("granuleId", "")
        doc_url = item.get("resultLink", "") or item.get("relatedLink", "") or ""

        # Build a readable citation from the package/granule IDs
        # e.g. USCODE-2023-title29 → 29 U.S.C.
        citation = title
        if package_id:
            parts = package_id.split("-")
            if len(parts) >= 3 and "title" in parts[-1]:
                title_num = parts[-1].replace("title", "").strip()
                citation = f"{title_num} U.S.C. — {title}" if title else f"{title_num} U.S.C."

        if not title:
            continue

        text = f"US Code: {title}"
        if granule_id:
            text += f" [{granule_id}]"

        results.append(
            LiveResult(
                text=text,
                title=title,
                url=doc_url,
                citation=citation,
                authority="United States Code via GovInfo (Government Publishing Office)",
                source="uscode",
            )
        )

    logger.info("GovInfo US Code returned %d result(s) for query: %r", len(results), query)
    return results[:max_results]


def fetch_courtlistener_federal(query: str, max_results: int = 3) -> List[LiveResult]:
    """Search CourtListener for US federal court opinions (SCOTUS, Circuit, District).

    Covers Supreme Court and all federal appellate/district courts — no API key needed.
    Adds federal case law to complement eCFR and Federal Register sources.
    """
    _STOPWORDS = r"\b(what|are|the|is|a|an|of|in|for|how|does|do|under|have|has|been|that|this|those|these|regarding|about|related|law|rules|rule|rights|right|i|can|my|your|their|its|will|would|should|could|when|where|which)\b"
    search_q = re.sub(_STOPWORDS, "", query.lower())
    search_q = re.sub(r"[?!.,]", "", search_q)
    search_q = re.sub(r"\s+", " ", search_q).strip()

    # Restrict to federal courts: Supreme Court + all Circuit Courts of Appeal
    # scotus = Supreme Court; ca1-ca11, cadc, cafc = Circuit Courts
    params: dict = {
        "q": search_q,
        "type": "o",
        "stat_Precedential": "on",
        "order_by": "score desc",
        "page_size": 20,
        "court": "scotus ca1 ca2 ca3 ca4 ca5 ca6 ca7 ca8 ca9 ca10 ca11 cadc cafc",
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(
                "https://www.courtlistener.com/api/rest/v4/search/",
                params=params,
                headers={"User-Agent": "LegalSearchHub/1.0"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("CourtListener federal search failed: %s", exc)
        return []

    _HEADER_PATTERNS = re.compile(
        r"^(Filed \d|CERTIFIED FOR|IN THE COURT OF|APPELLATE DIVISION|COURT OF APPEAL|"
        r"SUPERIOR COURT|OSCN Found|J-A\d+|FOR PUBLICATION|NOT FOR PUBLICATION)",
        re.IGNORECASE,
    )

    substantive: List[LiveResult] = []
    with_header: List[LiveResult] = []

    for item in data.get("results", []):
        case_name = (item.get("caseName") or item.get("case_name") or "").strip()
        citation_list = item.get("citation", [])
        citation_str = citation_list[0] if citation_list else None
        absolute_url = item.get("absolute_url", "")
        cl_url = f"https://www.courtlistener.com{absolute_url}" if absolute_url else ""
        court = item.get("court_citation_string") or item.get("court", "")

        opinions = item.get("opinions") or []
        snippet = ""
        if opinions and isinstance(opinions, list):
            raw = opinions[0].get("snippet", "") or ""
            snippet = _strip_html(raw).strip()
            snippet = re.sub(r"\s+", " ", snippet)

        if not case_name:
            continue

        text = f"Case: {case_name}"
        if court:
            text += f" ({court})"
        if snippet:
            text += f"\n\nExcerpt: {snippet}"

        result = LiveResult(
            text=text,
            title=case_name,
            url=cl_url,
            citation=citation_str or case_name,
            authority="US Federal Courts via CourtListener (Free Law Project)",
            source="courtlistener_federal",
        )

        if snippet and not _HEADER_PATTERNS.match(snippet):
            substantive.append(result)
        else:
            with_header.append(result)

    combined = (substantive + with_header)[:max_results]
    logger.info(
        "CourtListener federal: %d substantive + %d header-only results for query: %r",
        len(substantive), len(with_header), search_q,
    )
    return combined


def retrieve_live(
    question: str,
    jurisdiction: Optional[str] = None,
    max_results: int = 7,
) -> List[LiveResult]:
    """
    Query live official sources in parallel and return combined results.

    For US Federal: searches eCFR and Federal Register concurrently.
    For a US state: searches both sources with the state name added to the
    query so HUD, FTC, and other federal regulations that apply to states
    are retrieved alongside CourtListener state case law.
    All sources run in parallel — slow or failing sources are skipped
    without blocking the response.
    """
    # Strip surrounding quotes users may type (e.g. "What is X?" → What is X?)
    # Quoted phrases break eCFR/Federal Register Lucene search with zero results
    question = question.strip().strip('"\'')

    is_state = (
        jurisdiction is not None
        and jurisdiction.upper() not in ("US", "US FEDERAL")
        and jurisdiction.lower() in _US_STATES
    )

    # Strip common question words to produce a keyword-focused search query.
    # This improves eCFR/Federal Register relevance vs sending the full question sentence.
    _STOPWORDS = re.compile(
        r"\b(what|does|do|is|are|the|a|an|of|in|for|how|under|have|has|been|that|"
        r"this|those|these|about|related|i|can|my|your|their|its|will|would|should|"
        r"could|when|where|which|say|says|said|tell|me|us|federal|law|laws|legal|"
        r"rights|right|requirements|requirement)\b",
        re.IGNORECASE,
    )
    keywords = re.sub(_STOPWORDS, " ", question)
    keywords = re.sub(r"[?!.,]", " ", keywords)
    keywords = re.sub(r"\s+", " ", keywords).strip()
    # Fall back to full question if keyword extraction strips too much
    search_query = keywords if len(keywords) > 10 else question

    # For state queries, embed the state name so federal APIs return state-relevant results
    query = f"{search_query} {jurisdiction}" if is_state else search_query

    combined: List[LiveResult] = []
    seen_citations: set = set()

    def _dedup(results: List[LiveResult]) -> List[LiveResult]:
        unique = []
        for r in results:
            key = r.citation or r.url or r.text[:80]
            if key not in seen_citations:
                seen_citations.add(key)
                unique.append(r)
        return unique

    with ThreadPoolExecutor(max_workers=5) as executor:
        if is_state:
            futures = {
                executor.submit(fetch_ecfr, query, 3): "ecfr",
                executor.submit(fetch_federal_register, query, 2): "fr",
                executor.submit(fetch_courtlistener, question, jurisdiction, 3): "courtlistener",
                executor.submit(fetch_uscode, question, 2): "uscode",
            }
        else:
            futures = {
                executor.submit(fetch_ecfr, query, 3): "ecfr",
                executor.submit(fetch_federal_register, query, 2): "fr",
                executor.submit(fetch_courtlistener_federal, question, 3): "courtlistener_federal",
                executor.submit(fetch_uscode, question, 3): "uscode",
            }

        try:
            for future in as_completed(futures, timeout=30):
                name = futures[future]
                try:
                    results = _dedup(future.result())
                    combined.extend(results)
                    logger.warning("Source %r returned %d unique result(s)", name, len(results))
                except Exception as exc:
                    logger.warning("Source %r failed: %s", name, exc)
        except Exception as exc:
            logger.warning("Parallel retrieval timed out or failed: %s", exc)

    logger.info(
        "Live retrieval: %d total result(s) for jurisdiction=%r",
        len(combined),
        jurisdiction,
    )
    return combined[:max_results]
