# Backend Migrations

Run these SQL files in order from Supabase SQL Editor for hosted account auth.

- `001_account_auth.sql`: base account users, API keys, email codes, and RLS policies.
- `002_account_onboarding.sql`: first-run onboarding fields on `account_users`.

Keep migrations idempotent with `if not exists` where Supabase/Postgres supports it.
