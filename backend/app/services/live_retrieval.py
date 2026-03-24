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

    logger.warning("eCFR returned %d result(s) for query: %r", len(results[:max_results]), query)
    return results[:max_results]


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
    # Strip common question words, keep substantive legal terms (rights, law, etc.).
    _STOPWORDS = r"\b(what|are|the|is|a|an|of|in|for|how|does|do|under|have|has|been|that|this|those|these|regarding|about|related|rules|rule|i|can|my|your|their|its|will|would|should|could|when|where|which)\b"
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



# ---------------------------------------------------------------------------
# Keyword → US Code section mapping.
# Each entry: (pattern, citation, lii_url, title_label, fallback_text)
# fallback_text is used when the live LII fetch fails or is blocked.
# ---------------------------------------------------------------------------
_STATUTE_MAP = [
    # Civil Rights Act — Title VII employment discrimination
    (
        re.compile(r"civil rights act|title vii|employment discrimination|race.{0,30}discriminat|color.{0,30}discriminat|religion.{0,30}discriminat|sex.{0,30}discriminat|national origin", re.I),
        "42 U.S.C. § 2000e-2",
        "https://www.law.cornell.edu/uscode/text/42/2000e-2",
        "Civil Rights Act — Unlawful Employment Practices (Title VII)",
        (
            "It shall be an unlawful employment practice for an employer— "
            "(1) to fail or refuse to hire or to discharge any individual, or otherwise to discriminate against any "
            "individual with respect to his compensation, terms, conditions, or privileges of employment, because of "
            "such individual's race, color, religion, sex, or national origin; or "
            "(2) to limit, segregate, or classify his employees or applicants for employment in any way which would "
            "deprive or tend to deprive any individual of employment opportunities or otherwise adversely affect his "
            "status as an employee, because of such individual's race, color, religion, sex, or national origin. "
            "(42 U.S.C. § 2000e-2, Civil Rights Act of 1964, Title VII)"
        ),
    ),
    # Civil Rights Act — Title II public accommodations
    (
        re.compile(r"public accommodation|restaurant|hotel|motel|place of public", re.I),
        "42 U.S.C. § 2000a",
        "https://www.law.cornell.edu/uscode/text/42/2000a",
        "Civil Rights Act — Public Accommodations (Title II)",
        (
            "All persons shall be entitled to the full and equal enjoyment of the goods, services, facilities, "
            "privileges, advantages, and accommodations of any place of public accommodation, as defined in this "
            "section, without discrimination on the ground of race, color, religion, or national origin. "
            "Places of public accommodation include hotels, motels, restaurants, motion picture houses, theaters, "
            "concert halls, sports arenas, and stadiums. (42 U.S.C. § 2000a, Civil Rights Act of 1964, Title II)"
        ),
    ),
    # Civil Rights Act — Title VI federal funding
    (
        re.compile(r"title vi|federal (funding|assistance|program).{0,30}discriminat|federally.{0,30}funded", re.I),
        "42 U.S.C. § 2000d",
        "https://www.law.cornell.edu/uscode/text/42/2000d",
        "Civil Rights Act — Nondiscrimination in Federal Programs (Title VI)",
        (
            "No person in the United States shall, on the ground of race, color, or national origin, be excluded "
            "from participation in, be denied the benefits of, or be subjected to discrimination under any program "
            "or activity receiving Federal financial assistance. (42 U.S.C. § 2000d, Civil Rights Act of 1964, Title VI)"
        ),
    ),
    # ADA — Americans with Disabilities Act
    (
        re.compile(r"\bADA\b|americans with disabilities|disability discriminat|reasonable accommodation", re.I),
        "42 U.S.C. § 12112",
        "https://www.law.cornell.edu/uscode/text/42/12112",
        "Americans with Disabilities Act — Prohibited Discrimination",
        (
            "No covered entity shall discriminate against a qualified individual on the basis of disability in regard "
            "to job application procedures, the hiring, advancement, or discharge of employees, employee compensation, "
            "job training, and other terms, conditions, and privileges of employment. "
            "Discrimination includes not making reasonable accommodations to the known physical or mental limitations "
            "of an otherwise qualified individual with a disability, unless the covered entity can demonstrate that "
            "the accommodation would impose an undue hardship on the operation of the business. "
            "(42 U.S.C. § 12112, Americans with Disabilities Act of 1990)"
        ),
    ),
    # FMLA — Family and Medical Leave
    (
        re.compile(r"\bFMLA\b|family.{0,15}medical leave|medical leave act|parental leave", re.I),
        "29 U.S.C. § 2612",
        "https://www.law.cornell.edu/uscode/text/29/2612",
        "Family and Medical Leave Act — Entitlement to Leave",
        (
            "An eligible employee shall be entitled to a total of 12 workweeks of leave during any 12-month period "
            "for one or more of the following: (A) Because of the birth of a son or daughter of the employee and in "
            "order to care for such son or daughter. (B) Because of the placement of a son or daughter with the "
            "employee for adoption or foster care. (C) In order to care for the spouse, or a son, daughter, or parent "
            "of the employee, if such spouse, son, daughter, or parent has a serious health condition. (D) Because of "
            "a serious health condition that makes the employee unable to perform the functions of the position of "
            "such employee. (29 U.S.C. § 2612, Family and Medical Leave Act of 1993)"
        ),
    ),
    # FLSA — Fair Labor Standards / minimum wage
    (
        re.compile(r"minimum wage|overtime pay|fair labor standards|\bFLSA\b|hourly wage", re.I),
        "29 U.S.C. § 206-207",
        "https://www.law.cornell.edu/uscode/text/29/206",
        "Fair Labor Standards Act — Minimum Wage and Overtime",
        (
            "Every employer shall pay to each of his employees who in any workweek is engaged in commerce or in the "
            "production of goods for commerce, wages at the following rates: not less than $7.25 an hour beginning "
            "July 24, 2009. (29 U.S.C. § 206) "
            "No employer shall employ any employee for a workweek longer than forty hours unless such employee "
            "receives compensation for his employment in excess of the hours above specified at a rate not less than "
            "one and one-half times the regular rate at which he is employed. (29 U.S.C. § 207, FLSA overtime rule)"
        ),
    ),
    # OSHA — workplace safety
    (
        re.compile(r"\bOSHA\b|workplace safety|occupational safety|hazard.{0,20}workplace", re.I),
        "29 U.S.C. § 654",
        "https://www.law.cornell.edu/uscode/text/29/654",
        "Occupational Safety and Health Act — Employer Duties",
        (
            "Each employer shall furnish to each of his employees employment and a place of employment which are free "
            "from recognized hazards that are causing or are likely to cause death or serious physical harm to his "
            "employees (the 'general duty clause'). Each employer shall comply with occupational safety and health "
            "standards promulgated under this chapter. Each employee shall comply with occupational safety and health "
            "standards and all rules, regulations, and orders issued pursuant to this chapter which are applicable "
            "to his own actions and conduct. (29 U.S.C. § 654, Occupational Safety and Health Act of 1970)"
        ),
    ),
    # ADEA — Age discrimination
    (
        re.compile(r"\bADEA\b|age discrimination|40 years.{0,20}old|older worker", re.I),
        "29 U.S.C. § 623",
        "https://www.law.cornell.edu/uscode/text/29/623",
        "Age Discrimination in Employment Act — Prohibited Practices",
        (
            "It shall be unlawful for an employer to fail or refuse to hire or to discharge any individual or "
            "otherwise discriminate against any individual with respect to his compensation, terms, conditions, or "
            "privileges of employment, because of such individual's age. It shall be unlawful for an employer to "
            "limit, segregate, or classify his employees in any way which would deprive or tend to deprive any "
            "individual of employment opportunities or otherwise adversely affect his status as an employee, because "
            "of such individual's age. The ADEA protects individuals who are at least 40 years of age. "
            "(29 U.S.C. § 623, Age Discrimination in Employment Act of 1967)"
        ),
    ),
    # Fair Housing Act
    (
        re.compile(r"fair housing|housing discriminat|refuse to (sell|rent)|landlord.{0,30}discriminat", re.I),
        "42 U.S.C. § 3604",
        "https://www.law.cornell.edu/uscode/text/42/3604",
        "Fair Housing Act — Prohibited Discrimination",
        (
            "It shall be unlawful to refuse to sell or rent after the making of a bona fide offer, or to refuse to "
            "negotiate for the sale or rental of, or otherwise make unavailable or deny, a dwelling to any person "
            "because of race, color, religion, sex, familial status, or national origin. It shall be unlawful to "
            "discriminate against any person in the terms, conditions, or privileges of sale or rental of a dwelling, "
            "or in the provision of services or facilities in connection therewith, because of race, color, religion, "
            "sex, familial status, or national origin. (42 U.S.C. § 3604, Fair Housing Act of 1968)"
        ),
    ),
    # Title IX — education
    (
        re.compile(r"title ix|education.{0,20}discriminat|school.{0,20}discriminat|sex.{0,20}education", re.I),
        "20 U.S.C. § 1681",
        "https://www.law.cornell.edu/uscode/text/20/1681",
        "Title IX — Sex Discrimination in Education",
        (
            "No person in the United States shall, on the basis of sex, be excluded from participation in, be denied "
            "the benefits of, or be subjected to discrimination under any education program or activity receiving "
            "Federal financial assistance. (20 U.S.C. § 1681, Title IX of the Education Amendments of 1972)"
        ),
    ),
    # NLRA — labor unions
    (
        re.compile(r"\bNLRA\b|labor union|collective bargaining|right to organize|unfair labor practice", re.I),
        "29 U.S.C. § 157",
        "https://www.law.cornell.edu/uscode/text/29/157",
        "National Labor Relations Act — Rights of Employees",
        (
            "Employees shall have the right to self-organization, to form, join, or assist labor organizations, "
            "to bargain collectively through representatives of their own choosing, and to engage in other concerted "
            "activities for the purpose of collective bargaining or other mutual aid or protection, and shall also "
            "have the right to refrain from any or all of such activities. (29 U.S.C. § 157, National Labor "
            "Relations Act)"
        ),
    ),
    # § 1983 civil rights enforcement — First/Fourth Amendment violations
    (
        re.compile(r"first amendment|free speech|freedom of speech|freedom of religion|freedom of press|fourth amendment|unreasonable search|search and seizure|police search|civil rights violation|constitutional right", re.I),
        "42 U.S.C. § 1983",
        "https://www.law.cornell.edu/uscode/text/42/1983",
        "Civil Rights Act — Civil Action for Deprivation of Rights (§ 1983)",
        (
            "Every person who, under color of any statute, ordinance, regulation, custom, or usage, of any State or "
            "Territory or the District of Columbia, subjects, or causes to be subjected, any citizen of the United "
            "States or other person within the jurisdiction thereof to the deprivation of any rights, privileges, or "
            "immunities secured by the Constitution and laws, shall be liable to the party injured in an action at "
            "law, suit in equity, or other proper proceeding for redress. (42 U.S.C. § 1983)"
        ),
    ),
    # IRS — Tax record retention and statute of limitations on assessment
    (
        re.compile(r"keep.{0,20}tax records|tax records.{0,20}keep|how long.{0,30}tax|irs.{0,20}records|record.{0,20}keeping.{0,20}tax|income tax.{0,20}records|tax.{0,20}retention|audit.{0,20}period|irs.{0,20}audit|how long.{0,30}irs|tax document|how long.{0,30}keep.{0,30}return", re.I),
        "26 U.S.C. §§ 6001, 6501",
        "https://www.law.cornell.edu/uscode/text/26/6501",
        "Internal Revenue Code — Tax Record Retention and IRS Audit Periods",
        (
            "Under 26 U.S.C. § 6001, every person liable for any tax must keep such records as the IRS prescribes "
            "by regulation — sufficient to establish the amount of gross income, deductions, credits, and other "
            "matters required on a tax return. Under 26 U.S.C. § 6501, the IRS generally has 3 years from the date "
            "a return is filed to assess additional tax (the standard audit window). Key exceptions: (1) The period "
            "extends to 6 years if you omit from gross income an amount exceeding 25% of the gross income stated on "
            "the return. (2) There is no time limit if you file a fraudulent return or fail to file a return at all. "
            "Practical retention periods: Keep tax returns and all supporting records (W-2s, 1099s, receipts, "
            "statements) for at least 3 years from the filing date or 2 years from the date you paid the tax, "
            "whichever is later. Keep records for 6 years if you may have underreported income by more than 25%. "
            "Keep records relating to property (cost basis, improvements) until the limitation period expires for "
            "the year you dispose of it. Employment tax records must be kept for at least 4 years after the tax "
            "is due or paid. (26 U.S.C. §§ 6001, 6501; IRS Publication 552)"
        ),
    ),
    # IRS — Federal income tax filing requirements and estimated taxes
    (
        re.compile(r"income tax return|file.{0,15}federal tax|who must file|filing requirement|irs.{0,15}file|federal income tax|estimated tax|quarterly tax|self.{0,10}employ.{0,20}tax|1040|form w.?2|form 1099", re.I),
        "26 U.S.C. § 6012",
        "https://www.law.cornell.edu/uscode/text/26/6012",
        "Internal Revenue Code — Federal Income Tax Filing Requirements",
        (
            "Under 26 U.S.C. § 6012, every individual with gross income at or above the applicable threshold for "
            "their filing status must file a federal income tax return. Self-employed individuals must file if net "
            "self-employment earnings are $400 or more, regardless of other income. Estimated quarterly tax "
            "payments (Form 1040-ES) are required under 26 U.S.C. § 6654 when you expect to owe at least $1,000 "
            "in federal tax and your withholding will cover less than the smaller of 90% of the current year's tax "
            "liability or 100% of the prior year's tax liability. Estimated tax due dates are April 15, June 15, "
            "September 15, and January 15 of the following year. Employees receive Form W-2; independent "
            "contractors and other payers receive Form 1099-NEC or 1099-MISC. (26 U.S.C. §§ 6012, 6654)"
        ),
    ),
    # IRS — Penalties for failure to file or pay taxes
    (
        re.compile(r"irs penalty|tax penalty|failure to.{0,10}pay.{0,15}tax|failure to.{0,10}file.{0,15}tax|late.{0,15}tax|underpayment.{0,15}tax|irs.{0,15}fine|tax.{0,15}late fee|penalty.{0,20}irs", re.I),
        "26 U.S.C. § 6651",
        "https://www.law.cornell.edu/uscode/text/26/6651",
        "Internal Revenue Code — Penalties for Failure to File or Pay",
        (
            "Under 26 U.S.C. § 6651, the IRS imposes two main civil penalties: (1) Failure to file on time: 5% of "
            "the unpaid tax for each month or partial month the return is late, up to a maximum of 25% of unpaid "
            "tax. (2) Failure to pay on time: 0.5% of unpaid tax for each month or partial month the balance "
            "remains unpaid after the due date, up to a maximum of 25%. If both penalties apply in the same month, "
            "the failure-to-file penalty is reduced by the amount of the failure-to-pay penalty. The combined "
            "maximum penalty can reach 47.5% (22.5% for late filing + 25% for late payment). A taxpayer who can "
            "demonstrate reasonable cause and absence of willful neglect may qualify for penalty abatement. "
            "First-time penalty abatement is also available administratively for taxpayers with a clean compliance "
            "history. (26 U.S.C. § 6651)"
        ),
    ),
]


