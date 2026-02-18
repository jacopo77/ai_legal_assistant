from __future__ import annotations

from typing import Generator, Iterable
from openai import OpenAI
from ..core.settings import get_settings


def _get_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to backend/.env.")
    return OpenAI(api_key=settings.openai_api_key)


def stream_completion(system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
    """
    Streams tokens from the chat completion API as plain text chunks.
    """
    settings = get_settings()
    client = _get_client()

    stream = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        temperature=0.2,
    )

    for event in stream:
        delta = event.choices[0].delta
        if (text := getattr(delta, "content", None)):
            yield text

