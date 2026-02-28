from __future__ import annotations

import time
from fastapi import APIRouter
from ..core.settings import get_settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/db")
def health_db():
    """
    Diagnostic endpoint: tests all configured storage backends and reports
    which one is active (Supabase REST → Postgres → SQLite priority order).
    """
    settings = get_settings()
    result: dict = {"active_backend": None, "checks": {}}

    # --- Check 1: Supabase REST API ---
    sb_configured = bool(
        settings.supabase_url
        and settings.supabase_key
        and settings.supabase_key != "YOUR_SERVICE_ROLE_KEY_HERE"
    )
    if sb_configured:
        start = time.monotonic()
        try:
            from supabase import create_client  # type: ignore

            client = create_client(settings.supabase_url, settings.supabase_key)
            # Lightweight check — list 0 rows from documents table
            client.table("documents").select("id").limit(1).execute()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["checks"]["supabase_rest"] = {
                "status": "connected",
                "latency_ms": elapsed_ms,
                "url": settings.supabase_url,
            }
            result["active_backend"] = "supabase_rest"
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["checks"]["supabase_rest"] = {
                "status": "error",
                "latency_ms": elapsed_ms,
                "error": str(exc),
            }
    else:
        result["checks"]["supabase_rest"] = {
            "status": "not_configured",
            "note": "Set SUPABASE_URL and SUPABASE_KEY in backend/.env",
        }

    # --- Check 2: Direct Postgres ---
    if settings.db_url:
        start = time.monotonic()
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(
                settings.db_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 8},
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["checks"]["postgres_direct"] = {
                "status": "connected",
                "latency_ms": elapsed_ms,
            }
            engine.dispose()
            if not result["active_backend"]:
                result["active_backend"] = "postgres_direct"
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["checks"]["postgres_direct"] = {
                "status": "error",
                "latency_ms": elapsed_ms,
                "error": str(exc).split("\n")[0],
            }
    else:
        result["checks"]["postgres_direct"] = {"status": "not_configured"}

    # --- Check 3: SQLite fallback ---
    result["checks"]["sqlite"] = {"status": "always_available", "path": settings.db_path}
    if not result["active_backend"]:
        result["active_backend"] = "sqlite"

    return result
