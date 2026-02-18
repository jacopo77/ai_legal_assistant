from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = Field(default="Paralegal Assistant API")
    environment: str = Field(default="development")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # CORS
    allowed_origin: str = Field(default="http://localhost:3000")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    openai_embeddings_model: str = Field(default="text-embedding-3-small")

    # Data
    db_path: str = Field(default=os.path.join(os.path.dirname(__file__), "..", "data", "app.db"))
    db_url: Optional[str] = Field(default=None, description="Postgres URL; if set, pgvector is used")


def get_settings() -> Settings:
    return Settings()

