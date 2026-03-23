"""
generate_faqs.py — Populate frontend/data/faqs.json with answers from the backend.

Usage:
    python scripts/generate_faqs.py

Requirements:
    pip install httpx

The script reads the questions from frontend/data/faqs.json, calls the Railway
backend for each one, parses the streamed response (including the SOURCES_DATA
marker), and writes the answers back to the same file.

Set BACKEND_URL below to your Railway URL before running.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

# ── Configuration ──────────────────────────────────────────────────────────────
BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "https://ailegalassistant-production-fe76.up.railway.app",
)
FAQS_FILE = Path(__file__).parent.parent / "frontend" / "data" / "faqs.json"
DELAY_BETWEEN_REQUESTS = 3  # seconds — be polite to the backend
TIMEOUT = 120  # seconds per question
# ───────────────────────────────────────────────────────────────────────────────


def call_backend(question: str, jurisdiction: str) -> tuple[str, list]:
    """Stream an answer from the backend. Returns (answer_text, sources_list)."""
    url = f"{BACKEND_URL}/api/chat/stream"
    payload = {"question": question, "country": jurisdiction}

    full = ""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                for chunk in r.iter_text():
                    full += chunk
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return "", []

    # Split off the SOURCES_DATA marker appended by rag.py
    sources: list = []
    marker = "\n\nSOURCES_DATA:"
    if marker in full:
        text_part, sources_part = full.split(marker, 1)
        try:
            sources = json.loads(sources_part.strip())
        except json.JSONDecodeError:
            pass
        full = text_part.strip()
    else:
        full = full.strip()

    return full, sources


def main() -> None:
    if not FAQS_FILE.exists():
        print(f"ERROR: {FAQS_FILE} not found.")
        sys.exit(1)

    with open(FAQS_FILE, encoding="utf-8") as f:
        faqs = json.load(f)

    total = len(faqs)
    updated = 0
    skipped = 0

    for i, faq in enumerate(faqs, start=1):
        slug = faq.get("slug", "")
        question = faq.get("question", "")
        jurisdiction = faq.get("jurisdiction", "US")

        # Skip questions that already have an answer
        if faq.get("answer", "").strip():
            print(f"[{i}/{total}] SKIP (already answered): {slug}")
            skipped += 1
            continue

        print(f"[{i}/{total}] Asking: {question[:70]}...")
        answer, sources = call_backend(question, jurisdiction)

        if answer:
            faq["answer"] = answer
            faq["sources"] = sources
            updated += 1
            print(f"    OK — {len(answer)} chars, {len(sources)} source(s)")
        else:
            print(f"    FAILED — no answer received, leaving blank")

        # Save after every question so progress is not lost on interruption
        with open(FAQS_FILE, "w", encoding="utf-8") as f:
            json.dump(faqs, f, indent=2, ensure_ascii=False)

        if i < total:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"\nDone. {updated} answered, {skipped} skipped, {total - updated - skipped} failed.")
    print(f"Results saved to {FAQS_FILE}")


if __name__ == "__main__":
    main()
