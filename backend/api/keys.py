"""
API key management endpoints (Developers section).

Gated by the admin token (the owner manages keys). For multi-user hosted, each magic-link user
would manage their own keys via Supabase — same shape, deferred (NEEDS KEYS).

Plaintext key is returned ONLY on create/rotate; never again.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.admin import require_admin
from services.keystore import get_keystore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/keys", tags=["keys"])


class CreateKeyRequest(BaseModel):
    name: str = "key"
    quota: Optional[int] = None


@router.get("")
async def list_keys(admin: dict = Depends(require_admin)):
    return {"keys": [r.public() for r in get_keystore().list()]}


@router.post("")
async def create_key(body: CreateKeyRequest, admin: dict = Depends(require_admin)):
    raw, rec = get_keystore().create(body.name, body.quota)
    # `key` (plaintext) shown ONCE — the client must copy it now.
    return {"key": raw, "record": rec.public()}


@router.post("/{key_id}/rotate")
async def rotate_key(key_id: str, admin: dict = Depends(require_admin)):
    raw = get_keystore().rotate(key_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="key not found")
    rec = get_keystore().get(key_id)
    return {"key": raw, "record": rec.public() if rec else None}


@router.delete("/{key_id}")
async def revoke_key(key_id: str, admin: dict = Depends(require_admin)):
    if not get_keystore().revoke(key_id):
        raise HTTPException(status_code=404, detail="key not found")
    return {"ok": True, "revoked": key_id}
