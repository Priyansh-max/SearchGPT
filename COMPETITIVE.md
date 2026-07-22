# Competitive Analysis — SearchBot vs the paid web-search/scrape APIs

Goal: position SearchBot as the **open-source, self-hostable** alternative to the paid
"search + scrape + answer" APIs that AI apps build on. Pricing figures are approximate and
move often — verify before quoting (sourced below).

## The incumbents

### Tavily — search API for LLMs
- **What:** search + content extraction tuned for RAG; basic/advanced depth.
- **Pricing:** 1,000 free credits/month (no card); basic search = 1 credit, advanced = 2;
  pay-as-you-go ~$0.008/credit; Researcher $30/mo, Startup $100/mo (~15k searches).
  Credits **don't roll over**.
- **Strength:** dead-simple, LLM-friendly results, generous-ish free tier.

### Firecrawl — scrape/crawl + search "context API"
- **What:** Find → Extract → Clean → Use in one API (scrape/crawl/map/search/extract).
- **Pricing:** 1,000 free pages/mo; Hobby $16 (5k credits), Standard $83 (100k), Growth $333
  (500k), Scale $599 (1M). Scrape = 1 credit/page, search = 2 credits/10 results, stealth = 5
  credits/page. Credits **don't roll over**.
- **Strength:** full pipeline in one vendor, predictable per-page cost, JS rendering/stealth.

### Exa — neural/semantic search + Contents API
- **What:** embeddings-based discovery; you search, then call the Contents API to extract.
- **Pricing:** usage-based; two-step (search + contents) so most teams stitch a search API +
  scraper + browser together.
- **Strength:** semantic/neural relevance, good for discovery.

### Perplexity Sonar API — search-grounded answers
- **What:** hosted "answer" models with built-in web grounding + citations.
- **Pricing:** token-based ($0.20/1M up to ~$15/1M output for Pro) **plus** per-request search
  fees ($14–$22 / 1k queries for Pro Search). You pay for the model AND the search.
- **Strength:** turnkey cited answers, strong models, no infra.

### Brave Search API — independent index
- **What:** independent web index (not Google/Bing reseller).
- **Pricing:** **free tier removed** — now $5 prepaid metered, ~$0.003–0.005/query, card
  required, attribution required.
- **Strength:** independent index, privacy positioning.

## What SearchBot has today

| Capability | SearchBot | Typical paid API |
|---|---|---|
| Search (SerpAPI) | ✅ | ✅ |
| Scrape (own Playwright pipeline) | ✅ hand-built | ✅ managed |
| Synthesized answer (LLM) | ✅ `synthesize` flag | ✅ (often a separate product) |
| Semantic retrieval / RAG over sources | ✅ chunk + embed + rank | ⚠️ varies |
| One endpoint, modes | ✅ `/api/v1/query` | ⚠️ multiple endpoints |
| LLM fallback (Gemini→OpenAI) | ✅ | ❌ (single vendor) |
| Result caching | ✅ | ⚠️ you build it |
| **Self-host with your own keys** | ✅ **$0 per call** | ❌ metered forever |
| Transparent, hackable pipeline | ✅ open source | ❌ black box |
| Link-mode (answer over a given URL) | ✅ SSRF-guarded | ⚠️ via extract |
| Analytics + admin dashboard | ✅ built in | ⚠️ external |

## What we lack (honest gaps / roadmap)
- **Independent index** — we rely on SerpAPI for search (cost + dependency); Brave/Exa own theirs.
- **Managed scale & SLAs** — incumbents run global infra; we're self-host/single-box first.
- **Stealth/anti-bot at scale** — Firecrawl's stealth mode is more battle-tested than our Playwright.
- **Crawl/map** (multi-page site crawl) — we do single-page scrape, not full-site crawl.
- **Polished SDKs** — they ship typed SDKs; we have OpenAPI (Postman-importable) for now.
- **Embedding quality** — default MiniLM/hashing is fine, not best-in-class vs neural search.

## The disruption angle
The paid players all share one structural weakness for heavy users: **every call is metered
forever, credits don't roll over, and free tiers are shrinking** (Brave just killed theirs).
SearchBot's wedge:

1. **Self-host = your keys, your box, $0 per call.** Heavy users escape metering entirely —
   the exact users who cost the incumbents the most are the ones we serve best.
2. **One transparent pipeline, not a black box.** Search → scrape → RAG → answer is readable,
   forkable, and tunable (chunking, model, prompts) — impossible with a closed API.
3. **Vendor-resilient by design.** Gemini→OpenAI fallback and swappable SerpAPI/embedding
   backends mean no single price hike or rate limit breaks you.
4. **Generous hosted demo + cheap onboarding** funnels evaluators in; power users graduate to
   self-host instead of churning to a competitor.

Positioning line: **"The open-source Tavily/Firecrawl — run it free on your own box, or use our
hosted demo to try it. One endpoint, your keys, no per-call meter."**

## Sources
- Tavily: [pricing](https://www.tavily.com/pricing), [credits docs](https://docs.tavily.com/documentation/api-credits)
- Firecrawl: [pricing](https://www.firecrawl.dev/pricing), [best web search APIs](https://www.firecrawl.dev/blog/best-web-search-apis)
- Exa: [Exa alternatives overview](https://www.firecrawl.dev/blog/exa-alternatives)
- Perplexity Sonar: [pricing docs](https://docs.perplexity.ai/docs/getting-started/pricing), [CloudZero breakdown](https://www.cloudzero.com/blog/perplexity-api-pricing/)
- Brave: [API pricing](https://api-dashboard.search.brave.com/documentation/pricing), [free tier removal](https://www.implicator.ai/brave-drops-free-search-api-tier-puts-all-developers-on-metered-billing/)
