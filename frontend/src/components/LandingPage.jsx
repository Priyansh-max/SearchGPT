import React, { useRef, useEffect, useState } from 'react';
import ToolSelection from './ToolSelection';
import ToolDescriptionCards from './ToolDescriptionCards';

const LandingPage = ({ 
  query, 
  setQuery, 
  handleSearch, 
  handleKeyPress, 
  selectedTool, 
  setSelectedTool, 
  userName 
}) => {
  const textareaRef = useRef(null);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [showAboutModal, setShowAboutModal] = useState(false);
  
  // Auto-resize textarea as content changes
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  // Format the date and time
  const formatDate = (date) => {
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* Greeting */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-semibold mb-2">Welcome to {userName}</h1>
          <p className="text-2xl text-gray-300">How can I help you today?</p>
        </div>
        
        {/* Search Input */}
        <div className="w-full bg-gray-800 rounded-xl p-6 mb-6">
          <form onSubmit={handleSearch}>
            <textarea
              ref={textareaRef}
              placeholder="What do you want to know?"
              className="w-full bg-transparent text-xl outline-none resize-none overflow-hidden min-h-[40px] max-h-[200px]"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              rows={1}
            />
            
            {/* Tool Selection with Send button inline */}
            <div className="mt-6">
              <ToolSelection 
                selectedTool={selectedTool} 
                setSelectedTool={setSelectedTool} 
                includeSubmitButton={true} 
              />
            </div>
          </form>
        </div>
        
        {/* Tool Details */}
        <ToolDescriptionCards />
      </div>
      
      {/* About SearchGPT Footer and Server Time */}
      <div className="absolute bottom-4 flex flex-col items-center gap-2">
        <div 
          className="text-center text-gray-400 cursor-pointer hover:text-gray-300 transition-colors"
          onClick={() => setShowAboutModal(true)}
        >
          About SearchGPT
        </div>
        <div className="text-center text-gray-500 text-sm">
          Server Time: {formatDate(currentDateTime)}
        </div>
      </div>
      
      {/* About Modal */}
      {showAboutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">About SearchGPT</h2>
              <button 
                onClick={() => setShowAboutModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <span className="material-icons">close</span>
              </button>
            </div>
            
            <div className="text-gray-300 space-y-4">
              <p>
                SearchGPT is a powerful web research agent that helps you find, extract, analyze, and synthesize information from the web.
              </p>
              
              <h3 className="text-xl font-medium">Features</h3>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Web Search Tool:</strong> Search the web and retrieve relevant results</li>
                <li><strong>Web Scraper:</strong> Extract data from websites for further analysis</li>
                <li><strong>Content Analyzer:</strong> Analyze content from multiple sources to provide comprehensive answers</li>
                <li><strong>News Aggregator:</strong> Find the latest news articles on any topic</li>
              </ul>
              
              <h3 className="text-xl font-medium">How to Use</h3>
              <ol className="list-decimal pl-5 space-y-2">
                <li>Select a tool from the available options</li>
                <li>Enter your search query in the input field</li>
                <li>Click "Send" or press Ctrl+Enter to submit</li>
                <li>View the results in the chat interface</li>
              </ol>
              
              <p>
                SearchGPT uses advanced AI techniques to process your queries and construct responses in a structured manner, making it easier to find the information you need.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage; 