def _fetch_lii_section(url: str, query: str, max_chars: int = 1000) -> str:
    """Fetch a Cornell LII US Code page and extract the most relevant text."""
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True,
                          headers={"User-Agent": "LegalSearchHub/1.0"}) as client:
            r = client.get(url)
            r.raise_for_status()
    except Exception as exc:
        logger.warning("LII fetch failed for %s: %s", url, exc)
        return ""

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", r.text)
    text = re.sub(r"\s+", " ", text).strip()

    # Find the most relevant passage by keyword overlap
    query_words = set(re.findall(r"\w+", query.lower())) - {
        "the", "a", "an", "of", "in", "is", "what", "are", "under", "my", "rights", "how",
    }
    best_idx = 0
    best_score = -1
    window = 800
    for i in range(0, max(1, len(text) - window), 100):
        chunk = text[i: i + window].lower()
        score = sum(1 for w in query_words if w in chunk)
        if score > best_score:
            best_score = score
            best_idx = i

    # Always anchor on the first statutory provision marker if found
    for marker in ("it shall be unlawful", "it shall be an unlawful", "no person shall",
                   "every employer shall", "an employer shall", "it is unlawful"):
        marker_idx = text.lower().find(marker)
        if marker_idx != -1:
            best_idx = marker_idx
            break

    return text[best_idx: best_idx + max_chars].strip()


