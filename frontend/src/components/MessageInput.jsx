import React, { useRef, useEffect } from 'react';
import ToolSelection from './ToolSelection';

// Detect http(s) links in the input (Problem 6) — when present we read those pages
// directly instead of running a web search.
const URL_RE = /https?:\/\/[^\s]+/gi;

const renderHighlightedQuery = (value) => {
  if (!value) return null;
  const parts = [];
  let lastIndex = 0;
  const matcher = new RegExp(URL_RE.source, 'gi');
  let match;
  while ((match = matcher.exec(value)) !== null) {
    if (match.index > lastIndex) parts.push({ text: value.slice(lastIndex, match.index), link: false });
    parts.push({ text: match[0], link: true });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < value.length) parts.push({ text: value.slice(lastIndex), link: false });
  return parts.map((part, index) => (
    <span key={`${part.text}-${index}`} className={part.link ? 'text-blue-600 dark:text-blue-300 underline decoration-blue-400/60 underline-offset-2' : 'text-gray-800 dark:text-gray-100'}>
      {part.text}
    </span>
  ));
};

const MessageInput = ({ query, setQuery, handleSendMessage, handleKeyPress, selectedTool, setSelectedTool, isDisabled = false }) => {
  const textareaRef = useRef(null);
  const detectedUrls = (query.match(URL_RE) || []).slice(0, 5);

  // Auto-resize textarea as content changes
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-neutral-100 dark:bg-black border-t border-gray-200 dark:border-white/10 p-4 pb-4 z-10">
      <div className="mx-auto max-w-4xl">
        <form onSubmit={handleSendMessage} className="flex flex-col">
          <div className="border-2 border-gray-200 dark:border-neutral-800 rounded-lg p-4 shadow-lg dark:shadow-neutral-900 bg-white/10 dark:bg-white/5">
            <div className="relative min-h-[40px]">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 whitespace-pre-wrap break-words text-md leading-normal overflow-hidden"
              >
                {renderHighlightedQuery(query)}
              </div>
              <textarea
                ref={textareaRef}
                placeholder="Ask Anything"
                className={`relative z-10 w-full h-auto bg-transparent text-md leading-normal outline-none resize-none overflow-hidden min-h-[40px] max-h-[100px] caret-gray-900 dark:caret-white ${
                  query
                    ? 'text-transparent placeholder-gray-500 dark:placeholder-neutral-400'
                    : isDisabled
                      ? 'text-gray-400 dark:text-neutral-500 placeholder-gray-400 dark:placeholder-neutral-600 cursor-not-allowed'
                      : 'text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-neutral-400'
                }`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                rows={1}
                disabled={isDisabled}
              />
            </div>

            {/* Link-mode chips — shown when the query contains URLs (Problem 6) */}
            {detectedUrls.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {detectedUrls.map((u, i) => (
                  <span
                    key={i}
                    title={u}
                    className="inline-flex items-center gap-1 max-w-[260px] truncate text-xs px-2 py-1 rounded-full border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-300"
                  >
                    <span className="material-icons text-[14px] leading-none select-none">link</span>
                    Reading this link
                  </span>
                ))}
              </div>
            )}

                {/* Tool Selection with Send button inline */}
            <div className="border-t border-gray-200 dark:border-neutral-800 pt-4">
              <ToolSelection 
                selectedTool={selectedTool} 
                setSelectedTool={setSelectedTool} 
                includeSubmitButton={true}
                isDisabled={isDisabled}
                dropdownDirection="up"
              />
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageInput; 