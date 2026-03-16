#!/usr/bin/env python3
"""
End-to-end test script for AI Legal Assistant.

Usage:
  python scripts/test_stack.py <backend_url> [n8n_webhook_url]

Examples:
  python scripts/test_stack.py https://ailegalassistant-production-fe76.up.railway.app
  python scripts/test_stack.py https://ailegalassistant-production-fe76.up.railway.app https://jacopo7-u35110.vm.elestio.app/webhook-test/622b4b61-57c8-413c-97cf-227048bfef19
"""

import sys
import json
import requests
from typing import Optional

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
RESET  = '\033[0m'

def ok(msg):  print(f"{GREEN}[OK]{RESET}   {msg}")
def err(msg): print(f"{RED}[ERR]{RESET}  {msg}")
def info(msg):print(f"{BLUE}[..]{RESET}   {msg}")
def warn(msg):print(f"{YELLOW}[WARN]{RESET} {msg}")

# ---------------------------------------------------------------------------
# Baseline checks
# ---------------------------------------------------------------------------

def test_health_check(base_url: str) -> bool:
    info(f"GET {base_url}/healthz")
    try:
        r = requests.get(f"{base_url}/healthz", timeout=10)
        if r.status_code == 200 and r.json().get("status") == "ok":
            ok("Health check passed")
            return True
        err(f"Health check failed: {r.status_code} {r.text[:120]}")
        return False
    except requests.RequestException as e:
        err(f"Health check error: {e}")
        return False


def test_database_connection(base_url: str) -> bool:
    info(f"GET {base_url}/api/health/db")
    try:
        r = requests.get(f"{base_url}/api/health/db", timeout=10)
        if r.status_code == 200:
            data = r.json()
            backend = (data.get("active_backend")
                       or data.get("backend")
                       or data.get("database")
                       or "")
            ok(f"DB connected — active backend: {backend}")
            supabase = (data.get("checks") or {}).get("supabase_rest", {})
            if supabase.get("status") == "connected":
                ok(f"  Supabase REST reachable ({supabase.get('latency_ms')}ms)")
            return True
        err(f"DB check failed: {r.status_code} {r.text[:120]}")
        return False
    except requests.RequestException as e:
        err(f"DB check error: {e}")
        return False


# ---------------------------------------------------------------------------
# n8n ingest — direct to Railway /api/webhooks/n8n
# ---------------------------------------------------------------------------

_TEST_N8N_PAYLOAD = {
    "text": (
        "Title: Procurement Test Notice\n\n"
        "Document type: Rule\n\n"
        "Abstract: This test document covers Federal Acquisition Regulation (FAR) "
        "applicability for public contracts. Under 41 U.S.C. § 1101 the FAR governs "
        "how executive agencies acquire supplies and services. The contracting officer "
        "must follow FAR Part 15 for negotiated acquisitions above the simplified "
        "acquisition threshold.\n\n"
        "Publication date: 2026-03-15\n\n"
        "Official URL: https://www.federalregister.gov/documents/test/cursor-ingest-test"
    ),
    "title":              "Cursor Ingest Test — FAR Procurement Notice",
    "url":                "https://www.federalregister.gov/documents/test/cursor-ingest-test",
    "country":            "US",
    "source":             "federal_register_api",
    "authority":          "National Archives and Records Administration",
    "source_type":        "api",
    "document_type":      "rulemaking_notice",
    "collection":         "Federal Register",
    "citation":           None,
    "citation_prefix":    "Fed. Reg.",
    "publication_date":   "2026-03-15",
    "source_registry_id": "federal_register_procurement_search",
    "raw_source_url":     "https://www.federalregister.gov/developers/documentation/api/v1",
    "official_url":       "https://www.federalregister.gov/documents/test/cursor-ingest-test",
    "official_title":     "Cursor Ingest Test — FAR Procurement Notice",
    "jurisdiction":       "US",
    "metadata": {
        "official":            True,
        "source_registry_id":  "federal_register_procurement_search",
        "authority":           "National Archives and Records Administration",
        "collection":          "Federal Register",
        "document_type":       "rulemaking_notice",
        "citation":            None,
        "citation_prefix":     "Fed. Reg.",
        "publication_date":    "2026-03-15",
        "official_url":        "https://www.federalregister.gov/documents/test/cursor-ingest-test",
        "official_title":      "Cursor Ingest Test — FAR Procurement Notice",
        "jurisdiction":        "US",
        "raw_source_url":      "https://www.federalregister.gov/developers/documentation/api/v1",
    },
}


