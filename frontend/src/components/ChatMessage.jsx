import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const ChatMessage = ({ message, isUser }) => {
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-lg p-4 ${
        isUser 
        ? 'bg-blue-600 text-white rounded-tr-none' 
        : 'bg-gray-800 text-white rounded-tl-none'
      }`}>
        {isUser ? (
          <p className="whitespace-pre-wrap break-words overflow-hidden overflow-wrap-anywhere">{message.text}</p>
        ) : (
          <MarkdownRenderer text={message.text} />
        )}
      </div>
    </div>
  );
};

export default ChatMessage; 