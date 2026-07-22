import React, { useState } from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const MODE_DETAILS = {
  search: { icon: 'travel_explore', label: 'Web Search', delivery: 'Web info with ranked sources' },
  scrape: { icon: 'data_object', label: 'Web Scrape', delivery: 'Clean extracted page content' },
  analyze: { icon: 'psychology', label: 'Deep Analysis', delivery: 'Researched synthesis with source backing' },
  news: { icon: 'newspaper', label: 'Live News', delivery: 'Current coverage across publishers' },
};

const collectScrapedImages = (sources) => sources
  .flatMap((source) => {
    const nested = Array.isArray(source.images) ? source.images : [];
    const imageRows = nested.map((image) => ({
      url: image.url || image.image || '',
      alt: image.alt || source.title || 'Scraped image',
      sourceUrl: image.source_url || source.url || '',
    }));
    if (source.image) imageRows.unshift({ url: source.image, alt: source.title || 'Scraped image', sourceUrl: source.url || '' });
    return imageRows;
  })
  .filter((image, index, all) => image.url && all.findIndex((item) => item.url === image.url) === index)
  .slice(0, 12);

const buildScrapeExport = (message, format) => {
  const sources = message.sources || [];
  if (format === 'json') {
    return JSON.stringify({ query: message.raw?.query || '', sources }, null, 2);
  }
  if (format === 'text') {
    return sources
      .map((source, index) => [
        `${index + 1}. ${source.title}`,
        source.url,
        '',
        source.content || source.snippet || '',
      ].join('\n'))
      .join('\n\n');
  }
  return sources
    .map((source, index) => [
      `## [${index + 1}] ${source.title}`,
      '',
      source.url ? `Source: ${source.url}` : '',
      '',
      source.content || source.snippet || '',
    ].filter((line, lineIndex) => line || lineIndex < 2).join('\n'))
    .join('\n\n');
};
const downloadTextFile = (filename, content, mime = 'text/plain') => {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const downloadImages = (images) => {
  images.forEach((image, index) => {
    const link = document.createElement('a');
    link.href = image.url;
    link.download = `scraped-image-${index + 1}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    link.remove();
  });
};

const stripReferences = (text) => {
  if (!text) return text;
  const lines = text.split('\n');
  const idx = lines.findIndex((line) => {
    const stripped = line
      .replace(/^#{1,6}\s*/, '')
      .replace(/\*\*/g, '')
      .replace(/[:*\s]+$/, '')
      .trim()
      .toLowerCase();
    return stripped === 'references' || stripped === 'sources';
  });
  if (idx === -1) return text.trim();
  return lines.slice(0, idx).join('\n').trim();
};

const ChatMessage = ({ message, isUser }) => {
  const [copied, setCopied] = useState(null);
  const sources = message.sources || [];
  const topImages = message.images || [];
  const mode = message.meta?.mode || message.raw?.mode || 'search';
  const modeDetails = MODE_DETAILS[mode] || MODE_DETAILS.search;
  const scrapedImages = mode === 'scrape' ? collectScrapedImages(sources) : [];

  const handleCopy = async (type) => {
    let content = type === 'summary' ? stripReferences(message.text) : message.text;
    if (type === 'scrape-json') content = buildScrapeExport(message, 'json');
    if (type === 'scrape-markdown') content = buildScrapeExport(message, 'markdown');
    if (type === 'scrape-text') content = buildScrapeExport(message, 'text');
    try {
      await navigator.clipboard.writeText(content);
      setCopied(type);
      setTimeout(() => setCopied(null), 1500);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[86%] rounded-lg p-3 dark:shadow-neutral-900 ${
        isUser
          ? 'bg-white dark:bg-neutral-900 dark:text-white text-black rounded-tr-none'
          : 'dark:text-white text-black rounded-tl-none'
      }`}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words overflow-hidden overflow-wrap-anywhere">{message.text}</p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-neutral-400">
              <span className="inline-flex items-center gap-1.5 font-medium text-gray-800 dark:text-neutral-100">
                <span className="material-icons text-[15px] leading-none">{modeDetails.icon}</span>
                {modeDetails.label}
              </span>
              <span className="h-1 w-1 rounded-full bg-gray-300 dark:bg-neutral-700" />
              <span>{modeDetails.delivery}</span>
              {sources.length > 0 && (
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-neutral-900 dark:text-neutral-300">
                  {sources.length} sources
                </span>
              )}
            </div>

            {topImages.length > 0 && (
              <div className="mb-4 grid grid-cols-1 gap-2 overflow-hidden rounded-lg border border-gray-200 bg-gray-100 dark:border-neutral-800 dark:bg-neutral-900 sm:grid-cols-3">
                {topImages.slice(0, 3).map((image, index) => (
                  <a
                    key={`${image.image}-${index}`}
                    href={image.url || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group relative block aspect-[16/10] min-w-0 overflow-hidden bg-gray-100 dark:bg-neutral-900"
                  >
                    <img
                      src={image.image}
                      alt={image.title}
                      loading="lazy"
                      onError={(event) => {
                        if (image.thumbnail && event.currentTarget.src !== image.thumbnail) {
                          event.currentTarget.src = image.thumbnail;
                          return;
                        }
                        event.currentTarget.closest('a').style.display = 'none';
                      }}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
                    />
                    {(image.domain || image.source) && (
                      <span className="absolute bottom-1 left-1 max-w-[calc(100%-0.5rem)] truncate rounded bg-black/65 px-1.5 py-0.5 text-[10px] font-medium text-white backdrop-blur">
                        {image.domain || image.source}
                      </span>
                    )}
                  </a>
                ))}
              </div>
            )}

            <MarkdownRenderer text={message.text} />

            {mode === 'scrape' && sources.length > 0 && (
              <div className="mt-4 space-y-3 border-t border-gray-200 pt-3 dark:border-neutral-800">
                <div className="flex flex-wrap items-center gap-2">
                  <button type="button" onClick={() => handleCopy('scrape-markdown')} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                    <span className="material-icons text-[14px]">content_copy</span> Markdown
                  </button>
                  <button type="button" onClick={() => handleCopy('scrape-json')} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                    <span className="material-icons text-[14px]">data_object</span> JSON
                  </button>
                  <button type="button" onClick={() => handleCopy('scrape-text')} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                    <span className="material-icons text-[14px]">notes</span> Text
                  </button>
                  <button type="button" onClick={() => downloadTextFile('scrape-output.md', buildScrapeExport(message, 'markdown'), 'text/markdown')} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                    <span className="material-icons text-[14px]">download</span> MD
                  </button>
                  <button type="button" onClick={() => downloadTextFile('scrape-output.json', buildScrapeExport(message, 'json'), 'application/json')} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                    <span className="material-icons text-[14px]">download</span> JSON
                  </button>
                  {scrapedImages.length > 0 && (
                    <button type="button" onClick={() => downloadImages(scrapedImages)} className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:text-black dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white">
                      <span className="material-icons text-[14px]">image</span> Images
                    </button>
                  )}
                </div>
                {scrapedImages.length > 0 && (
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                    {scrapedImages.slice(0, 6).map((image, index) => (
                      <a key={`${image.url}-${index}`} href={image.url} target="_blank" rel="noopener noreferrer" download className="group block aspect-square overflow-hidden rounded-md bg-gray-100 dark:bg-neutral-900" title="Open scraped image">
                        <img src={image.url} alt={image.alt} loading="lazy" className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.04]" />
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}


            {sources.length > 0 && (
              <div className="mt-4 border-t border-gray-200 pt-3 dark:border-neutral-800">
                <div className="mb-2 text-xs font-semibold text-gray-500 dark:text-neutral-400">References</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {sources.slice(0, 6).map((source, index) => (
                    <a
                      key={`${source.url || source.title}-${index}`}
                      href={source.url || undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex min-w-0 gap-2 rounded-md px-1 py-1.5 hover:bg-gray-50 dark:hover:bg-neutral-900"
                    >
                      <span className="mt-0.5 shrink-0 text-[11px] font-semibold text-gray-700 dark:text-neutral-200">[{source.ref || index + 1}]</span>
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center overflow-hidden rounded">
                        {source.favicon ? <img src={source.favicon} alt="" className="h-4 w-4" /> : <span className="material-icons text-[14px] text-gray-400">link</span>}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-xs font-medium text-black dark:text-white">{source.title}</span>
                        <span className="mt-0.5 block truncate text-[11px] text-gray-500 dark:text-neutral-400">{source.domain || source.url}</span>
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-3 mt-2 pt-1">
              <button
                type="button"
                onClick={() => handleCopy('full')}
                className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
                title="Copy the complete response"
              >
                <span className="material-icons text-[15px] leading-none select-none">
                  {copied === 'full' ? 'check' : 'content_copy'}
                </span>
                {copied === 'full' ? 'Copied' : 'Copy response'}
              </button>
              <button
                type="button"
                onClick={() => handleCopy('summary')}
                className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
                title="Copy the summary without the references section"
              >
                <span className="material-icons text-[15px] leading-none select-none">
                  {copied === 'summary' ? 'check' : 'notes'}
                </span>
                {copied === 'summary' ? 'Copied' : 'Copy summary'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
