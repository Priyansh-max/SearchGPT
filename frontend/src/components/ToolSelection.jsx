import React from 'react';

const ToolSelection = ({ selectedTool, setSelectedTool, includeSubmitButton = false, isDisabled = false }) => (
  <div className="flex flex-wrap gap-2 items-center">
    <button 
      type="button"
      className={`flex items-center px-4 py-2 rounded-full border border-gray-600 ${
        selectedTool === 'search' ? 'bg-gray-600' : 'hover:bg-gray-700'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('search')}
      disabled={isDisabled}
    >
      <span className="material-icons mr-2">search</span> Web Search
    </button>
    
    <button 
      type="button"
      className={`flex items-center px-4 py-2 rounded-full border border-gray-600 ${
        selectedTool === 'scraper' ? 'bg-gray-600' : 'hover:bg-gray-700'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('scraper')}
      disabled={isDisabled}
    >
      <span className="material-icons mr-2">code</span> Web Scraper
    </button>
    
    <button 
      type="button"
      className={`flex items-center px-4 py-2 rounded-full border border-gray-600 ${
        selectedTool === 'analyzer' ? 'bg-gray-600' : 'hover:bg-gray-700'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('analyzer')}
      disabled={isDisabled}
    >
      <span className="material-icons mr-2">analytics</span> Content Analyzer
    </button>
    
    <button 
      type="button"
      className={`flex items-center px-4 py-2 rounded-full border border-gray-600 ${
        selectedTool === 'news' ? 'bg-gray-600' : 'hover:bg-gray-700'
      } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
      onClick={() => !isDisabled && setSelectedTool('news')}
      disabled={isDisabled}
    >
      <span className="material-icons mr-2">newspaper</span> News Aggregator
    </button>
    
    {includeSubmitButton && (
      <button 
        type="submit"
        className={`ml-auto flex items-center px-4 py-2 rounded-full bg-blue-600 hover:bg-blue-700 ${
          isDisabled ? 'opacity-70 cursor-not-allowed' : ''
        }`}
        disabled={isDisabled}
      >
        <span className="material-icons mr-2">send</span> Send
      </button>
    )}
  </div>
);

export default ToolSelection; 