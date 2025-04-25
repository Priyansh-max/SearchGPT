import React from 'react';

const ToolDescriptionCards = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-300">
    <div className="bg-gray-800 p-4 rounded-lg">
      <div className="flex items-center mb-2">
        <span className="material-icons mr-2">search</span>
        <h3 className="font-medium">Web Search Tool</h3>
      </div>
      <p>Performs search queries and returns links and snippets</p>
    </div>
    
    <div className="bg-gray-800 p-4 rounded-lg">
      <div className="flex items-center mb-2">
        <span className="material-icons mr-2">code</span>
        <h3 className="font-medium">Web Scraper/Crawler</h3>
      </div>
      <p>Extracts text, structured data, and other relevant information from web pages</p>
    </div>
    
    <div className="bg-gray-800 p-4 rounded-lg">
      <div className="flex items-center mb-2">
        <span className="material-icons mr-2">analytics</span>
        <h3 className="font-medium">Content Analyzer</h3>
      </div>
      <p>Processes and analyzes extracted content for relevance and reliability</p>
    </div>
    
    <div className="bg-gray-800 p-4 rounded-lg">
      <div className="flex items-center mb-2">
        <span className="material-icons mr-2">newspaper</span>
        <h3 className="font-medium">News Aggregator</h3>
      </div>
      <p>Finds and filters recent news articles on specific topics</p>
    </div>
  </div>
);

export default ToolDescriptionCards; 