def fetch_uscode(query: str, max_results: int = 3) -> List[LiveResult]:
    """Fetch US Code statute text for common federal statutes by keyword matching.

    Tries to fetch live text from Cornell LII; falls back to embedded statutory
    text when the live fetch is unavailable. Covers Civil Rights Act (Title VII,
    II, VI), ADA, FMLA, FLSA, OSHA, ADEA, Fair Housing Act, Title IX, NLRA, § 1983.
    No API key required.
    """
    results: List[LiveResult] = []
    seen_urls: set = set()

    for pattern, citation, url, title_label, fallback_text in _STATUTE_MAP:
        if len(results) >= max_results:
            break
        if not pattern.search(query):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Try live fetch first; use embedded fallback text if blocked or unavailable
        excerpt = _fetch_lii_section(url, query)
        if not excerpt:
            logger.warning("LII fetch unavailable for %s — using embedded statute text", citation)
            excerpt = fallback_text

        results.append(
            LiveResult(
                text=f"{title_label}\n\n{excerpt}",
                title=title_label,
                url=url,
                citation=citation,
                authority="United States Code — Cornell Legal Information Institute (LII)",
                source="uscode",
            )
        )

    logger.warning("US Code returned %d result(s) for query: %r", len(results), query)
    return results


def fetch_courtlistener_federal(query: str, max_results: int = 3) -> List[LiveResult]:
    """Search CourtListener for US federal court opinions (SCOTUS, Circuit, District).

    Covers Supreme Court and all federal appellate/district courts — no API key needed.
    Adds federal case law to complement eCFR and Federal Register sources.
    """
    _STOPWORDS = r"\b(what|are|the|is|a|an|of|in|for|how|does|do|under|have|has|been|that|this|those|these|regarding|about|related|rules|rule|i|can|my|your|their|its|will|would|should|could|when|where|which)\b"
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


