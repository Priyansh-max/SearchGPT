import React from 'react';

const ToolSelection = ({ selectedTool, setSelectedTool, includeSubmitButton = false, isDisabled = false }) => (
  <div className="flex flex-wrap gap-2 items-center">
    <button 
      type="button"
      className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
        selectedTool === 'search' 
          ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
          : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('search')}
      disabled={isDisabled}
    >
      <span className="material-icons text-sm mr-2">search</span> Web Search
    </button>
    
    <button 
      type="button"
      className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
        selectedTool === 'scraper' 
          ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
          : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('scraper')}
      disabled={isDisabled}
    >
      <span className="material-icons text-sm mr-2">code</span> Web Scraper
    </button>
    
    <button 
      type="button"
      className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
        selectedTool === 'analyzer' 
          ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
          : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('analyzer')}
      disabled={isDisabled}
    >
      <span className="material-icons text-sm mr-2">analytics</span> Content Analyzer
    </button>
    
    <button 
      type="button"
      className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
        selectedTool === 'news' 
          ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
          : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('news')}
      disabled={isDisabled}
    >
      <span className="material-icons text-sm mr-2">newspaper</span> News Aggregator
    </button>
    
    {includeSubmitButton && (
      <button 
        type="submit"
        className={`ml-auto flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          isDisabled 
            ? 'opacity-70 cursor-not-allowed bg-gray-100 border-gray-300 text-gray-400 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-600' 
            : 'bg-gray-800 text-white border-gray-900 hover:bg-gray-800 dark:bg-neutral-100 dark:text-gray-900 dark:border-white dark:hover:bg-gray-200'
        }`}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">send</span> Send
      </button>
    )}
  </div>
);

export default ToolSelection; 