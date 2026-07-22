# SearchBot — Wrap-up Plan

Living spec for finishing the project. Each problem gets locked here as we settle it.

Design principle threaded through everything: **the engine runs on just the 3 API keys
(SerpAPI + Gemini + optional OpenAI). Everything hosted-only — Supabase auth, analytics,
multi-user API keys, quotas — is an OPTIONAL toggle, OFF by default.** This is what keeps
both the hosted path and the self-host path simple.

---

## Problem 1 — Concurrency & Scaling  ✅ LOCKED

### Root causes (what we're actually fixing)
1. **One shared browser tab for the whole server** (`utils/playwright_utils.py` singleton
   `self.page`) → concurrent scrapes corrupt each other's results. Also breaks *within* a
   single `/analyze` (10 gathered scrapes share one page).
2. **Synchronous Gemini call** inside async code (`llm_processor._generate_content` →
   `model.generate_content`) → freezes the worker, serializes all users.
3. **Chromium on 512 MB** → memory pressure / crashes.
4. **No fairness** → a demo user can starve a signed-in user.

### Engine correctness fixes (host-independent — do these regardless)
- **`utils/playwright_utils.py`** — kill the shared page. One browser launched once at
  startup (FastAPI `lifespan`); **each scrape gets its own isolated `context` + `page`**,
  used then closed. Block **images/fonts/media/css** via route interception.
- **`services/content_extractor.py`** — use per-request context; a **tier-aware concurrency
  manager** (two semaphore pools: reserved signed-in + demo; demo may borrow idle signed-in
  slots but yields); **memory guard** before opening a page → graceful "busy" instead of crash.
- **`services/llm_processor.py`** — swap to **`generate_content_async`** so requests interleave.
- **`app.py`** — browser start/stop in `lifespan`; dependency that tags each request
  **demo vs signed-in** (stub: "valid key present?"; real validation lands with Problems 4/5).
- **Caching (highest-leverage free win):** wire the unused `CACHE_ENABLED`. Same/normalized
  query within TTL → return cached JSON, **skip scrape AND LLM**. Cuts latency, cost, and
  rate-limit pressure. Store in Supabase table (hosted) or in-process (self-host).

### Concurrency config (env-tunable, no code change to retune)
| Env var | Purpose | small box | notes |
|---|---|---|---|
| `SIGNEDIN_SLOTS` | reserved concurrent pages for keyed traffic | 2 | demo box: 0 |
| `DEMO_SLOTS` | concurrent pages for anonymous | 1 | signed-in box: 0 |
| `MEMORY_GUARD_MB` | min free MB before opening a page | ~120 | graceful-busy trigger |
| `BLOCK_RESOURCES` | block img/font/media/css | true | |
| `CACHE_ENABLED` / `CACHE_TTL` | result cache | true / 3600 | already in config |

