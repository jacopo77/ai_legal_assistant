from __future__ import annotations

import secrets
import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/apikeys", tags=["apikeys"])

# In-memory key store — replace with Supabase persistence for production
_api_keys: Dict[str, dict] = {}


class GenerateKeyRequest(BaseModel):
    client_name: str
    plan: str = "business"
    admin_secret: str


class ApiKeyResponse(BaseModel):
    api_key: str
    client_name: str
    plan: str
    message: str


class KeyInfoResponse(BaseModel):
    client_name: str
    plan: str
    active: bool
    request_count: int


@router.post("/generate", response_model=ApiKeyResponse)
def generate_api_key(req: GenerateKeyRequest):
    """Generate a new B2B API key. Requires admin_secret from environment."""
    from ..core.settings import get_settings
    settings = get_settings()
    admin_secret = getattr(settings, "admin_secret", None)

    if not admin_secret:
        raise HTTPException(status_code=503, detail="API key management is not configured on this server.")
    if req.admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret.")

    api_key = f"lsh_{secrets.token_urlsafe(32)}"
    _api_keys[api_key] = {
        "client_name": req.client_name,
        "plan": req.plan,
        "active": True,
        "request_count": 0,
    }
    logger.info("Generated B2B API key for client: %s (plan: %s)", req.client_name, req.plan)
    return ApiKeyResponse(
        api_key=api_key,
        client_name=req.client_name,
        plan=req.plan,
        message=f"API key generated for {req.client_name}. Add X-API-Key: <key> header to all requests.",
    )


@router.get("/validate", response_model=KeyInfoResponse)
def validate_key(x_api_key: Optional[str] = Header(default=None)):
    """Check if a B2B API key is valid. Pass key in X-Api-Key header."""
    if not x_api_key:
        raise HTTPException(status_code=400, detail="X-Api-Key header is required.")
    info = _api_keys.get(x_api_key)
    if not info or not info["active"]:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")
    return KeyInfoResponse(
        client_name=info["client_name"],
        plan=info["plan"],
        active=info["active"],
        request_count=info["request_count"],
    )


def get_api_key_info(x_api_key: Optional[str]) -> Optional[dict]:
    """Used by other routers to check for a valid B2B key and increment usage."""
    if not x_api_key:
        return None
    info = _api_keys.get(x_api_key)
    if info and info["active"]:
        info["request_count"] += 1
        return info
    return None
