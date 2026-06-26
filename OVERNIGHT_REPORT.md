# Overnight Work Report — SearchBot wrap-up

Branch: **`wrapup-overnight`** (NOT pushed — review locally). Plan: `wrapup.md`.

> **Hard limit:** no API keys were provided, so the full pipeline (Gemini / SerpAPI / OpenAI /
> Supabase) could not be run end-to-end. Everything below is either (a) verified by offline
> unit tests / builds, or (b) clearly marked **NEEDS KEYS** for you to verify with the morning
> test script. Nothing is claimed "tested" that wasn't.

---

## ✅ Done & verified (offline)

| Problem | What | Verification |
|---|---|---|
| Secrets | Root `.gitignore` — Oracle SSH key (`server/`), `.env`, `*.key` excluded | `git check-ignore` confirms key is ignored |
| 7 | Copy response / Copy summary buttons | `vite build` passes |
| 6 | URL detection + **SSRF guard** (`utils/url_utils.py`) | 16 unit tests pass |
| 2 | RAG core: chunking + cosine retrieval, pluggable embedders (`services/retrieval.py`) | 8 unit tests pass |
| 3 | LLM fallback chain Gemini→OpenAI (`services/llm_provider.py`) | 9 unit tests pass |
| — | Config layering + complete `.env.example` (self-host vs hosted) | imports clean |
| 1 | Result cache `TTLCache` + key normalization (`services/cache.py`) | 7 unit tests pass |
| 3/1 | `LLMProcessor` lazy init + routed through fallback chain; async; out-tokens 8192 | 2 import tests; imports keyless |

Backend tests: **42 passing** (`cd backend && python -m pytest tests/ -q`).

> **Note:** a real `GEMINI_API_KEY` is present in `backend/.env`. I did **not** use it for any
> generation calls (credit care + you said keys come in the morning). One cheap `list_models`
> metadata call happened once during a test, now eliminated. Tell me if you want overnight live
> testing enabled with that key.

---

## 🔑 SECURITY NOTE (action for you)
Your **Oracle private SSH key** is sitting in the repo at `server/ssh-key-2026-06-26.key`.
I git-ignored it so it can't be committed/pushed, but you should **move it out of the project
folder** to be safe. Never commit private keys.

---

## ⏳ In progress / remaining (this loop continues overnight)
- [x] Lazy-init `llm_processor` + route LLM calls through fallback chain (async, 8192 tokens) — done
- [ ] Wire `retrieval` into the synthesize/scrape paths (replace char-truncation with passages)
- [x] Caching layer (skip scrape+LLM on repeat queries) — done, 7 tests
- [ ] Playwright per-request context + semaphore lanes + memory guard (Problem 1)
- [ ] Single `POST /api/v1/query` endpoint + envelope + `X-API-Key` middleware (Problem 4)
- [ ] Link-mode integration into the request path (Problem 6)
- [ ] Analytics `events` + admin endpoints (Problem 5, behind `ANALYTICS_ENABLED`)
- [ ] Frontend: link chip, admin dashboard (Recharts), key/onboarding page, design polish
- [ ] Competitive research doc (vs Tavily/Exa/Perplexity/Firecrawl)
- [ ] Final morning test script (`verify.sh` / `verify.md`) for the key-dependent paths

---

## Commits so far
(see `git log --oneline wrapup-overnight`)
