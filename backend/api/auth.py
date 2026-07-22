"""
User auth endpoints for the hosted Developers flow.

Auth is owned by our backend domain: Google OAuth redirects to our API, and email auth is
passwordless via one-time codes. Supabase can remain the database later without exposing a
Supabase auth URL to users.
"""
import base64
import hashlib
import html
import hmac
import json
import logging
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from config import settings
from services.accounts import get_account_store

try:
    import jwt as _pyjwt
    _HAS_JWT = True
except Exception:  # pragma: no cover
    _HAS_JWT = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
SESSION_TTL_SECONDS = 30 * 24 * 3600
STATE_TTL_SECONDS = 10 * 60
EMAIL_CODE_TTL_SECONDS = 10 * 60
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
RESEND_SEND_URL = "https://api.resend.com/emails"


class EmailStartRequest(BaseModel):
    email: str


class EmailVerifyRequest(BaseModel):
    email: str
    code: str


def _secret() -> str:
    return settings.SESSION_SECRET or settings.JWT_SECRET or "dev-session-secret-change-me"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _make_hmac_token(payload: dict, secret: str) -> str:
    raw = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64(hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest())
    return f"{raw}.{sig}"


def _verify_hmac_token(token: str, secret: str) -> dict:
    try:
        raw, sig = token.split(".", 1)
        expected = _b64(hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(raw))
        if payload.get("exp") and payload["exp"] < time.time():
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="invalid session")


def make_session(user_id: str) -> str:
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time() + SESSION_TTL_SECONDS)}
    secret = _secret()
    if _HAS_JWT:
        return _pyjwt.encode(payload, secret, algorithm="HS256")
    return _make_hmac_token(payload, secret)


def verify_session(token: str) -> dict:
    secret = _secret()
    if _HAS_JWT:
        try:
            return _pyjwt.decode(token, secret, algorithms=["HS256"])
        except Exception:
            raise HTTPException(status_code=401, detail="invalid session")
    return _verify_hmac_token(token, secret)


def _make_state(next_path: str) -> str:
    next_path = next_path if next_path.startswith("/") else "/"
    payload = {"next": next_path, "nonce": secrets.token_urlsafe(12), "exp": int(time.time() + STATE_TTL_SECONDS)}
    return _make_hmac_token(payload, _secret())


def _verify_state(state: str) -> str:
    payload = _verify_hmac_token(state, _secret())
    next_path = payload.get("next") or "/"
    return next_path if next_path.startswith("/") else "/"


def _normalize_email(email: str) -> str:
    email = (email or "").lower().strip()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=400, detail="valid email is required")
    return email


def _auth_brand() -> tuple[str, str]:
    brand = (getattr(settings, "AUTH_BRAND_NAME", "") or "SearchBot").strip()
    public_url = (getattr(settings, "AUTH_PUBLIC_URL", "") or getattr(settings, "FRONTEND_URL", "") or "").strip()
    return brand, public_url.rstrip("/")


def _build_email_code_payload(email: str, code: str) -> dict:
    brand, public_url = _auth_brand()
    safe_brand = html.escape(brand)
    safe_email = html.escape(email)
    safe_url = html.escape(public_url)
    code_digits = " ".join(code)
    subject = f"{brand} sign-in code: {code}"
    manage_line = (
        f'<p style="margin:18px 0 0;color:#6b7280;font-size:13px;line-height:20px;">Open <a href="{safe_url}" style="color:#111827;text-decoration:underline;">{safe_url}</a> to continue.</p>'
        if public_url else ""
    )
    html_body = f"""
<!doctype html>
<html>
  <body style="margin:0;background:#f5f5f4;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
      <tr>
        <td style="padding:28px 28px 20px;border-bottom:1px solid #f0f0f0;">
          <div style="font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6b7280;">{safe_brand}</div>
          <h1 style="margin:10px 0 0;font-size:24px;line-height:32px;font-weight:700;color:#111827;">Your sign-in code</h1>
        </td>
      </tr>
      <tr>
        <td style="padding:28px;">
          <p style="margin:0;color:#374151;font-size:15px;line-height:24px;">Use this one-time code to finish signing in as <strong>{safe_email}</strong>.</p>
          <div style="margin:26px 0;padding:18px 20px;background:#111827;border-radius:10px;text-align:center;">
            <div style="font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;font-size:32px;line-height:38px;font-weight:800;letter-spacing:.18em;color:#ffffff;">{code_digits}</div>
          </div>
          <p style="margin:0;color:#4b5563;font-size:14px;line-height:22px;">This code expires in 10 minutes. If you did not request this email, you can safely ignore it.</p>
          {manage_line}
        </td>
      </tr>
      <tr>
        <td style="padding:18px 28px;background:#fafafa;border-top:1px solid #f0f0f0;color:#6b7280;font-size:12px;line-height:18px;">
          {safe_brand} will never ask you to share this code outside the sign-in page.
        </td>
      </tr>
    </table>
  </body>
</html>""".strip()
    text_lines = [
        f"Your {brand} sign-in code is {code}.",
        "",
        "This code expires in 10 minutes.",
        f"It was requested for {email}.",
    ]
    if public_url:
        text_lines.extend(["", f"Open {public_url} to continue."])
    text_lines.extend(["", "If you did not request this email, you can ignore it."])
    return {
        "subject": subject,
        "html": html_body,
        "text": "\n".join(text_lines),
    }


