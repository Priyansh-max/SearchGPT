# SearchGPT — Web Research Agent

SearchGPT is an open-source web research agent that finds, extracts, analyzes, and synthesizes information from the web. It combines structured search results from SerpAPI with page extraction, retrieval, and optional LLM synthesis behind one API and a React playground.

The primary public endpoint is:

```text
POST /api/v1/query
```

It supports four modes—`search`, `scrape`, `analyze`, and `news`—and preserves a consistent response envelope:

```json
{
  "mode": "search",
  "query": "your question",
  "data": {},
  "answer": "optional synthesized answer",
  "meta": {}
}
```

## How SearchGPT uses SerpAPI

SerpAPI is the discovery layer for the research pipeline. It replaces fragile search-engine result-page scraping with structured Google or Bing data that the application can normalize and use consistently.

For each web query, SearchGPT can use:

- Google organic results, including titles, links, snippets, positions, and thumbnails
- Google Knowledge Graph and answer-box results for structured facts
- Bing organic results through the same internal result format
- Google Images results for image research, previews, and downloadable source URLs

This data drives more than a results page:

- **Search** returns structured SerpAPI results directly and can optionally synthesize them.
- **Scrape** uses SerpAPI result URLs to identify relevant pages, then extracts their full content.
- **Analyze** follows the same discovery and extraction path, retrieves the most relevant passages, and produces a multi-source report.
- **News** tries dedicated news APIs and RSS feeds first, then uses SerpAPI-backed web search as its final discovery fallback.
- **Image requests** use SerpAPI's Google Images engine to return original images, thumbnails, titles, and source pages.

The fields matter throughout the pipeline: URLs determine which pages are opened, titles and snippets provide fast context, positions preserve relevance ordering, rich results add structured facts, and source metadata supports attribution. A cache hit bypasses SerpAPI, scraping, and LLM calls to reduce latency, cost, and rate-limit pressure.

## Features

- **Structured web search** — Google or Bing results through SerpAPI
- **Rich-result parsing** — organic results, Knowledge Graph records, answer boxes, and images
- **Full-page extraction** — Newspaper3k first, with isolated Playwright browser contexts as the dynamic-page fallback
- **Link mode** — safely scrape explicit HTTP(S) URLs after DNS-aware SSRF validation
- **Deep analysis** — multi-source extraction, passage retrieval, synthesis, source notes, and limitations
- **News aggregation** — GNews/NewsAPI, Google News RSS, Bing News RSS, and web-search fallback
- **LLM fallback** — Gemini first, optional OpenAI fallback, then a non-LLM formatter
- **Retrieval/RAG** — local MiniLM, OpenAI embeddings, or an always-available hashing fallback
- **Result caching** — repeated requests avoid search, scraping, and LLM work
- **Self-hosting** — the core engine does not require Supabase or hosted account services
- **Optional hosted features** — account auth, scoped API keys, credits, analytics, Google OAuth, Resend email, and Supabase persistence

## Architecture

```text
User / API client
        |
        v
FastAPI: POST /api/v1/query
        |
        +-- cache hit ------------------------------> response
        |
        +-- search ----------> SerpAPI ------------> structured results
        |
        +-- scrape/analyze --> SerpAPI or link mode
        |                         |
        |                         v
        |               Newspaper3k / Playwright
        |                         |
        |                         v
        |               passage retrieval / RAG
        |                         |
        |                         v
        |               Gemini -> OpenAI -> formatter
        |
        +-- news -----------> news APIs / RSS ------> SerpAPI fallback
```

## Technology stack

| Area | Technology |
| --- | --- |
| Search | SerpAPI via the `google-search-results` Python package; Google, Bing, and Google Images engines |
| Backend API | FastAPI, Pydantic, Uvicorn |
| Extraction | Newspaper3k, Playwright, Beautiful Soup, lxml |
| Synthesis | Google Gemini; optional OpenAI fallback |
| Retrieval | NumPy, optional Sentence Transformers or OpenAI embeddings, hashing fallback |
| News | GNews/NewsAPI, Google News RSS, Bing News RSS, SerpAPI-backed fallback |
| Frontend | React 19, Vite, Tailwind CSS, React Router, Recharts |
| Optional hosted services | Supabase PostgREST, Google OAuth/OpenID, Resend |
| Deployment | Docker Compose or a local Python/Node.js setup |

