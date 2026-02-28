"""
Placeholder embeddings & retrieval helpers.
Replace with OpenAI embeddings and SQLite/pgvector-backed vector store.
"""
from typing import List, Dict, Any


def embed_texts(texts: List[str]) -> List[List[float]]:
    # TODO: call OpenAI embeddings
    return [[0.0] * 1536 for _ in texts]


def search_similar(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # TODO: perform vector search against DB
    return []

