/**
 * Application configuration
 */

// API configuration
export const API_CONFIG = {
  // Base URL for API requests - change for different environments
  BASE_URL: 'https://searchgpt-nb8h.onrender.com/api',
  
  // Timeout for API requests in milliseconds
  TIMEOUT: 60000, // 60 seconds
  
  // Define API endpoints
  ENDPOINTS: {
    SEARCH: '/search',
    SCRAPE: '/scrape',
    ANALYZE: '/analyze',
    NEWS: '/news',
    QUERY: '/query'
  }
};

// UI configuration
export const UI_CONFIG = {
  // Default tool descriptions
  TOOL_DESCRIPTIONS: {
    search: "Search the web and retrieve relevant results",
    scraper: "Extract data from websites for further analysis",
    analyzer: "Analyze content from multiple sources to provide a comprehensive answer",
    news: "Find the latest news articles on any topic"
  },
  
  // Max message length to display before truncating
  MAX_MESSAGE_PREVIEW_LENGTH: 300
}; 