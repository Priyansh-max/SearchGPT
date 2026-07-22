-- SearchBot hosted account database schema.
-- Use this when moving ACCOUNT_STORE from local JSON to Supabase Postgres.
-- Keep Supabase as the database; do not use Supabase Auth for the branded OAuth flow.

create table if not exists public.account_users (
  id text primary key,
  email text not null unique,
  name text not null default '',
  picture text not null default '',
  password_hash text,
  google_sub text unique,
  email_verified boolean not null default false,
  heard_about text not null default '',
  use_cases jsonb not null default '[]'::jsonb,
  onboarding_completed boolean not null default false,
  onboarded_at double precision,
  created_at double precision not null,
  monthly_quota integer not null default 1000,
  credits_used integer not null default 0,
  period_start double precision not null
);

alter table public.account_users add column if not exists heard_about text not null default '';
alter table public.account_users add column if not exists use_cases jsonb not null default '[]'::jsonb;
alter table public.account_users add column if not exists onboarding_completed boolean not null default false;
alter table public.account_users add column if not exists onboarded_at double precision;

create table if not exists public.account_api_keys (
  id text primary key,
  user_id text not null references public.account_users(id) on delete cascade,
  name text not null,
  key_hash text not null unique,
  prefix text not null,
  scopes jsonb not null default '["search", "scrape", "analyze", "news"]'::jsonb,
  created_at double precision not null,
  last_used_at double precision,
  revoked boolean not null default false,
  usage_count integer not null default 0,
  credits_spent integer not null default 0
);

create index if not exists account_api_keys_user_id_idx on public.account_api_keys(user_id);
create index if not exists account_api_keys_key_hash_idx on public.account_api_keys(key_hash) where revoked = false;
create table if not exists public.account_email_codes (
  email text primary key,
  code_hash text not null,
  expires_at double precision not null,
  attempts integer not null default 0,
  created_at double precision not null default extract(epoch from now())
);

create index if not exists account_email_codes_expires_at_idx on public.account_email_codes(expires_at);

-- If exposing these tables through PostgREST with a service role key, keep RLS enabled
-- and grant access only to backend service credentials. Browser clients should never receive
-- the service role key.
alter table public.account_users enable row level security;
alter table public.account_api_keys enable row level security;
alter table public.account_email_codes enable row level security;
comment on table public.account_users is 'SearchBot hosted account users. Auth is owned by backend, not Supabase Auth.';
comment on table public.account_api_keys is 'SearchBot user-owned API keys. Raw keys are never stored, only SHA-256 hashes.';
comment on table public.account_email_codes is 'Passwordless email login codes. Codes are SHA-256 hashed and short-lived.';