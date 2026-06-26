"""
Admin analytics endpoints (Problem 5) — gate enforced SERVER-SIDE.

Login verifies ADMIN_USER + ADMIN_PASSWORD_HASH (bcrypt if available, sha256 fallback) and
issues a token (PyJWT if available, else an HMAC-signed token via JWT_SECRET). The analytics
endpoints require that token via `Authorization: Bearer <token>` — separate from the public
X-API-Key. The frontend dashboard only renders what these return; the password never reaches
the client.
"""
import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from config import settings
from services.analytics import get_recorder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

try:
    import jwt as _pyjwt  # PyJWT
    _HAS_JWT = True
except Exception:
    _pyjwt = None
    _HAS_JWT = False

_TOKEN_TTL = 86400  # 24h


def _verify_password(plain: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("$2"):  # bcrypt
        try:
            import bcrypt
            return bcrypt.checkpw(plain.encode(), stored_hash.encode())
        except Exception:
            return False
    # sha256 fallback (store sha256 hex if bcrypt unavailable)
    return hmac.compare_digest(hashlib.sha256(plain.encode()).hexdigest(), stored_hash)


def _make_token(username: str, secret: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + _TOKEN_TTL}
    if _HAS_JWT:
        return _pyjwt.encode(payload, secret, algorithm="HS256")
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def _verify_token(token: str, secret: str) -> Optional[dict]:
    if not token:
        return None
    if _HAS_JWT:
        try:
            return _pyjwt.decode(token, secret, algorithms=["HS256"])
        except Exception:
            return None
    try:
        raw, sig = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def admin_login(req: LoginRequest):
    if not (settings.ADMIN_USER and settings.ADMIN_PASSWORD_HASH and settings.JWT_SECRET):
        raise HTTPException(status_code=503, detail="admin dashboard not configured")
    if req.username != settings.ADMIN_USER or not _verify_password(req.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"token": _make_token(req.username, settings.JWT_SECRET)}


async def require_admin(authorization: Optional[str] = Header(default=None)) -> dict:
    if not settings.JWT_SECRET:
        raise HTTPException(status_code=503, detail="admin dashboard not configured")
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    payload = _verify_token(token, settings.JWT_SECRET)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid or missing admin token")
    return payload


@router.get("/analytics/summary")
async def analytics_summary(admin: dict = Depends(require_admin)):
    return get_recorder().aggregate()