The active browser extraction path uses Playwright. `backend/utils/selenium_utils.py` is retained as legacy code but is not part of the current request path.

## Repository layout

```text
backend/
  api/          FastAPI routes, authentication, account, and admin endpoints
  services/     Search, extraction, retrieval, LLM, cache, analytics, and account logic
  tests/        Offline backend tests
  utils/        Playwright, text-processing, and URL/SSRF helpers
frontend/
  src/          React playground, developer pages, and admin dashboard
verify.md       Live-provider acceptance checklist
```

## Quick start with Docker

Docker installs Chromium and the required NLTK data as part of the image build.

```bash
cd backend
cp .env.example .env
```

Set these values in `backend/.env`:

```dotenv
SERPAPI_KEY=your_serpapi_key
GEMINI_API_KEY=your_gemini_api_key
API_KEY=choose_a_long_random_secret
```

Then start the backend:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Supabase, OpenAI, Google OAuth, Resend, quotas, and analytics are optional and disabled or unused by the core self-hosted path unless configured.

## Local development

### Backend

Python 3.10 is the container baseline.

```bash
cd backend
python -m venv venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

For semantic local retrieval, install `sentence-transformers`. If it is unavailable, the engine falls back to deterministic hashing retrieval. OpenAI generation or embeddings require the `openai` package and `OPENAI_API_KEY`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development frontend runs at `http://localhost:5173` and targets `http://localhost:8000` by default. Set `VITE_BACKEND_URL` to override the backend URL.

## API usage

### Search without LLM synthesis

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_API_KEY" \
  -d '{
    "mode": "search",
    "query": "how retrieval augmented generation works"
  }'
```

### Search with synthesis

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_API_KEY" \
  -d '{
    "mode": "search",
    "query": "how retrieval augmented generation works",
    "options": {"synthesize": true, "max_sources": 5}
  }'
```

### Analyze an explicit URL

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_API_KEY" \
  -d '{
    "mode": "analyze",
    "query": "summarize the main claims",
    "options": {"urls": ["https://example.com/article"]}
  }'
```

`analyze` always synthesizes. For the other modes, `options.synthesize` is additive: raw data remains in `data`, and the generated response is added as `answer`.

Authentication behavior is controlled by `AUTH_MODE`:

- `static` — one self-hosted `API_KEY`
- `keystore` — admin-managed keys and quotas
- `accounts` — hosted user accounts and scoped keys
- `off` — no API-key requirement
- `supabase` — reserved mode that currently returns `501` rather than silently weakening authentication

## Configuration

Use [`backend/.env.example`](backend/.env.example) as the source of truth. Important settings include:

| Setting | Purpose |
| --- | --- |
| `SERPAPI_KEY` | Enables web and image discovery |
| `SERPAPI_ENGINE` | Selects `google` or `bing`; defaults to `google` |
| `GEMINI_API_KEY` | Enables primary LLM synthesis |
| `OPENAI_API_KEY` | Enables optional generation and embedding fallback |
| `API_KEY` | Protects `/api/v1/query` in `AUTH_MODE=static` |
| `MAX_PAGES_TO_SCRAPE` | Limits browser extraction work per request |
| `EMBEDDING_MODE` | Selects `local`, `openai`, or `hashing` retrieval |
| `CACHE_ENABLED` / `CACHE_TTL` | Controls result reuse |
| `CORS_ORIGINS` | Restricts allowed frontend origins |
| `ACCOUNT_STORE_BACKEND` | Selects local JSON or optional Supabase account persistence |

Never expose provider keys, Supabase service-role credentials, or API keys in frontend code.

## Verification

The backend suite is offline and does not require provider keys:

```bash
cd backend
python -m pytest tests/ -q
python -c "from app import app; print(sorted({r.path for r in app.routes if r.path.startswith('/api')}))"
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

Live SerpAPI, LLM, news-provider, and browser checks are intentionally separate. Follow [`verify.md`](verify.md) only when usable provider keys are configured and you intend to spend API credit.

## Responsible scraping

Only HTTP(S) links are accepted in link mode. URLs are checked after DNS resolution, and loopback, private, link-local, and cloud-metadata targets are rejected. Operators are responsible for respecting website terms, robots policies, copyright, rate limits, and applicable law.
