from __future__ import annotations

from typing import Iterable, List
from openai import OpenAI
from ..core.settings import get_settings


def _get_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to backend/.env.")
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: Iterable[str]) -> List[List[float]]:
    """
    Returns embeddings for a sequence of texts.
    """
    settings = get_settings()
    client = _get_client()
    texts_list = list(texts)
    if not texts_list:
        return []
    resp = client.embeddings.create(
        model=settings.openai_embeddings_model,
        input=texts_list,
    )
    return [d.embedding for d in resp.data]

