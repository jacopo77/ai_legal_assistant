from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    country: Optional[str] = Field(default=None, description="ISO country name or code")


class ChatChunk(BaseModel):
    text: str
    done: bool = False


class IngestRequest(BaseModel):
    country: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    title: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class N8nPayload(BaseModel):
    # Flexible shape; map common fields
    country: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    source: Optional[str] = "n8n"
    metadata: Dict[str, Any] = Field(default_factory=dict)

