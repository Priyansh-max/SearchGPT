import React, { useRef, useEffect } from 'react';
import ToolSelection from './ToolSelection';

const MessageInput = ({ query, setQuery, handleSendMessage, handleKeyPress, selectedTool, setSelectedTool, isDisabled = false }) => {
  const textareaRef = useRef(null);
  
  // Auto-resize textarea as content changes
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 p-4 z-10">
      <div className="mx-auto max-w-4xl">
        <form onSubmit={handleSendMessage} className="flex flex-col">
          <div className="mb-3">
            <div className="flex flex-nowrap overflow-x-auto hide-scrollbar pb-2">
              <ToolSelection 
                selectedTool={selectedTool} 
                setSelectedTool={setSelectedTool}
                isDisabled={isDisabled}
              />
            </div>
          </div>
          
          <div className="flex">
            <div className={`flex-1 bg-gray-800 rounded-l-lg p-2 ${isDisabled ? 'opacity-70' : ''}`}>
              <textarea
                ref={textareaRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={isDisabled ? "Processing request..." : "What do you want to know?"}
                className="w-full bg-gray-800 border-0 text-white outline-none resize-none overflow-hidden min-h-[20px] break-words"
                rows={1}
                disabled={isDisabled}
              />
            </div>
            <button
              type="submit"
              disabled={!query.trim() || isDisabled}
              className={`px-4 rounded-r-lg bg-gray-800 flex items-center ${
                query.trim() && !isDisabled ? 'text-blue-500' : 'text-gray-600'
              } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <span className="material-icons">send</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageInput; 