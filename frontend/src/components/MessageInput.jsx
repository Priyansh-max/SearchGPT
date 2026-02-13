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
    <div className="fixed bottom-0 left-0 right-0 bg-neutral-100 dark:bg-black border-t border-gray-200 dark:border-white/10 p-4 pb-4 z-10">
      <div className="mx-auto max-w-4xl">
        <form onSubmit={handleSendMessage} className="flex flex-col">
          <div className="border-2 border-gray-200 dark:border-neutral-800 rounded-lg p-4 shadow-lg dark:shadow-neutral-900 bg-white/10 dark:bg-white/5">
            <textarea
              ref={textareaRef}
              placeholder="Ask Anything"
              className="w-full h-auto bg-transparent text-md text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-neutral-400  outline-none resize-none overflow-hidden min-h-[40px] max-h-[100px]"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              rows={1}
            />

                
                {/* Tool Selection with Send button inline */}
            <div className="border-t border-gray-200 dark:border-neutral-800 pt-4">
              <ToolSelection 
                selectedTool={selectedTool} 
                setSelectedTool={setSelectedTool} 
                includeSubmitButton={true}
                isDisabled={isDisabled}
              />
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageInput; 