### Hosting (the engine)
- **Now:** **DigitalOcean Droplet** (4–8 GB, covered by the $200 credit — credit **expires next
  month**, unused credit is lost, so size up while it's free). Real RAM → Chromium runs with
  proper concurrency; no 512 MB gymnastics, no keep-alive hack.
- **Frontend:** stays on **Vercel** (already there; always-warm CDN — do NOT migrate).
- **State:** **Supabase** (keys, quotas, analytics) → app servers stay **stateless**.
- **Before credit expires, pick the landing:** Oracle Always-Free A1 (2 OCPU / 12 GB) **if it
  finally provisions** (single-AD region, "out of capacity" — running an auto-retry), else
  **downsize the droplet** to a cheap 1–2 GB (~$6–12/mo). Because the engine is
  **Dockerized + stateless**, every move = "run the same container elsewhere + repoint DNS."

> Note: Oracle free shape is `VM.Standard.A1.Flex`, limit **2 OCPU / 12 GB** (1,500 OCPU-hrs +
> 9,000 GB-hrs/mo). `A4`/`DVH` shapes are paid. Capacity scarce in single-AD regions.

### Two onboarding paths — BOTH must be simple
**Hosted API user:**
1. Magic-link sign-in on the site → key shown on dashboard.
2. Call `/api/v1/*` with `X-API-Key`. (OpenAPI spec → import into Postman.)

**Self-hoster (open-source clone):**
1. `git clone`
2. `cp .env.example .env` → set `SERPAPI_KEY`, `GEMINI_API_KEY`, and a self-chosen `API_KEY`
   (optionally `OPENAI_API_KEY`).
3. `docker compose up`
4. Call the same `/api/v1/*` with their `API_KEY`.
- **No Supabase account required.** Auth in self-host mode = simple static key(s) from env
  (or `AUTH_ENABLED=false` for fully open local use). Analytics/quotas off by default.

### Layering that makes both simple (the toggles)
- `AUTH_MODE` = `supabase` (hosted, magic-link, multi-user) | `static` (self-host, env key) | `off`
- `ANALYTICS_ENABLED` = true (hosted, Supabase) | false (self-host)
- `QUOTA_ENABLED` = true (hosted) | false (self-host)
- Core engine + `/api/v1/*` work with all of these off.

### Demo gate UX (two distinct messages)
- **Allowance used:** "You've used your free demo queries — sign in for a free key to keep going."
- **Capacity busy:** "Lots of people are demoing right now — try again shortly, or sign in to
  skip the queue." (Reserve a signed-in slot so "skip the queue" is a real promise.)

### Explicitly deferred
- Web + worker hard process split (keep scraper logically separable for a later config change).
- Redis job queue / scaling past one box.
- Real per-key quota *enforcement* (mechanism hooks here; counting lands with Problems 4/5).

---

## Problem 2 — Truncation losing data  ✅ LOCKED (Option C: semantic retrieval / RAG)

### The bug (two truncations)
1. **Input cut:** scrape mode = first 5 sources × 1500 chars; analyze = 5 × 1200. Sources 6+
   dropped; long pages lose their tail (buried answer lost).
2. **Output cut:** `max_output_tokens = 2048` clips the *answer* even with full input.

### Why naive "fit everything" is wrong
- The OpenAI fallback (Problem 3, `gpt-4o-mini`) has **128k** context, not Gemini's 1M.
  Budget must fit the **smallest** model in the chain.
- Whole-source selection doesn't fix **within-page** loss; only passage-level retrieval does.

### Locked design — embed at CHUNK level, ephemeral in-memory RAG
1. Scrape **N sources**, `N = min(client_requested, 10)` (hard cap 10; configurable default).
2. Split each source into passages (~500–1000 chars, slight overlap).
3. Embed all passages + the query → **cosine-rank** → take **top-K passages** until a token
   budget (sized to fit the 128k fallback model, with room for prompt + output) is filled.
4. Feed those passages (+ source URLs for citations) to the LLM. **Raise `max_output_tokens`
   2048 → 8192.**

### Why this is the right call
- Fixes truncation properly (relevance-ranked passages, nothing arbitrarily cut).
- Sends the LLM **fewer, better tokens** → eases the rate limit (Problem 3) and cuts cost.
- **No vector DB** — content is scraped fresh per query, so retrieval is ephemeral in-memory
  (numpy cosine over the query's chunks). Nothing to maintain.

### Embedding model (env toggle, default keeps self-host simple)
- `EMBEDDING_MODE=local` (default) → `sentence-transformers/all-MiniLM-L6-v2` (~80 MB, CPU,
  **free, no extra API key**). Fits the DO droplet fine.
- `EMBEDDING_MODE=openai` → `text-embedding-3-small` (tiny image, cheap, adds a key dep).

### Config knobs
| Env var | Purpose | default |
|---|---|---|
| `MAX_SOURCES` | hard cap on sources used | 10 |
| `EMBEDDING_MODE` | `local` \| `openai` | local |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | passage sizing | ~800 / ~100 chars |
| `RETRIEVAL_TOKEN_BUDGET` | top-K passage budget (fits 128k fallback) | ~90k tokens |
| `max_output_tokens` | answer length | 8192 |

### Deferred
- Map-reduce for pathological huge-content cases (retrieval makes it unnecessary for ~95%).
- Persistent vector store / cross-query caching of embeddings.

## Problem 3 — Gemini rate limit / fallback  ✅ LOCKED

**One `generate()` wrapper** — all LLM methods route through it (fallback logic in one place).

**Three tiers, never a hard crash:**
1. **Gemini** primary, **async** (`generate_content_async` — also fixes the Problem 1 blocking call).
2. **OpenAI** (`gpt-4o-mini`, async) fallback.
3. **Basic non-LLM formatter** (already in code: `_format_basic_*`) as last resort → user always
   gets something.

**Fallback triggers:** 429, 5xx, timeout, empty/safety-blocked response ("Gemini didn't return a
usable answer → try OpenAI"). On 429 **fail over immediately** (no slow backoff); one quick retry
allowed for transient 5xx/timeout.

**Details:**
- `OPENAI_API_KEY` **optional** — unset = fallback disabled (Gemini-only). Self-hosters not forced
  to get an OpenAI key.
- OpenAI **JSON mode** for the structured (`synthesize`) path — more reliable JSON than Gemini.
- **Log which provider answered** → feeds Problem 5 analytics.
- **Caching (Problem 1) sits in front** — a cache hit skips both providers.

| Env var | Purpose | default |
|---|---|---|
| `OPENAI_API_KEY` | enables fallback | unset = off |
| `OPENAI_MODEL` | fallback model | `gpt-4o-mini` |
| `LLM_PRIMARY` | provider order | `gemini` |

## Problem 4 — Data API: single endpoint + modes  ✅ LOCKED

**One endpoint** `POST /api/v1/query` — `mode` selects the tool. (Not 4 separate routes; matches the
"tools as modes" model, one auth/quota/rate-limit path, one OpenAPI op → clean Postman import.)

**Request:**
```json
{ "mode": "search|scrape|analyze|news", "query": "...",
  "options": { "max_sources": 10, "synthesize": false } }
```

**Consistent response envelope** (same top-level shape every mode):
```json
{ "mode": "search", "query": "...",
  "data": { /* mode-specific structured payload */ },
  "answer": "…",                       // present only when synthesize=true
  "meta": { "cached": false, "synthesized": false, "provider": "gemini", "sources_used": 8 } }
```

**Output is ALWAYS JSON.** `synthesize` is **additive**:
- `false` (default) → raw structured `data` only, **no LLM** (cheap/fast).
- `true` → same `data` **plus an `answer` field** (LLM text). Raw sources still present for citations.
- `analyze` mode = shorthand for "always synthesize."
- `synthesize` is the **cost lever** → weighs heavier against quota (LLM tokens spent).

**Gated by `X-API-Key`.** Self-hosters use their static env key on the same endpoint.

## Problem 5 — Analytics + admin dashboard  ✅ LOCKED

### Identities
- API users → their **API key**; playground visitors → anonymous **`client_id`** (localStorage UUID) + IP.

### Data model — ONE append-only `events` table
```
events(created_at, identity_type, identity_id, ip_hash, geo_country, geo_city,
       event_type, mode, query_text, synthesize, cached, provider, status,
       latency_ms, session_id)
```
Everything (queries/day, per-key usage, geo, time-spent, provider mix) derived via **SQL views**.
Store **hashed IP** (not raw) — public tool. Supabase free tier.

### Time-spent (no auth)
- Every query carries a per-page-load **`session_id`** → first/last delta = rough active window.
- Plus a **visible-only heartbeat** (`navigator.sendBeacon`, ~30s, only while tab visible) →
  time-spent ≈ heartbeats × interval. Catches "reading the answer" without unreliable unload events.

### Admin dashboard — gate enforced SERVER-SIDE (critical)
Frontend is public → a React-only password check is fake security. The real gate is on the
**backend endpoints that serve the data**.
- **Backend:** `ADMIN_USER` + `ADMIN_PASSWORD_HASH` env vars (only the owner sets; bcrypt-hashed,
  never in repo/frontend). `POST /api/admin/login` → **signed JWT** (~24h). `GET /api/admin/analytics/*`
  require the JWT (separate from public `X-API-Key`). **Rate-limit login**; HTTPS via Caddy.
- **Frontend:** `/admin` route → login form → JWT → **Recharts** dashboard.

### Graphs
Queries over time; by mode; geo distribution; demo vs signed-in; top API keys by usage;
provider mix (Gemini vs OpenAI); cache-hit rate; avg latency; active sessions / time-spent.

### Self-host
`ANALYTICS_ENABLED=false` by default → collects nothing. Self-hosters may enable it + set their
own admin creds. Reads the same `events` table + views.

## Problem 6 — Link input mode  ✅ LOCKED

### Behavior
Detect URL(s) in the input → **skip SerpAPI** → scrape only those URL(s) → same RAG pipeline
(Problem 2) → answer per the query. Only the **source-acquisition** step changes ("given URLs"
instead of "SerpAPI search"); everything downstream is unchanged.

### How URLs get in (both)
- **API:** explicit `options.urls: [...]` array.
- **Playground:** auto-detect URLs in the query text (regex), strip them out, rest = the question.

### Security — SSRF guard (NON-NEGOTIABLE, public tool)
Resolve the host and **block loopback / private / link-local IPs + cloud metadata endpoints
(169.254.169.254)**; allow only `http`/`https`. Without this, users could make the server fetch
internal addresses and leak credentials.

### Filters
- **Bypass the search domain blacklist** (`is_valid_url` blocks linkedin/youtube/PDF — right for
  search, wrong here; if the user pastes it, they want it).
- **Keep the SSRF guard.** Different filters for different jobs.

### Defaults
- URL but no question → default "summarize / extract key info".
- Multiple URLs → scrape all up to `MAX_SOURCES=10`, retrieve across them, answer.

### UX
Frontend shows a chip/highlight ("📎 reading this link") when a URL is detected. Cacheable
(key = urls + query). Works in playground and Data API; in the single endpoint, detected URLs
or `options.urls` override source-acquisition for any mode.

## Problem 7 — Copy buttons  ✅ DONE
`ChatMessage.jsx`: "Copy response" (full markdown) + "Copy summary" (strips References/Sources).
Verified `vite build` passes.
