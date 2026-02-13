import React, { useState } from 'react';
import './App.css';
import LandingPage from './components/LandingPage';
import ChatInterface from './components/ChatInterface';
import { 
  performWebSearch, 
  scrapeWebContent, 
  analyzeContent, 
  searchNews,
  formatSearchResults,
  formatScraperResults,
  formatAnalyzerResults,
  formatNewsResults
} from './services/api';

function App() {
  // State management
  const [query, setQuery] = useState('');
  const [selectedTool, setSelectedTool] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState("");
  
  // Mock user name - can be replaced with actual user info from auth system
  const userName = "SearchGPT";
  
  // Handle initial search from landing page
  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    sendMessage(query);
  };
  
  // Handle sending messages from chat page
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    sendMessage(query);
  };
  
  // Handle key press in textarea
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        return;
      } else {
        e.preventDefault(); // prevent newline
        if (query.trim()) {
          sendMessage(query);
        }
      }
    }
  };
  
  
  // Common message sending logic
  const sendMessage = async (text) => {
    // Add user message
    const userMessage = { 
      id: Date.now(), 
      text: text, 
      isUser: true
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Show typing indicator and set loading state
    setIsTyping(true);
    setIsLoading(true);
    setLoadingStartTime(Date.now());
    
    try {
      // Choose API based on selected tool
      let response;
      let formattedResponse;
      
      if (selectedTool === 'search') {
        setLoadingMessage("Searching the web");
        response = await performWebSearch(text);
        formattedResponse = formatSearchResults(response);
      } else if (selectedTool === 'scraper') {
        setLoadingMessage("Extracting content from web pages");
        response = await scrapeWebContent(text);
        formattedResponse = formatScraperResults(response);
      } else if (selectedTool === 'analyzer') {
        setLoadingMessage("Analyzing content from multiple sources on the internet");
        response = await analyzeContent(text);
        formattedResponse = formatAnalyzerResults(response);
      } else if (selectedTool === 'news') {
        setLoadingMessage("Searching for news articles");
        response = await searchNews(text);
        formattedResponse = formatNewsResults(response);
      } else {
        // If no tool selected, provide a general response
        setLoadingMessage("Processing your request");

        //add a delay of 4 seconds before showing the loading message
        const number = Math.random() * (3-1) + 1;
        console.log(number);
        await new Promise(resolve => setTimeout(resolve, number * 1000));

        formattedResponse = getDefaultResponse(text);
      }
      
      // Add AI response
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        text: formattedResponse,
        isUser: false
      }]);
      
    } catch (error) {
      console.error('API error:', error);
      
      // Add error message
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        text: `I encountered an error while processing your request. Please try again or select a different tool.\n\nError details: ${error.message}`,
        isUser: false
      }]);
    } finally {
      // Hide typing indicator and loading state
      setIsTyping(false);
      setIsLoading(false);
      setLoadingStartTime(null);
      setLoadingMessage("");
      
      // Clear the input
      setQuery('');
    }
  };
  
  // Default response when no tool is selected
  const getDefaultResponse = (userText) => {
    if (userText.toLowerCase().includes('search the web')) {
      return "Yes I can search the web for you, Please select a tool and put on your requirements";
    } else if (userText.toLowerCase().includes('hello') || userText.toLowerCase().includes('hi')) {
      return "Hello! How can I help you today with web research?";
    } else {
      return "I am just a web research agent. I can't do general conversations at the moment.\nI can help you research things on the web. Select a tools as per your requirement and I will help you.\n\n- Web Search Tool: For general search queries\n- Web Scraper: To extract data from specific websites\n- Content Analyzer: To analyze content for relevance and reliability\n- News Aggregator: To find recent news on your topic";
    }
  };

  return (
    <div className="min-h-screen">
      {messages.length === 0 ? (
        <LandingPage
          query={query}
          setQuery={setQuery}
          handleSearch={handleSearch}
          handleKeyPress={handleKeyPress}
          selectedTool={selectedTool}
          setSelectedTool={setSelectedTool}
          userName={userName}
        />
      ) : (
        <ChatInterface
          messages={messages}
          isTyping={isTyping}
          isLoading={isLoading}
          loadingStartTime={loadingStartTime}
          loadingMessage={loadingMessage}
          query={query}
          setQuery={setQuery}
          handleSendMessage={handleSendMessage}
          handleKeyPress={handleKeyPress}
          selectedTool={selectedTool}
          setSelectedTool={setSelectedTool}
        />
      )}
    </div>
  );
}

export default App;
