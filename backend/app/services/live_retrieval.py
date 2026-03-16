from __future__ import annotations

import logging
import os
import re
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
    url = (
        f"https://www.ecfr.gov/api/search/v1/results"
        f"?query={quote_plus(query)}&per_page={max_results}"
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


def fetch_federal_register(query: str, max_results: int = 3) -> List[LiveResult]:
    """Search the Federal Register API for documents matching the query."""
    url = (
        f"https://www.federalregister.gov/api/v1/documents.json"
        f"?conditions[term]={quote_plus(query)}"
        f"&per_page={max_results}"
        f"&order=relevance"
        f"&fields[]=title&fields[]=abstract&fields[]=html_url&fields[]=citation&fields[]=type"
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
    for item in data.get("results", []):
        abstract = (item.get("abstract") or "").strip()
        title = (item.get("title") or "").strip()
        if not abstract and not title:
            continue

        text = f"Title: {title}\n\nAbstract: {abstract}" if abstract else f"Title: {title}"
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
    Query live official sources and return combined results.

    For US Federal (or no jurisdiction): searches eCFR and Federal Register.
    For a US state: searches eCFR + Federal Register (federal rules relevant to
    that state) AND OpenStates for state-level bills/statutes.
    """
    is_state = (
        jurisdiction is not None
        and jurisdiction.upper() not in ("US", "US FEDERAL")
        and jurisdiction.lower() in _US_STATES
    )

    query = f"{question} {jurisdiction}" if is_state else question

    if is_state:
        # Allocate slots: 2 federal + 2 federal register + 3 state
        ecfr_results = fetch_ecfr(query, max_results=2)
        fr_results = fetch_federal_register(query, max_results=2)
        state_results = fetch_openstates(question, state=jurisdiction, max_results=3)  # type: ignore[arg-type]
        combined = ecfr_results + fr_results + state_results
    else:
        ecfr_results = fetch_ecfr(query, max_results=4)
        fr_results = fetch_federal_register(query, max_results=3)
        combined = ecfr_results + fr_results

    logger.info(
        "Live retrieval: %d total result(s) for jurisdiction=%r",
        len(combined),
        jurisdiction,
    )
    return combined[:max_results]
