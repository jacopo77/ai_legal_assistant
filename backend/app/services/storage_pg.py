from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import cosine_distance

from ..db import Base, get_session_factory, get_engine
from ..models.db_models import Document, Chunk


def init_schema() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def save_document(
    *,
    source: Optional[str],
    url: Optional[str],
    country: Optional[str],
    title: Optional[str],
    content: str,
    metadata: Dict[str, Any],
) -> int:
    init_schema()
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        doc = Document(
            source=source,
            url=url,
            country=country,
            title=title,
            content=content,
            metadata=json.dumps(metadata or {}),
        )
        session.add(doc)
        session.commit()
        return int(doc.id)


def save_chunks(document_id: int, chunks: Iterable[tuple[str, List[float]]]) -> None:
    init_schema()
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        for text, vec in chunks:
            session.add(Chunk(document_id=document_id, text=text, embedding=vec))
        session.commit()


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: Optional[str]
    url: Optional[str]
    title: Optional[str]


def retrieve_similar(query_embedding: List[float], *, country: Optional[str], k: int = 6) -> List[RetrievedChunk]:
    init_schema()
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        q = select(
            Chunk.text,
            (1 - cosine_distance(Chunk.embedding, query_embedding)).label("score"),
            Document.source,
            Document.url,
            Document.title,
        ).join(Document, Document.id == Chunk.document_id)
        if country:
            q = q.where(Document.country == country)
        q = q.order_by(func.desc("score")).limit(k)
        rows = session.execute(q).all()
        return [
            RetrievedChunk(text=row[0], score=float(row[1]), source=row[2], url=row[3], title=row[4])  # type: ignore
            for row in rows
        ]

