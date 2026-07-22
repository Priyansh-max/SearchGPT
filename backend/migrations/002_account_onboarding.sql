-- One-time migration for first-run onboarding fields.
-- Safe to run more than once.

alter table public.account_users add column if not exists heard_about text not null default '';
alter table public.account_users add column if not exists use_cases jsonb not null default '[]'::jsonb;
alter table public.account_users add column if not exists onboarding_completed boolean not null default false;
alter table public.account_users add column if not exists onboarded_at double precision;

comment on column public.account_users.heard_about is 'Where the user heard about SearchBot.';
comment on column public.account_users.use_cases is 'Selected onboarding use cases for product metrics.';
comment on column public.account_users.onboarding_completed is 'Whether the user finished first-run onboarding.';
comment on column public.account_users.onboarded_at is 'Unix timestamp when onboarding was completed.';