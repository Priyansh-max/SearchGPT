/**
 * API service for communicating with the backend
 */
import { API_CONFIG } from '../config';

// Get the base URL from configuration
const API_BASE_URL = API_CONFIG.BASE_URL;

/**
 * Perform a web search
 * @param {string} query - The search query
 * @returns {Promise} - The search results
 */
export const performWebSearch = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.SEARCH}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, tool: 'search', use_llm: true }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Web search error:', error);
    throw error;
  }
};

/**
 * Scrape web content based on a query
 * @param {string} query - The search query
 * @returns {Promise} - The scraped content
 */
export const scrapeWebContent = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.SCRAPE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, tool: 'scraper', use_llm: true }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Web scraping error:', error);
    throw error;
  }
};

/**
 * Analyze content based on a query
 * @param {string} query - The search query
 * @returns {Promise} - The analysis results
 */
export const analyzeContent = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.ANALYZE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, tool: 'analyzer', use_llm: true }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Content analysis error:', error);
    throw error;
  }
};

/**
 * Search for news based on a query
 * @param {string} query - The search query
 * @returns {Promise} - The news results
 */
export const searchNews = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.NEWS}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, tool: 'news', use_llm: true }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('News search error:', error);
    throw error;
  }
};

/**
 * Format search results to a readable message
 * @param {Object} results - The search results from the API
 * @returns {string} - Formatted text
 */
export const formatSearchResults = (results) => {
  // Use the LLM-generated response if available
  if (results.llm_response) {
    // Add a note about the refined query if it differs from the original
    if (results.refined_query && results.refined_query !== results.query) {
      return `${results.llm_response}\n\n*Search was optimized using: "${results.refined_query}"*`;
    }
    return results.llm_response;
  }

  // Fallback to traditional formatting
  if (!results || !results.results || results.results.length === 0) {
    return "No search results found.";
  }

  const formattedResults = results.results.map((result, index) => {
    return `${index + 1}. **${result.title}**\n   ${result.snippet}\n   [Link](${result.url})\n`;
  }).join('\n');

  return `Here are the search results for "${results.query}":\n\n${formattedResults}`;
};

/**
 * Format scraper results to a readable message
 * @param {Object} results - The scraper results from the API
 * @returns {string} - Formatted text
 */
export const formatScraperResults = (results) => {
  // Use the LLM-generated response if available
  if (results.llm_response) {
    // Add a note about the refined query if it differs from the original
    if (results.refined_query && results.refined_query !== results.query) {
      return `${results.llm_response}\n\n*Search was optimized using: "${results.refined_query}"*`;
    }
    return results.llm_response;
  }

  // Fallback to traditional formatting
  if (!results || !results.results || results.results.length === 0) {
    return "No content could be scraped.";
  }

  const formattedResults = results.results.map((result, index) => {
    // Truncate content if it's too long
    const content = result.content.length > 500 
      ? result.content.substring(0, 500) + '...' 
      : result.content;
      
    return `${index + 1}. **${result.title}**\n   Source: ${result.url}\n\n   ${content}\n`;
  }).join('\n');

  return `Here's the content I scraped for "${results.query}":\n\n${formattedResults}`;
};

/**
 * Format analyzer results to a readable message
 * @param {Object} results - The analyzer results from the API
 * @returns {string} - Formatted text
 */
export const formatAnalyzerResults = (results) => {
  if (!results || !results.result) {
    return "No analysis could be generated.";
  }

  // We don't use llm_response directly for analyzer as it's already integrated into the result

  const { summary, key_points, sources } = results.result;
  
  let formatted = `## Analysis for "${results.query}"\n\n`;
  
  // Add refined query note if applicable
  if (results.refined_query && results.refined_query !== results.query) {
    formatted += `*Analysis was based on the optimized search: "${results.refined_query}"*\n\n`;
  }
  
  // Add summary
  formatted += `### Summary\n${summary}\n\n`;
  
  // Add key points if available
  if (key_points && key_points.length > 0) {
    formatted += '### Key Points\n';
    formatted += key_points.map(point => `- ${point}`).join('\n');
    formatted += '\n\n';
  }
  
  // Add sources if available
  if (sources && sources.length > 0) {
    formatted += '### Sources\n';
    formatted += sources.map((source, index) => 
      `${index + 1}. [${source.title}](${source.url})`
    ).join('\n');
  }
  
  return formatted;
};

/**
 * Format news results to a readable message
 * @param {Object} results - The news results from the API
 * @returns {string} - Formatted text
 */
export const formatNewsResults = (results) => {
  // Use the LLM-generated response if available
  if (results.llm_response) {
    // Add a note about the refined query if it differs from the original
    if (results.refined_query && results.refined_query !== results.query) {
      return `${results.llm_response}\n\n*Search was optimized using: "${results.refined_query}"*`;
    }
    return results.llm_response;
  }

  // Fallback to traditional formatting
  if (!results || !results.results || results.results.length === 0) {
    return "No news articles found.";
  }

  const formattedResults = results.results.map((article, index) => {
    const date = article.published_date ? new Date(article.published_date).toLocaleDateString() : 'Unknown date';
    return `${index + 1}. **${article.title}**\n   *${article.source}* | ${date}\n   ${article.snippet}\n   [Read more](${article.url})\n`;
  }).join('\n');

  return `Here are the latest news articles for "${results.query}":\n\n${formattedResults}`;
}; 