def test_n8n_ingest_direct(base_url: str) -> bool:
    """POST a fully-shaped n8n payload directly to Railway /api/webhooks/n8n."""
    url = f"{base_url}/api/webhooks/n8n"
    info(f"POST {url}")
    info("  Sending test Federal Register payload with all required provenance fields...")
    try:
        r = requests.post(url, json=_TEST_N8N_PAYLOAD, timeout=60)
        if r.status_code == 200:
            data = r.json()
            doc_id = data.get("document_id")
            ok(f"n8n ingest accepted — document_id={doc_id}")
            return True
        err(f"n8n ingest failed: {r.status_code}")
        try:
            err(f"  detail: {r.json().get('detail', r.text[:200])}")
        except Exception:
            err(f"  body: {r.text[:200]}")
        return False
    except requests.RequestException as e:
        err(f"n8n ingest error: {e}")
        return False


# ---------------------------------------------------------------------------
# n8n trigger — fire the n8n webhook so n8n runs its workflow
# ---------------------------------------------------------------------------

def test_n8n_trigger(n8n_url: str) -> bool:
    """POST a simple probe payload to the n8n webhook URL and confirm it responds."""
    info(f"POST {n8n_url}")
    info("  Triggering n8n workflow (webhook must be in Listen mode)...")
    probe = {"source": "cursor_test", "message": "ping from test_stack.py"}
    try:
        r = requests.post(n8n_url, json=probe, timeout=30)
        if r.status_code in (200, 201):
            ok(f"n8n responded {r.status_code}")
            try:
                info(f"  n8n response: {json.dumps(r.json(), indent=2)[:400]}")
            except Exception:
                info(f"  n8n response text: {r.text[:200]}")
            return True
        warn(f"n8n returned {r.status_code} — check Listen mode is active")
        info(f"  body: {r.text[:200]}")
        return False
    except requests.RequestException as e:
        err(f"n8n trigger error: {e}")
        return False


# ---------------------------------------------------------------------------
# Chat / retrieval quality
# ---------------------------------------------------------------------------

_PROCUREMENT_QUESTIONS = [
    ("What is the simplified acquisition threshold under the FAR?",  "US"),
    ("Which statute authorizes the Federal Acquisition Regulation?", "US"),
    ("What does 41 U.S.C. govern?",                                  "US"),
]


def test_chat_stream(base_url: str,
                     question: str = "What makes a contract valid?",
                     country: str = "US") -> bool:
    info(f"POST {base_url}/api/chat/stream")
    info(f"  Q: {question!r}  (country={country})")
    try:
        r = requests.post(
            f"{base_url}/api/chat/stream",
            json={"question": question, "country": country},
            stream=True,
            timeout=30,
        )
        if r.status_code != 200:
            err(f"Chat request failed: {r.status_code} {r.text[:120]}")
            return False
        full = ""
        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                full += chunk
        if not full:
            err("Empty response from chat endpoint")
            return False
        ok("Chat streaming successful")
        info(f"  Preview: {full[:240]}")
        if any(f"[{n}]" in full for n in range(1, 6)):
            ok("Inline citations found in response")
        else:
            warn("No inline citations — corpus may be empty or question out of scope")
        return True
    except requests.RequestException as e:
        err(f"Chat error: {e}")
        return False


