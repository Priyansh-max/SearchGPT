/**
 * Playground API service.
 * The public API remains /api/v1/query for API-key users. The UI playground uses
 * the signed-in account endpoint so users can demo without exposing raw API keys.
 */
import { API_CONFIG } from '../config';
import { authFetch, getToken } from './auth';

const normalizeMode = (tool) => ({
  search: 'search',
  scraper: 'scrape',
  analyzer: 'analyze',
  news: 'news',
}[tool] || 'search');

const modeLabels = {
  search: 'Web search',
  scrape: 'Scrape',
  analyze: 'Analyze',
  news: 'News',
};

const parseError = async (response) => {
  try {
    const body = await response.json();
    return body.detail || 'Request failed';
  } catch {
    return 'Request failed';
  }
};

export const runPlaygroundQuery = async ({ query, tool = 'search', synthesize = true, maxSources = 5 }) => {
  const mode = normalizeMode(tool);
  const body = JSON.stringify({
    mode,
    query,
    options: {
      max_sources: maxSources,
      synthesize: mode === 'analyze' ? true : synthesize,
    },
  });

  const response = getToken()
    ? await authFetch('/api/account/playground/query', { method: 'POST', body })
    : await fetch(`${API_CONFIG.BASE_URL}/api/playground/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      });

  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
};


const hostnameFromUrl = (url) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
};

const faviconFor = (url) => {
  const domain = hostnameFromUrl(url);
  return domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
};

const isContentImage = (url) => {
  if (!url || !/^https?:\/\//i.test(url)) return false;
  const lowered = String(url).toLowerCase();
  return ![
    'google.com/s2/favicons',
    '/favicon',
    'favicon.',
    'apple-touch-icon',
    'logo.svg',
  ].some((token) => lowered.includes(token));
};

const imageFrom = (item) => {
  const image = item.image || item.original || item.thumbnail || item.urlToImage || item.image_url || item.metadata?.image || '';
  return isContentImage(image) ? image : '';
};

const trim = (value, max = 320) => {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  return text.length > max ? `${text.slice(0, max).trim()}...` : text;
};

export const extractImages = (response) => {
  const rows = response?.data?.images || [];
  return rows
    .map((item, index) => ({
      ref: index + 1,
      title: item.title || response?.query || 'Image result',
      image: imageFrom(item),
      thumbnail: isContentImage(item.thumbnail) ? item.thumbnail : '',
      url: item.source_url || item.link || item.url || '',
      source: item.source || hostnameFromUrl(item.source_url || item.link || item.url || ''),
      domain: hostnameFromUrl(item.source_url || item.link || item.url || ''),
    }))
    .filter((item) => item.image)
    .slice(0, 4);
};

export const extractSources = (response) => {
  const mode = response?.mode;
  const data = response?.data || {};
  const rows = mode === 'search'
    ? data.results || []
    : mode === 'news'
      ? data.articles || []
      : mode === 'analyze'
        ? data.sources || []
        : data.sources || [];

  return rows
    .map((item, index) => {
      const url = item.url || item.link || '';
      return {
        ref: index + 1,
        title: item.title || item.source || url || 'Untitled source',
        url,
        domain: hostnameFromUrl(url) || item.source || '',
        favicon: faviconFor(url),
        image: imageFrom(item),
        images: Array.isArray(item.images) ? item.images : [],
        snippet: item.snippet || item.content || item.summary || '',
        content: item.content || '',
        published_date: item.published_date || item.date || item.metadata?.published_date || '',
        source_name: item.source || item.metadata?.source || '',
      };
    })
    .filter((item) => item.title || item.url || item.snippet)
    .slice(0, 8);
};

const formatRawData = (response) => {
  const { mode, query, data = {} } = response || {};
  if (mode === 'search') {
    const results = data.results || [];
    if (!results.length) return 'No search results found.';
    return `## Search results for "${query}"\n\n${results.slice(0, 6).map((result, index) => `[${index + 1}] **${result.title || 'Untitled'}**\n${trim(result.snippet, 220)}\n${result.url ? `[Open source](${result.url})` : ''}`).join('\n\n')}`;
  }
  if (mode === 'news') {
    const articles = data.articles || [];
    if (!articles.length) return 'No news articles found.';
    return `## News results for "${query}"\n\n${articles.slice(0, 6).map((article, index) => `[${index + 1}] **${article.title || 'Untitled'}**\n${trim(article.snippet, 220)}\n${article.url ? `[Read more](${article.url})` : ''}`).join('\n\n')}`;
  }
  if (mode === 'scrape') {
    const sources = data.sources || [];
    if (!sources.length) return 'No readable content could be extracted.';
    return `## Extracted content for "${query}"\n\n${sources.slice(0, 5).map((source, index) => `[${index + 1}] **${source.title || source.url || 'Untitled source'}**\n${trim(source.content, 420)}\n${source.url ? `[Source](${source.url})` : ''}`).join('\n\n')}`;
  }
  if (mode === 'analyze') {
    const points = data.key_points || [];
    const findings = data.detailed_findings || [];
    const sourceNotes = data.source_notes || [];
    const limitations = data.limitations || [];
    const researchSteps = data.research_steps || [];
    const summary = data.summary || response.answer || 'No analysis could be generated.';
    const section = (title, items) => items.length ? ['', `### ${title}`, ...items.map((item) => `- ${item}`)].join('\n') : '';
    return [
      '## Deep analysis',
      '',
      summary,
      section('Research path', researchSteps),
      section('Key takeaways', points),
      section('Detailed findings', findings),
      section('Source notes', sourceNotes),
      section('Gaps and caveats', limitations),
    ].filter(Boolean).join('\n');
  }
  return 'No response returned.';
};

export const formatPlaygroundResponse = (response) => {
  const sources = extractSources(response);
  const images = extractImages(response);
  const fallbackImages = sources.filter((source) => source.image).slice(0, 3);
  const text = response?.mode === 'analyze' ? formatRawData(response) : (response?.answer || formatRawData(response));
  return {
    text,
    sources,
    images: images.length ? images : fallbackImages,
    meta: {
      ...(response?.meta || {}),
      mode: response?.mode || 'search',
      mode_label: modeLabels[response?.mode] || response?.mode || 'Playground',
    },
    raw: response,
  };
};

export const performWebSearch = (query) => runPlaygroundQuery({ query, tool: 'search' });
export const scrapeWebContent = (query) => runPlaygroundQuery({ query, tool: 'scraper' });
export const analyzeContent = (query) => runPlaygroundQuery({ query, tool: 'analyzer' });
export const searchNews = (query) => runPlaygroundQuery({ query, tool: 'news' });
export const formatSearchResults = formatRawData;
export const formatScraperResults = formatRawData;
export const formatAnalyzerResults = formatRawData;
export const formatNewsResults = formatRawData;

export { API_CONFIG };
