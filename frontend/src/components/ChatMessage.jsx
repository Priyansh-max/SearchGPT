import React, { useState } from 'react';
import MarkdownRenderer from './MarkdownRenderer';

/**
 * Remove the trailing "References" / "Sources" section from a markdown response.
 * Matches a line that is *only* the word References/Sources, in any of these forms:
 *   "## References", "### Sources", "**References**", "References:", "References"
 */
const stripReferences = (text) => {
  if (!text) return text;
  const lines = text.split('\n');
  const idx = lines.findIndex((line) => {
    const stripped = line
      .replace(/^#{1,6}\s*/, '')   // markdown heading markers
      .replace(/\*\*/g, '')         // bold markers
      .replace(/[:*\s]+$/, '')      // trailing colon/asterisk/space
      .trim()
      .toLowerCase();
    return stripped === 'references' || stripped === 'sources';
  });
  if (idx === -1) return text.trim();
  return lines.slice(0, idx).join('\n').trim();
};

const ChatMessage = ({ message, isUser }) => {
  const [copied, setCopied] = useState(null); // 'full' | 'summary' | null

  const handleCopy = async (type) => {
    const content = type === 'summary' ? stripReferences(message.text) : message.text;
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
      <div className={`max-w-[80%] rounded-lg p-2 dark:shadow-neutral-900 ${
        isUser
        ? 'bg-white dark:bg-neutral-900 dark:text-white text-black rounded-tr-none'
        : 'dark:text-white text-black rounded-tl-none'
      }`}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words overflow-hidden overflow-wrap-anywhere">{message.text}</p>
        ) : (
          <>
            <MarkdownRenderer text={message.text} />

            {/* Copy actions — AI messages only */}
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