def test_retrieval_procurement(base_url: str) -> bool:
    """Ask three procurement-scoped questions and check for citations."""
    info("Retrieval quality test — procurement corpus")
    any_cited = False
    all_ok = True
    for q, country in _PROCUREMENT_QUESTIONS:
        print()
        info(f"  Q: {q}")
        try:
            r = requests.post(
                f"{base_url}/api/chat/stream",
                json={"question": q, "country": country},
                stream=True,
                timeout=30,
            )
            if r.status_code != 200:
                err(f"  Stream failed: {r.status_code}")
                all_ok = False
                continue
            full = ""
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    full += chunk
            has_cite = any(f"[{n}]" in full for n in range(1, 6))
            if has_cite:
                any_cited = True
                ok(f"  Cited answer: {full[:200]}")
            else:
                warn(f"  No citations — may be a corpus gap: {full[:200]}")
        except requests.RequestException as e:
            err(f"  Error: {e}")
            all_ok = False
    if any_cited:
        ok("At least one procurement question returned a cited answer")
    else:
        warn("No procurement questions returned citations — ingest official sources first")
    return all_ok


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def test_cors(base_url: str, origin: str) -> bool:
    info(f"OPTIONS {base_url}/api/chat/stream  Origin: {origin}")
    try:
        r = requests.options(
            f"{base_url}/api/chat/stream",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
            timeout=10,
        )
        if r.status_code == 200:
            cors = r.headers.get("Access-Control-Allow-Origin", "")
            if cors == origin or cors == "*":
                ok(f"CORS configured correctly: {cors}")
                return True
            warn(f"CORS header value unexpected: {cors!r}")
            return False
        err(f"CORS preflight returned {r.status_code}")
        return False
    except requests.RequestException as e:
        err(f"CORS test error: {e}")
        return False


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests(base_url: str, n8n_url: Optional[str] = None):
    header = "=" * 64
    print(f"\n{BLUE}{header}{RESET}")
    print(f"{BLUE}  AI Legal Assistant — Test Suite{RESET}")
    print(f"{BLUE}{header}{RESET}\n")
    print(f"  Backend : {base_url}")
    if n8n_url:
        print(f"  n8n URL : {n8n_url}")
    print()

    results: dict[str, Optional[bool]] = {}

    print(f"{BLUE}[1] Backend health{RESET}")
    results["health"] = test_health_check(base_url)

    print(f"\n{BLUE}[2] Database / storage{RESET}")
    results["database"] = test_database_connection(base_url)

    print(f"\n{BLUE}[3] n8n ingest — direct to Railway{RESET}")
    results["n8n_ingest_direct"] = test_n8n_ingest_direct(base_url)

    if n8n_url:
        print(f"\n{BLUE}[4] n8n trigger — fire the n8n webhook{RESET}")
        results["n8n_trigger"] = test_n8n_trigger(n8n_url)
    else:
        print(f"\n{YELLOW}[4] n8n trigger — skipped (no n8n URL provided){RESET}")
        results["n8n_trigger"] = None

    print(f"\n{BLUE}[5] Chat — general question{RESET}")
    results["chat_general"] = test_chat_stream(base_url)

    print(f"\n{BLUE}[6] Retrieval quality — procurement corpus{RESET}")
    results["retrieval_procurement"] = test_retrieval_procurement(base_url)

    # Summary
    print(f"\n{BLUE}{header}{RESET}")
    print(f"{BLUE}  Summary{RESET}")
    print(f"{BLUE}{header}{RESET}\n")

    passed  = sum(1 for v in results.values() if v is True)
    failed  = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for name, result in results.items():
        tag = (f"{GREEN}PASS{RESET}" if result is True
               else f"{RED}FAIL{RESET}" if result is False
               else f"{YELLOW}SKIP{RESET}")
        print(f"  {name.ljust(26)}: {tag}")

    print(f"\n  Total {len(results)} | "
          f"Pass {GREEN}{passed}{RESET} | "
          f"Fail {RED}{failed}{RESET} | "
          f"Skip {YELLOW}{skipped}{RESET}")
    print(f"{BLUE}{header}{RESET}\n")

    if failed == 0 and passed > 0:
        print(f"{GREEN}All tests passed.{RESET}\n")
        return 0
    if failed > 0:
        print(f"{RED}Some tests failed — see details above.{RESET}\n")
        return 1
    print(f"{YELLOW}No tests ran successfully.{RESET}\n")
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    backend  = sys.argv[1].rstrip("/")
    n8n_hook = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else None
    sys.exit(run_all_tests(backend, n8n_hook))
