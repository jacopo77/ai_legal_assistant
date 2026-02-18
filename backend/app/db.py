from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .core.settings import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    if not settings.db_url:
        raise RuntimeError("DB_URL is not set; Postgres mode requires DB_URL")
    engine = create_engine(settings.db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        # Ensure pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    return engine


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)

