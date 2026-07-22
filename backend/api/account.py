"""Signed-in account API: user-owned API keys and usage."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_user
from api.v1 import QueryRequest
from services.accounts import VALID_MODES, get_account_store
from services.playground import execute_playground_query

router = APIRouter(prefix="/api/account", tags=["account"])


class CreateAccountKeyRequest(BaseModel):
    name: str = "key"
    scopes: List[str] = VALID_MODES


class CompleteOnboardingRequest(BaseModel):
    name: str = Field(default="", max_length=120)
    picture: str = Field(default="", max_length=500)
    heard_about: str = Field(default="", max_length=120)
    use_cases: List[str] = Field(default_factory=list)




@router.post("/onboarding")
async def complete_onboarding(body: CompleteOnboardingRequest, user=Depends(require_user)):
    store = get_account_store()
    cleaned_cases = [str(x).strip() for x in body.use_cases if str(x).strip()]
    try:
        updated = store.update_onboarding(
            user.id,
            body.name,
            body.picture,
            body.heard_about,
            cleaned_cases,
        )
    except RuntimeError as exc:
        message = str(exc)
        onboarding_columns = ("heard_about", "use_cases", "onboarding_completed", "onboarded_at")
        if any(column in message for column in onboarding_columns):
            raise HTTPException(
                status_code=503,
                detail="Onboarding database migration is missing. Run backend/migrations/002_account_onboarding.sql",
            ) from exc
        raise HTTPException(status_code=502, detail="could not save onboarding") from exc
    if not updated:
        raise HTTPException(status_code=404, detail="user not found")
    return {"user": updated.public()}


@router.post("/playground/query")
async def playground_query(body: QueryRequest, user=Depends(require_user)):
    return await execute_playground_query(body, tier="signedin", user=user)


@router.get("/keys")
async def list_keys(user=Depends(require_user)):
    return {"keys": [k.public() for k in get_account_store().list_keys(user.id)]}


@router.post("/keys")
async def create_key(body: CreateAccountKeyRequest, user=Depends(require_user)):
    raw, rec = get_account_store().create_key(user.id, body.name, body.scopes)
    return {"key": raw, "record": rec.public()}


@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str, user=Depends(require_user)):
    store = get_account_store()
    if key_id not in {k.id for k in store.list_keys(user.id)}:
        raise HTTPException(status_code=404, detail="key not found")
    raw = store.rotate_key(key_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="key not found")
    rec = next((k for k in store.list_keys(user.id) if k.id == key_id), None)
    return {"key": raw, "record": rec.public() if rec else None}


@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, user=Depends(require_user)):
    store = get_account_store()
    if key_id not in {k.id for k in store.list_keys(user.id)}:
        raise HTTPException(status_code=404, detail="key not found")
    return {"ok": store.revoke_key(key_id), "revoked": key_id}


@router.get("/usage")
async def usage(user=Depends(require_user)):
    return get_account_store().usage_breakdown(user.id)