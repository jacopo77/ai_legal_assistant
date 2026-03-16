from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0


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


def retrieve_live(
    question: str,
    jurisdiction: Optional[str] = None,
    max_results: int = 7,
) -> List[LiveResult]:
    """
    Query eCFR and Federal Register in parallel and return combined results.

    For US Federal (or no jurisdiction), searches both sources.
    For state jurisdictions, appends the state name to the query so eCFR
    and Federal Register surface state-relevant federal rules where available.
    """
    query = question
    if jurisdiction and jurisdiction.upper() not in ("US", "US FEDERAL"):
        query = f"{question} {jurisdiction}"

    ecfr_results = fetch_ecfr(query, max_results=4)
    fr_results = fetch_federal_register(query, max_results=3)

    combined = ecfr_results + fr_results
    logger.info(
        "Live retrieval: %d eCFR + %d Federal Register = %d total result(s)",
        len(ecfr_results),
        len(fr_results),
        len(combined),
    )
    return combined[:max_results]
