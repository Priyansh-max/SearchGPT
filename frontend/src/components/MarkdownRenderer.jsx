import React from 'react';

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const highlightCode = (code, language = '') => {
  const lang = language.toLowerCase();
  let html = escapeHtml(code);

  if (lang === 'json') {
    return html
      .replace(/(&quot;[^&]*?&quot;)\s*:/g, '<span class="text-sky-300">$1</span>:')
      .replace(/:\s*(&quot;.*?&quot;)/g, ': <span class="text-emerald-300">$1</span>')
      .replace(/\b(true|false|null)\b/g, '<span class="text-purple-300">$1</span>')
      .replace(/\b(-?\d+(?:\.\d+)?)\b/g, '<span class="text-amber-300">$1</span>');
  }

  const keywords = lang === 'python'
    ? ['async', 'await', 'def', 'class', 'return', 'import', 'from', 'for', 'in', 'if', 'elif', 'else', 'try', 'except', 'with', 'as', 'None', 'True', 'False']
    : ['const', 'let', 'var', 'function', 'return', 'import', 'from', 'export', 'async', 'await', 'if', 'else', 'for', 'while', 'try', 'catch', 'new', 'class', 'true', 'false', 'null'];

  html = html.replace(/(#.*$|\/\/.*$)/gm, '<span class="text-neutral-500">$1</span>');
  html = html.replace(/(&quot;.*?&quot;|&#39;.*?&#39;|`.*?`)/g, '<span class="text-emerald-300">$1</span>');
  html = html.replace(new RegExp(`\\b(${keywords.join('|')})\\b`, 'g'), '<span class="text-purple-300">$1</span>');
  html = html.replace(/\b(-?\d+(?:\.\d+)?)\b/g, '<span class="text-amber-300">$1</span>');
  return html;
};

const renderCodeBlock = (code, language) => {
  const label = language || 'code';
  return `<div class="my-3 overflow-hidden rounded-lg border border-neutral-800 bg-[#0b0f14] text-sm shadow-sm">
    <div class="flex items-center justify-between border-b border-neutral-800 px-3 py-1.5 text-[11px] font-medium uppercase tracking-wide text-neutral-400">
      <span>${escapeHtml(label)}</span>
    </div>
    <pre class="overflow-x-auto p-3 text-[13px] leading-relaxed text-neutral-100"><code class="language-${escapeHtml(language)}">${highlightCode(code, language)}</code></pre>
  </div>`;
};

const MarkdownRenderer = ({ text }) => {
  if (!text) return null;

  const markdownToHtml = (markdown) => {
    const codeBlocks = [];
    let html = String(markdown).replace(/```(\w+)?\n([\s\S]*?)```/g, (_, language = '', code = '') => {
      const token = `@@CODE_BLOCK_${codeBlocks.length}@@`;
      codeBlocks.push(renderCodeBlock(code.trimEnd(), language));
      return token;
    });

    html = escapeHtml(html);

    html = html.replace(/^### (.*$)/gm, '<h3 class="text-base font-bold mt-2 mb-2">$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-lg font-bold mt-3 mb-2">$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>');
    html = html.replace(/`([^`]+)`/g, '<code class="rounded bg-gray-100 px-1 py-0.5 text-[12px] text-gray-900 dark:bg-neutral-900 dark:text-neutral-100">$1</code>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
    html = html.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 dark:text-blue-400 underline hover:text-blue-600 dark:hover:text-blue-300">$1</a>');
    html = html.replace(/(^|[^\w])\[(\d{1,2})\](?!\()/g, '$1<sup class="citation-pill inline-flex translate-y-[-1px] rounded bg-gray-100 px-1 text-[10px] font-semibold text-gray-700 dark:bg-neutral-800 dark:text-neutral-200">[$2]</sup>');
    html = html.replace(/^\s*-\s*(.*?)$/gm, '<li class="mb-1">$1</li>');
    html = html.replace(/<li class="mb-1">(.*?)<\/li>/g, '<ul class="list-disc ml-5 mb-2"><li class="mb-1">$1</li></ul>');
    html = html.replace(/\n/g, '<br />');
    html = html.replace(/<\/ul><br \/><ul class="list-disc ml-5 mb-2">/g, '');

    const parts = html.split(/(<(?:h[1-3]|ul|div)[^>]*>[\s\S]*?<\/(?:h[1-3]|ul|div)>|@@CODE_BLOCK_\d+@@)/g);
    html = parts.map((part) => {
      const codeMatch = part.match(/^@@CODE_BLOCK_(\d+)@@$/);
      if (codeMatch) return codeBlocks[Number(codeMatch[1])] || '';
      if (part.match(/^<(h[1-3]|ul|div)/)) return part;
      const trimmed = part.trim();
      if (trimmed && trimmed !== '<br />') return `<p class="mb-2">${trimmed}</p>`;
      return part;
    }).join('');

    codeBlocks.forEach((block, index) => {
      html = html.replace(`@@CODE_BLOCK_${index}@@`, block);
    });
    return html;
  };

  return (
    <div
      className="w-full break-words overflow-wrap-anywhere text-sm dark:prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: markdownToHtml(text) }}
    />
  );
};

export default MarkdownRenderer;