async def _send_email_code(email: str, code: str) -> bool:
    api_key = getattr(settings, "RESEND_API_KEY", "")
    sender = getattr(settings, "EMAIL_FROM", "") or "SearchBot <onboarding@resend.dev>"
    if not api_key:
        logger.info("Email sign-in code for %s: %s", email, code)
        return False

    payload = _build_email_code_payload(email, code)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            RESEND_SEND_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": sender,
                "to": [email],
                **payload,
            },
        )
        if resp.status_code >= 400:
            detail = "could not send email code"
            try:
                resend_error = resp.json().get("message") or resp.json().get("error")
                if resend_error:
                    detail = f"Resend rejected email: {str(resend_error)[:180]}"
            except Exception:
                resend_error = resp.text[:180]
            logger.warning("Resend email failed: %s %s", resp.status_code, str(resend_error)[:200])
            raise HTTPException(status_code=502, detail=detail)
    return True


async def require_user(authorization: Optional[str] = Header(default=None)):
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="missing session")
    payload = verify_session(token)
    user = get_account_store().get_user(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user


@router.post("/email/start")
async def start_email(req: EmailStartRequest):
    email = _normalize_email(req.email)
    code = get_account_store().create_email_code(email, EMAIL_CODE_TTL_SECONDS)
    sent = await _send_email_code(email, code)
    out = {"ok": True, "sent": sent, "expires_in": EMAIL_CODE_TTL_SECONDS}
    if not sent:
        out["dev_code"] = code
    return out


@router.post("/email/verify")
async def verify_email(req: EmailVerifyRequest):
    email = _normalize_email(req.email)
    if not get_account_store().verify_email_code(email, req.code):
        raise HTTPException(status_code=401, detail="invalid or expired code")
    user = get_account_store().get_or_create_verified_email_user(email)
    return {"token": make_session(user.id), "user": user.public()}


@router.get("/me")
async def me(user=Depends(require_user)):
    return user.public()


@router.get("/google/login")
async def google_login(next: str = Query("/")):
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_REDIRECT_URI):
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": _make_state(next),
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str = Query(""), state: str = Query("")):
    if not code:
        raise HTTPException(status_code=400, detail="missing code")
    next_path = _verify_state(state)
    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if token_resp.status_code >= 400:
            raise HTTPException(status_code=401, detail="Google token exchange failed")
        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_resp.status_code >= 400:
            raise HTTPException(status_code=401, detail="Google profile fetch failed")
        profile = user_resp.json()

    email = profile.get("email")
    sub = profile.get("sub")
    if not email or not sub:
        raise HTTPException(status_code=401, detail="Google profile missing email")
    if profile.get("email_verified") is False:
        raise HTTPException(status_code=401, detail="Google email is not verified")
    user = get_account_store().upsert_google_user(
        sub,
        email,
        name=profile.get("name", ""),
        picture=profile.get("picture", ""),
        email_verified=True,
    )
    token = make_session(user.id)
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{urlencode({'token': token, 'next': next_path})}")