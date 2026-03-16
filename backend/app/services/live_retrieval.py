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

    logger.info("eCFR returned %d result(s) for query: %r", len(results), query)
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

    logger.info("Federal Register returned %d result(s) for query: %r", len(results), query)
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


def retrieve_live(
    question: str,
    jurisdiction: Optional[str] = None,
    max_results: int = 7,
) -> List[LiveResult]:
    """
    Query live official sources in parallel and return combined results.

    For US Federal: searches eCFR and Federal Register concurrently.
    For a US state: adds OpenStates bill search concurrently.
    All sources run in parallel — slow or failing sources are skipped
    without blocking the response.
    """
    is_state = (
        jurisdiction is not None
        and jurisdiction.upper() not in ("US", "US FEDERAL")
        and jurisdiction.lower() in _US_STATES
    )

    query = f"{question} {jurisdiction}" if is_state else question

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

    with ThreadPoolExecutor(max_workers=3) as executor:
        if is_state:
            futures = {
                executor.submit(fetch_ecfr, query, 2): "ecfr",
                executor.submit(fetch_federal_register, query, 2): "fr",
                executor.submit(fetch_openstates, question, jurisdiction, 3): "openstates",
            }
        else:
            futures = {
                executor.submit(fetch_ecfr, query, 4): "ecfr",
                executor.submit(fetch_federal_register, query, 3): "fr",
            }

        try:
            for future in as_completed(futures, timeout=30):
                name = futures[future]
                try:
                    results = _dedup(future.result())
                    combined.extend(results)
                    logger.info("Source %r returned %d unique result(s)", name, len(results))
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