# ---------------------------------------------------------------------------
# State statute static content — official sources for common state law topics.
# Keyed by (state_lower, topic_pattern). No API key or network call required.
# ---------------------------------------------------------------------------
_STATE_TOPIC_MAP: List[tuple] = [
    # LLC formation
    (
        re.compile(r"\bLLC\b|limited liability company|articles of organization|form an? LLC|start.{0,20}LLC|register.{0,20}LLC", re.I),
        {
            "texas": (
                "To form an LLC in Texas: (1) Choose a name that includes 'Limited Liability Company', 'LLC', or 'L.L.C.' and is distinguishable from existing Texas entities. "
                "(2) Appoint a registered agent with a Texas street address. "
                "(3) File a Certificate of Formation (Form 205) with the Texas Secretary of State online or by mail. Filing fee: $300. "
                "(4) Create an operating agreement (not filed with the state, but recommended). "
                "(5) Obtain an EIN from the IRS. "
                "Authority: Texas Business Organizations Code, Chapter 101 (Tex. Bus. Orgs. Code § 101.001 et seq.).",
                "Tex. Bus. Orgs. Code § 101",
                "https://www.sos.state.tx.us/corp/forms_boc.shtml",
                "Texas LLC Formation — Texas Secretary of State",
            ),
            "california": (
                "To form an LLC in California: (1) Choose a name with 'Limited Liability Company' or 'LLC'. "
                "(2) File Articles of Organization (Form LLC-1) with the California Secretary of State. Filing fee: $70. "
                "(3) Appoint a registered agent. (4) File an Initial Statement of Information (Form LLC-12) within 90 days. Fee: $20. "
                "(5) Pay the annual $800 minimum franchise tax to the California Franchise Tax Board. "
                "Authority: California Corporations Code § 17701.01 et seq.",
                "Cal. Corp. Code § 17701",
                "https://bizfileonline.sos.ca.gov",
                "California LLC Formation — California Secretary of State",
            ),
            "florida": (
                "To form an LLC in Florida: (1) Choose a name with 'Limited Liability Company', 'LLC', or 'L.L.C.' "
                "(2) File Articles of Organization (Form DLLC-1) with the Florida Division of Corporations. Online filing fee: $100 + $25 registered agent designation fee. "
                "(3) Designate a registered agent in Florida. (4) File an Annual Report each year (fee: $138.75). "
                "Authority: Florida Statutes Chapter 605 (Florida Revised LLC Act).",
                "Fla. Stat. § 605",
                "https://dos.myflorida.com/sunbiz/start-business/efile/fl-llc/",
                "Florida LLC Formation — Florida Division of Corporations",
            ),
            "new york": (
                "To form an LLC in New York: (1) Choose a name with 'Limited Liability Company', 'LLC', or 'L.L.C.' "
                "(2) File Articles of Organization with the New York Department of State. Filing fee: $200. "
                "(3) Designate a registered agent. "
                "(4) Publish a notice of formation in two newspapers for 6 consecutive weeks in the county of the LLC's principal office (publication requirement). "
                "(5) File a Certificate of Publication with the Department of State ($50). "
                "Authority: New York Limited Liability Company Law (NY LLC Law § 101 et seq.).",
                "NY LLC Law § 101",
                "https://www.dos.ny.gov/corps/llcguide.html",
                "New York LLC Formation — NY Department of State",
            ),
        },
        "LLC Formation",
        "https://www.sos.state.{state}.gov",
    ),
    # Corporation formation
    (
        re.compile(r"\bcorporation\b|\bcorp\b|incorporate|articles of incorporation|form an? (corp|company|business)|start.{0,20}(corp|company|business)|register.{0,20}(corp|company|business)", re.I),
        {
            "texas": (
                "To form a corporation (for-profit) in Texas: (1) Choose a name that includes 'Corporation', 'Incorporated', 'Company', 'Corp.', 'Inc.', or 'Co.' and is distinguishable from existing Texas entities. "
                "(2) Appoint a registered agent with a physical Texas street address. "
                "(3) File a Certificate of Formation (Form 201) with the Texas Secretary of State online or by mail. Filing fee: $300. "
                "(4) Adopt bylaws (not filed with the state, but required internally). "
                "(5) Issue shares to initial shareholders and hold an organizational meeting. "
                "(6) Obtain an EIN from the IRS. "
                "Authority: Texas Business Organizations Code, Chapter 21 (Tex. Bus. Orgs. Code § 21.001 et seq.).",
                "Tex. Bus. Orgs. Code § 21",
                "https://www.sos.state.tx.us/corp/forms_boc.shtml",
                "Texas Corporation Formation — Texas Secretary of State",
            ),
            "california": (
                "To form a corporation in California: (1) Choose a corporate name. "
                "(2) File Articles of Incorporation with the California Secretary of State. Filing fee: $100. "
                "(3) Appoint a registered agent in California. "
                "(4) Adopt bylaws and hold an organizational meeting. "
                "(5) Issue shares and obtain an EIN. "
                "(6) File an Initial Statement of Information (Form SI-550) within 90 days. Fee: $25. "
                "(7) Pay the annual minimum $800 franchise tax to the California Franchise Tax Board. "
                "Authority: California Corporations Code § 100 et seq.",
                "Cal. Corp. Code § 100",
                "https://bizfileonline.sos.ca.gov",
                "California Corporation Formation — California Secretary of State",
            ),
            "florida": (
                "To form a corporation in Florida: (1) Choose a name with 'Corporation', 'Incorporated', 'Corp.', or 'Inc.' "
                "(2) File Articles of Incorporation with the Florida Division of Corporations. Filing fee: $70 + $35 registered agent designation fee. "
                "(3) Designate a registered agent. (4) Adopt bylaws. (5) Issue stock and hold organizational meeting. "
                "(6) File an Annual Report each year (fee: $138.75). "
                "Authority: Florida Statutes Chapter 607 (Florida Business Corporation Act).",
                "Fla. Stat. § 607",
                "https://dos.myflorida.com/sunbiz/start-business/efile/fl-profit-corporation/",
                "Florida Corporation Formation — Florida Division of Corporations",
            ),
            "new york": (
                "To form a corporation in New York: (1) Choose a corporate name. "
                "(2) File a Certificate of Incorporation with the New York Department of State. Filing fee: $125. "
                "(3) Designate a registered agent. (4) Adopt bylaws and hold organizational meeting. "
                "(5) Issue stock and obtain an EIN. "
                "(6) File a Biennial Statement every two years ($9 fee). "
                "Authority: New York Business Corporation Law (NY BCL § 101 et seq.).",
                "NY Bus. Corp. Law § 101",
                "https://www.dos.ny.gov/corps/bus_entity_search.html",
                "New York Corporation Formation — NY Department of State",
            ),
        },
        "Corporation Formation",
        "https://www.sos.state.{state}.gov",
    ),
    # Landlord-tenant
    (
        re.compile(r"landlord|tenant|lease|eviction|security deposit|rent.{0,20}(increase|raise|hike)|habitability", re.I),
        {
            "texas": (
                "Texas Landlord-Tenant Law (Texas Property Code, Chapter 92): "
                "Landlords must make repairs necessary to keep the premises in a habitable condition. "
                "Security deposits must be returned within 30 days of lease termination with an itemized statement of deductions. "
                "Tenants may terminate a lease and recover costs if the landlord fails to make repairs after written notice. "
                "Tenants may also repair and deduct the cost from rent (limited to one month's rent) after proper notice. "
                "For eviction due to non-payment of rent, the landlord must give 3 days written notice before filing suit in Justice of the Peace Court.",
                "Tex. Prop. Code § 92",
                "https://statutes.capitol.texas.gov/Docs/PR/htm/PR.92.htm",
                "Texas Landlord-Tenant — Texas Property Code § 92",
            ),
            "california": (
                "California Landlord-Tenant Law (California Civil Code § 1940 et seq.): "
                "Security deposits are limited to 1 month's rent for unfurnished units and 2 months for furnished units. "
                "Landlords must return deposits within 21 days with an itemized statement. "
                "Landlords must maintain the rental in a habitable condition. "
                "Most tenancies over 12 months require just cause for eviction under AB 1482. "
                "Rent increases in rent-controlled cities require advance written notice.",
                "Cal. Civ. Code § 1940",
                "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1940.&lawCode=CIV",
                "California Landlord-Tenant — California Civil Code",
            ),
            "florida": (
                "Florida Landlord-Tenant Law (Florida Statutes Chapter 83 — Florida Residential Landlord and Tenant Act): "
                "Security deposits must be returned within 15 days (no deductions) or 30 days (with written deductions notice). "
                "Landlords must give 12 hours advance notice before entering the unit except in emergencies. "
                "For non-payment of rent, landlords must give a 3-day written notice before filing for eviction. "
                "Florida has no statewide rent control law.",
                "Fla. Stat. § 83",
                "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0083/0083.htm",
                "Florida Landlord-Tenant — Fla. Stat. Chapter 83",
            ),
        },
        "Landlord-Tenant Law",
        "https://statutes.capitol.{state}.gov",
    ),
    # Workers comp
    (
        re.compile(r"workers.{0,10}comp|workplace injury|injured at work|work.{0,15}accident", re.I),
        {
            "texas": (
                "Texas Workers' Compensation: Texas is the only state that does not require most private employers to carry workers' compensation insurance (Texas Labor Code § 406.002). "
                "Employers who opt out are called 'non-subscribers.' If your employer carries workers' comp, you may be entitled to income benefits (75% of average weekly wage), "
                "medical benefits, and death benefits. File a claim with the Texas Department of Insurance, Division of Workers' Compensation within 1 year of injury. "
                "Authority: Texas Labor Code, Chapter 406–408.",
                "Tex. Labor Code § 406",
                "https://www.tdi.texas.gov/wc/employee/index.html",
                "Texas Workers' Compensation — Texas Dept. of Insurance",
            ),
        },
        "Workers' Compensation",
        "",
    ),
]


