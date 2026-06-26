# Verify Guide — SearchBot wrap-up

Run these to confirm the work. **Part A is offline** (no keys, should fully pass). **Part B
needs your keys** (the live LLM/search/scrape paths I could not run overnight).

---

## Part A — Offline (verify now, no keys)

### A1. Backend unit tests (should show 67 passed)
```bash
cd backend
python -m pytest tests/ -q
```
Covers: URL/SSRF guard, RAG chunk+retrieval, LLM fallback chain, cache, lazy-init imports,
RAG wiring, the `/api/v1/query` endpoint (auth/envelope/cache/data-only-skips-LLM/synthesize),
concurrency lanes + memory guard, analytics aggregation, admin login + token gate.

### A2. App imports without keys
```bash
cd backend
python -c "from app import app; print(sorted({r.path for r in app.routes if r.path.startswith('/api')}))"
# -> ['/api/v1/query', '/api/admin/login', '/api/admin/analytics/summary', ...]
```

### A3. Frontend build
```bash
cd frontend
npx vite build      # must succeed
npm run dev         # then open http://localhost:5173/admin and /keys
```
`/admin` renders the dashboard with **sample data** until the backend has real analytics.
`/keys` shows the onboarding/key page. The chat input shows a "Reading this link" chip when
you paste a URL.

---

## Part B — Live paths (NEEDS KEYS)

### B1. Configure keys
```bash
cd backend
cp .env.example .env    # (a .env already exists with a GEMINI key — review it)
# set: SERPAPI_KEY, GEMINI_API_KEY, API_KEY (any strong string), optional OPENAI_API_KEY
pip install -r requirements.txt
pip install sentence-transformers   # optional: local embeddings (else hashing fallback)
playwright install chromium
```

### B2. Run the API
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
# OpenAPI for Postman: http://localhost:8000/docs  and  /openapi.json
```

### B3. Data API — each mode (set AUTH_MODE=static and your API_KEY)
```bash
KEY="your_api_key"
# search (data-only, no LLM)
curl -s -X POST localhost:8000/api/v1/query -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mode":"search","query":"who won euro 2024"}' | jq

# search + synthesized answer
curl -s -X POST localhost:8000/api/v1/query -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mode":"search","query":"who won euro 2024","options":{"synthesize":true}}' | jq

# analyze (always synthesizes)
curl -s -X POST localhost:8000/api/v1/query -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mode":"analyze","query":"impact of caffeine on sleep"}' | jq

# news
curl -s -X POST localhost:8000/api/v1/query -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mode":"news","query":"openai latest"}' | jq

# LINK MODE — scrape a given URL instead of searching
curl -s -X POST localhost:8000/api/v1/query -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mode":"analyze","query":"summarize this https://en.wikipedia.org/wiki/Web_scraping"}' | jq
```
Checks to make: envelope is `{mode,query,data,answer?,meta}`; `meta.cached` flips to `true` on
an identical second call; `synthesize:true` adds `answer`; link-mode sets `meta.link_mode:true`.

### B4. Auth
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/api/v1/query \
  -H "Content-Type: application/json" -d '{"mode":"search","query":"x"}'      # -> 401 (no key, AUTH_MODE=static)
```

### B5. Admin dashboard (set ADMIN_USER, ADMIN_PASSWORD_HASH, JWT_SECRET, ANALYTICS_ENABLED=True)
```bash
# password hash (sha256 fallback, or use a bcrypt hash):
python -c "import hashlib;print(hashlib.sha256(b'mypassword').hexdigest())"

TOKEN=$(curl -s -X POST localhost:8000/api/admin/login -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"mypassword"}' | jq -r .token)
curl -s localhost:8000/api/admin/analytics/summary -H "Authorization: Bearer $TOKEN" | jq
```
Then open `http://localhost:5173/admin`, sign in with the same creds → live charts.

---

## Known NEEDS-LIVE / follow-ups
- The Chromium scrape path (`scrape_isolated`) is verified by imports only; run B3 to exercise it.
- Thread the request **tier** (signed-in vs demo) from the API into the concurrency slot
  (manager is built + tested; wiring is a small follow-up).
- Supabase write-through for analytics + magic-link auth are **stubbed** (in-memory / static
  key work now); wire when you add Supabase creds.
- Bundle is ~680kB (Recharts) — code-split `/admin` later if you care about first load.
