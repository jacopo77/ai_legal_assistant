from __future__ import annotations

from typing import Generator, Iterable, List, Optional, Tuple

from .embeddings import embed_texts
from .llm import stream_completion
from ..core.settings import get_settings
from .storage import save_document as save_document_sqlite
from .storage import save_chunks as save_chunks_sqlite
from .storage import retrieve_similar as retrieve_similar_sqlite
from .storage import RetrievedChunk as RetrievedChunkSqlite
try:
    from .storage_pg import save_document as save_document_pg  # type: ignore
    from .storage_pg import save_chunks as save_chunks_pg  # type: ignore
    from .storage_pg import retrieve_similar as retrieve_similar_pg  # type: ignore
    from .storage_pg import RetrievedChunk as RetrievedChunkPg  # type: ignore
except Exception:
    save_document_pg = None  # type: ignore
    save_chunks_pg = None  # type: ignore
    retrieve_similar_pg = None  # type: ignore
    RetrievedChunkPg = None  # type: ignore


def _use_pg() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "db_url", None) and save_document_pg is not None)


def add_document(*, source: Optional[str], url: Optional[str], country: Optional[str], title: Optional[str], text: str, metadata: dict) -> int:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    embeddings = embed_texts(parts)
    if _use_pg():
        doc_id = save_document_pg(source=source, url=url, country=country, title=title, content=text, metadata=metadata)  # type: ignore
        save_chunks_pg(doc_id, list(zip(parts, embeddings)))  # type: ignore
        return doc_id
    else:
        doc_id = save_document_sqlite(source=source, url=url, country=country, title=title, content=text, metadata=metadata)
        save_chunks_sqlite(doc_id, list(zip(parts, embeddings)))
        return doc_id


def _build_prompt(question: str, country: Optional[str], retrieved: List[RetrievedChunk]) -> str:
    context_lines: List[str] = []
    for idx, r in enumerate(retrieved, start=1):
        cite = f"[{idx}]"
        meta = []
        if r.title:
            meta.append(r.title)
        if r.url:
            meta.append(r.url)
        meta_str = " — ".join(meta) if meta else ""
        context_lines.append(f"{cite} {r.text}\n{meta_str}")
    context = "\n\n".join(context_lines) if context_lines else "No relevant context found."
    location = f" for {country}" if country else ""
    instructions = (
        "You are a careful paralegal assistant. Answer strictly using the provided context snippets. "
        "Cite sources inline like [1], [2] where relevant. If unsure or missing, say you don't know."
    )
    return f"{instructions}\n\nQuestion{location}: {question}\n\nContext:\n{context}\n\nAnswer:"


def answer_stream(question: str, country: Optional[str]) -> Generator[str, None, None]:
    # Retrieve
    query_emb = embed_texts([question])[0]
    if _use_pg():
        retrieved = retrieve_similar_pg(query_emb, country=country, k=8)  # type: ignore
    else:
        retrieved = retrieve_similar_sqlite(query_emb, country=country, k=8)
    # Build prompt
    user_prompt = _build_prompt(question, country, retrieved)
    system_prompt = "You produce concise, legally careful answers with citations."
    # Stream LLM
    for chunk in stream_completion(system_prompt, user_prompt):
        yield chunk

