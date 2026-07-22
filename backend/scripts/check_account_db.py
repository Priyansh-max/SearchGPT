"""Verify SearchBot account tables are reachable through Supabase PostgREST.

Loads backend/.env via config.py. Does not print secrets.
"""
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import settings  # noqa: E402

TABLES = {
    "account_users": "id,email,name,picture,heard_about,use_cases,onboarding_completed,onboarded_at,monthly_quota,credits_used",
    "account_api_keys": "id,user_id,name,prefix,scopes,usage_count,credits_spent,revoked",
    "account_email_codes": "email,code_hash,expires_at,attempts",
}


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    if (settings.ACCOUNT_STORE_BACKEND or "local").lower() != "supabase":
        return fail("ACCOUNT_STORE_BACKEND must be set to supabase")
    if not settings.SUPABASE_URL:
        return fail("SUPABASE_URL is missing")
    if not settings.SUPABASE_KEY:
        return fail("SUPABASE_KEY is missing")

    base = settings.SUPABASE_URL.rstrip("/") + "/rest/v1"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }

    try:
        with httpx.Client(timeout=15) as client:
            for table, columns in TABLES.items():
                resp = client.get(
                    f"{base}/{table}",
                    params={"select": columns, "limit": "1"},
                    headers=headers,
                )
                if resp.status_code >= 400:
                    return fail(f"{table} check failed with HTTP {resp.status_code}: {resp.text[:180]}")
                print(f"OK: {table}")
    except Exception as exc:
        return fail(f"could not reach Supabase: {exc}")

    print("OK: Supabase account database is configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())