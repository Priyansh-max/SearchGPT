# Hosted Account Database Setup

SearchBot keeps the visible auth flow on your own backend domain. Supabase is used only as the server-side account database for users, email codes, API keys, and credit usage.

Do not put `SUPABASE_KEY` in frontend env vars. Use the Supabase `service_role` key only in `backend/.env` or your backend host secrets.

## 1. Create The Tables

In Supabase, open SQL Editor and run the full schema:

```sql
-- file: backend/migrations/001_account_auth.sql
```

Run migrations in order. The initial schema creates:

- `account_users`
- `account_api_keys`
- `account_email_codes`

RLS stays enabled. Backend requests use the service-role key through PostgREST.

If you already created the base tables, run only:

```sql
-- file: backend/migrations/002_account_onboarding.sql
```

## 2. Configure Backend Env

Set these in `backend/.env` or your backend host secrets:

```env
AUTH_MODE=accounts
ACCOUNT_STORE_BACKEND=supabase
ACCOUNT_MONTHLY_CREDITS=1000

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

SESSION_SECRET=replace_with_a_long_random_secret_32_chars_min
FRONTEND_URL=http://localhost:5173
```

For local/demo email sign-in without real email delivery, leave `RESEND_API_KEY` blank. The API returns a `dev_code`.

For production-looking email delivery:

```env
RESEND_API_KEY=your_resend_key
EMAIL_FROM=SearchBot <auth@yourdomain.com>
```

## 3. Verify DB Connectivity

From `backend/`:

```powershell
python scripts/check_account_db.py
```

Expected output:

```text
OK: account_users
OK: account_api_keys
OK: account_email_codes
OK: Supabase account database is configured
```

If this fails, fix the schema/env before testing login. The verifier does not print secrets.

## 4. Test Login And Key Flow

Start the backend:

```powershell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend:

```powershell
cd ../frontend
npm run dev
```

Then test:

1. Open `/signin?next=/developers`.
2. Enter email.
3. Use the email code or visible `dev_code`.
4. Confirm redirect to `/developers`.
5. Create an API key.
6. Refresh `/developers`; relogin should load user/key state from Supabase.
7. Call `/api/v1/query` with the generated `X-API-Key`.

## 5. Demo Mode Recommendation

For tomorrow's demo:

```env
AUTH_MODE=accounts
ACCOUNT_STORE_BACKEND=supabase
```

Use `RESEND_API_KEY` only if the sending domain is already verified. Otherwise keep dev-code login to avoid email-delivery risk during the demo.