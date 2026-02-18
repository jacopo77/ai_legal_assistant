from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from ..core.settings import get_settings


def _ensure_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            url TEXT,
            country TEXT,
            title TEXT,
            content TEXT,
            metadata TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
        """
    )
    conn.commit()


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    db_path = os.path.abspath(settings.db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    _ensure_db(conn)
    return conn


_CONN = _connect()


def save_document(
    *,
    source: Optional[str],
    url: Optional[str],
    country: Optional[str],
    title: Optional[str],
    content: str,
    metadata: Dict[str, Any],
) -> int:
    cur = _CONN.cursor()
    cur.execute(
        "INSERT INTO documents (source, url, country, title, content, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        (source, url, country, title, content, json.dumps(metadata or {})),
    )
    _CONN.commit()
    return int(cur.lastrowid)


def save_chunks(document_id: int, chunks: Iterable[Tuple[str, List[float]]]) -> None:
    rows = [(document_id, text, json.dumps(vec)) for text, vec in chunks]
    cur = _CONN.cursor()
    cur.executemany("INSERT INTO chunks (document_id, text, embedding) VALUES (?, ?, ?)", rows)
    _CONN.commit()


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: Optional[str]
    url: Optional[str]
    title: Optional[str]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def retrieve_similar(query_embedding: List[float], *, country: Optional[str], k: int = 6) -> List[RetrievedChunk]:
    """
    Naive retrieval: load embeddings to memory, compute cosine, filter by country if provided.
    """
    q = np.array(query_embedding, dtype=np.float32)
    cur = _CONN.cursor()
    if country:
        cur.execute(
            """
            SELECT c.text, c.embedding, d.source, d.url, d.title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.country = ?
            """,
            (country,),
        )
    else:
        cur.execute(
            """
            SELECT c.text, c.embedding, d.source, d.url, d.title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            """
        )
    rows = cur.fetchall()
    scored: List[RetrievedChunk] = []
    for text, emb_json, source, url, title in rows:
        vec = np.array(json.loads(emb_json), dtype=np.float32)
        score = _cosine_similarity(q, vec)
        scored.append(RetrievedChunk(text=text, score=score, source=source, url=url, title=title))
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:k]

