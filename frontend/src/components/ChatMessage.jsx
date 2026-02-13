import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const ChatMessage = ({ message, isUser }) => {
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
          <MarkdownRenderer text={message.text} />
        )}
      </div>
    </div>
  );
};

export default ChatMessage; 