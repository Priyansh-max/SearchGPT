import React from 'react';

const MarkdownRenderer = ({ text }) => {
  if (!text) return null;

  // Function to convert markdown to HTML
  const markdownToHtml = (markdown) => {
    // Handle headers (## Header)
    let html = markdown.replace(/^### (.*$)/gm, '<h3 class="text-base font-bold mt-2 mb-2">$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-lg font-bold mt-3 mb-2">$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>');
    
    // Handle bold (**text**)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>');
    
    // Handle italic (*text*)
    html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
    
    // Handle links ([text](url))
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 dark:text-blue-400 underline hover:text-blue-600 dark:hover:text-blue-300">$1</a>');
    
    // Handle lists (- item)
    html = html.replace(/^\s*-\s*(.*?)$/gm, '<li class="mb-1">$1</li>');
    html = html.replace(/<li class="mb-1">(.*?)<\/li>/g, function(match) {
      return '<ul class="list-disc ml-5 mb-2">' + match + '</ul>';
    });
    
    // Handle line breaks
    html = html.replace(/\n/g, '<br />');
    
    // Fix nested ul tags
    html = html.replace(/<\/ul><br \/><ul class="list-disc ml-5 mb-2">/g, '');
    
    // Wrap standalone text blocks (not already in tags) in paragraphs
    // Split by block elements and wrap text segments
    const parts = html.split(/(<(?:h[1-3]|ul|li)[^>]*>.*?<\/(?:h[1-3]|ul|li)>)/g);
    html = parts.map(part => {
      if (part.match(/^<(h[1-3]|ul|li)/)) {
        return part; // Keep block elements as-is
      }
      const trimmed = part.trim();
      if (trimmed && trimmed !== '<br />') {
        return '<p class="mb-2">' + trimmed + '</p>';
      }
      return part;
    }).join('');
    
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