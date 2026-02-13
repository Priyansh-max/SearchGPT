import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import MessageInput from './MessageInput';
import LoadingIndicator from './LoadingIndicator';

const ChatInterface = ({ 
  messages, 
  isTyping, 
  isLoading,
  loadingStartTime,
  loadingMessage,
  query, 
  setQuery, 
  handleSendMessage, 
  handleKeyPress, 
  selectedTool, 
  setSelectedTool 
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-screen bg-neutral-100 dark:bg-black">
      {/* Header make this clickable and redirect to home page*/}
      <header className="bg-white/10 dark:bg-neutral-900 py-2 px-4 shadow-md mb-4 cursor-pointer" onClick={() => window.location.href = '/'}>
        <h1 className="text-base text-center font-medium text-black dark:text-white">SearchGPT Agent</h1>
      </header>
      
      {/* Full page scrollable area */}
      <div className="flex-1 overflow-y-auto hide-scrollbar pb-4" style={{ paddingBottom: '180px' }}>
        <div className="flex flex-col items-center">
          <div className="w-full max-w-4xl px-4">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                isUser={message.isUser}
              />
            ))}
            
            {/* Loading indicator inline within chat */}
            {isLoading && loadingStartTime && (
              <LoadingIndicator 
                startTime={loadingStartTime} 
                message={loadingMessage}
              />
            )}
            
            {/* Typing indicator (bouncing dots) - only show when not loading */}
            {isTyping && !isLoading && (
              <div className="flex w-full mb-4 justify-start">
                <div className="bg-white dark:bg-neutral-900 dark:text-white text-black rounded-lg rounded-tl-none p-2">
                  <div className="flex space-x-2">
                    <div className="w-1 h-1 rounded-full bg-gray-300 animate-bounce"></div>
                    <div className="w-1 h-1 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1 h-1 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>
      
      <MessageInput 
        query={query}
        setQuery={setQuery}
        handleSendMessage={handleSendMessage}
        handleKeyPress={handleKeyPress}
        selectedTool={selectedTool}
        setSelectedTool={setSelectedTool}
        isDisabled={isLoading} // Keep input disabled while loading
      />
    </div>
  );
};

export default ChatInterface; 