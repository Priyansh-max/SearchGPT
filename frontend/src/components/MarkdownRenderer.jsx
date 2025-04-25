import React from 'react';

const MarkdownRenderer = ({ text }) => {
  if (!text) return null;

  // Function to convert markdown to HTML
  const markdownToHtml = (markdown) => {
    // Handle headers (## Header)
    let html = markdown.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Handle bold (**text**)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic (*text*)
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle links ([text](url))
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 underline">$1</a>');
    
    // Handle lists (- item)
    html = html.replace(/^\s*-\s*(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/<li>(.*?)<\/li>/g, function(match) {
      return '<ul class="list-disc ml-5 mb-2">' + match + '</ul>';
    });
    
    // Handle line breaks
    html = html.replace(/\n/g, '<br />');
    
    // Fix nested ul tags
    html = html.replace(/<\/ul><br \/><ul class="list-disc ml-5 mb-2">/g, '');
    
    return html;
  };

  return (
    <div 
      className="markdown-content" 
      dangerouslySetInnerHTML={{ __html: markdownToHtml(text) }}
    />
  );
};

export default MarkdownRenderer; 