def fetch_state_statutes(question: str, state: str) -> List[LiveResult]:
    """Return static official-source content for common state law topics.

    Uses pre-authored authoritative content drawn from state statutes and
    official government websites. No API key or network call required.
    Covers LLC formation, landlord-tenant, workers' comp for major states.
    """
    state_lower = state.lower()
    results: List[LiveResult] = []

    for pattern, state_map, topic_label, _default_url in _STATE_TOPIC_MAP:
        if not pattern.search(question):
            continue
        entry = state_map.get(state_lower)
        if not entry:
            continue
        text, citation, url, title = entry
        results.append(
            LiveResult(
                text=text,
                title=title,
                url=url,
                citation=citation,
                authority=f"{state} Official State Law — {topic_label}",
                source="state_statute",
            )
        )

    logger.warning("State statutes returned %d result(s) for %r / query: %r", len(results), state, question)
    return results


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
        r"could|when|where|which|say|says|said|tell|me|us)\b",
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

    with ThreadPoolExecutor(max_workers=6) as executor:
        if is_state:
            futures = {
                executor.submit(fetch_ecfr, query, 3): "ecfr",
                executor.submit(fetch_federal_register, query, 2): "fr",
                executor.submit(fetch_courtlistener, question, jurisdiction, 3): "courtlistener",
                executor.submit(fetch_uscode, question, 2): "uscode",
                executor.submit(fetch_state_statutes, question, jurisdiction): "state_statute",
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
