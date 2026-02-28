from __future__ import annotations

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .core.settings import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    if not settings.db_url:
        raise RuntimeError("DB_URL is not set; Postgres mode requires DB_URL")
    engine = create_engine(
        settings.db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        logger.info("✅ Connected to Supabase/Postgres successfully.")
    except Exception as exc:
        engine.dispose()
        logger.error(
            "❌ Postgres connection failed: %s\n"
            "   DB_URL starts with: %s\n"
            "   Tip: If DNS resolution fails, switch to the Supabase Connection "
            "Pooler URL (Project Settings → Database → Connection Pooling, port 6543).",
            exc,
            (settings.db_url or "")[:50],
        )
        raise
    return engine


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)

