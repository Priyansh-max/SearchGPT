import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatMessage from './ChatMessage';
import MessageInput from './MessageInput';
import LoadingIndicator from './LoadingIndicator';
import TypewriterBlurFade from './TypewriterBlurFade';

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
  setSelectedTool,
  onResetChat 
}) => {
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    return false;
  });

  // Sync dark class on <html> and persist
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="w-full h-screen bg-neutral-100 dark:bg-black flex flex-col">
      {/* Navbar — same width as chat content (max-w-4xl) */}
      <header className="w-full shrink-0 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-sm mb-4">
        <div className="w-full max-w-4xl mx-auto px-4 flex items-center justify-between">
          {/* Left: Home, New chat (+), temp chat indicator */}
          <div className="flex items-center gap-1 min-w-0">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-9 h-9 inline-flex items-center justify-center rounded-lg text-gray-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
              title="Home"
            >
              <span className="material-icons text-[20px] leading-none select-none">home</span>
            </button>
            <button
              type="button"
              onClick={onResetChat}
              className="w-9 h-9 inline-flex items-center justify-center rounded-lg text-gray-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
              title="New chat"
            >
              <span className="material-icons text-[20px] leading-none select-none">add</span>
            </button>
          </div>

          <div className="flex items-center justify-center flex-shrink-0">
            <h1 className="text-base text-center font-medium text-black dark:text-white">SearchGPT Agent <span className="text-xs text-gray-500 dark:text-neutral-400">Playground</span></h1>
          </div>

          {/* Right: theme toggle */}
          <button
            type="button"
            onClick={() => setIsDark(!isDark)}
            className="w-9 h-9 inline-flex items-center justify-center rounded-lg text-gray-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
            title={isDark ? 'Light mode' : 'Dark mode'}
          >
            <span className="material-icons text-[20px] leading-none select-none">{isDark ? 'light_mode' : 'dark_mode'}</span>
          </button>
        </div>
      </header>
      
      {/* Full page scrollable area */}
      <div className="flex-1 min-h-0 overflow-y-auto hide-scrollbar pb-4" style={{ paddingBottom: '180px' }}>
        <div className="flex flex-col items-center">
          <div className="w-full max-w-4xl px-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center min-h-[min(60vh,400px)] py-12">
                <TypewriterBlurFade text="How can I help you today?" />
              </div>
            ) : (
              <>
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
              </>
            )}
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