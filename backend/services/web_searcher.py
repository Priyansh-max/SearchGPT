import logging
import asyncio
import re
from typing import List, Dict, Any
from pydantic import BaseModel

from utils.selenium_utils import browser
from config import settings

logger = logging.getLogger(__name__)

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    position: int

class WebSearcher:
    """
    Service to search the web using Google
    """
    
    def __init__(self):
        pass
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the web using Google and return results
        """
        if not query:
            return []
            
        try:
            logger.info(f"Searching for: {query}")
            
            # Perform Google search
            search_results = await browser.search_google(query)
            
            # Convert to standardized format
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.get("title", "No title"),
                    "snippet": result.get("snippet", "No description available"),
                    "url": result.get("url", ""),
                    "position": result.get("position", 0)
                })
                
            logger.info(f"Found {len(formatted_results)} search results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching the web: {str(e)}")
            return []
            
    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for a query
        NOTE: This would be better implemented using an API, but
        this shows how to extract auto-suggestions using Selenium as a fallback
        """
        if not query:
            return []
            
        try:
            # Navigate to Google
            await browser.navigate("https://www.google.com")
            
            # Input the query but don't submit
            search_box = browser.driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys(query)
            
            # Wait for suggestions to appear
            await asyncio.sleep(1)
            
            # Get suggestions
            suggestions = []
            try:
                suggestion_elements = browser.driver.find_elements_by_css_selector("li.sbct")
                for element in suggestion_elements:
                    text_element = element.find_element_by_css_selector("div.wM6W7d")
                    if text_element:
                        suggestions.append(text_element.text)
            except Exception as e:
                logger.warning(f"Error extracting suggestions: {str(e)}")
                
            return suggestions
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []
    
    async def extract_urls_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract URLs from search results
        """
        return [result["url"] for result in results if result.get("url")]
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and allowed
        """
        if not url:
            return False
            
        # Check for common valid URL patterns
        if not re.match(r'^https?://', url):
            return False
            
        # Check for disallowed domains (common SEO spam, etc.)
        disallowed_domains = [
            'pinterest.com',  # Often not helpful for information
            'quora.com',      # Requires login
            'reddit.com',     # Often not structured well for scraping
            'facebook.com',   # Social media
            'twitter.com',    # Social media
            'instagram.com',  # Social media
        ]
        
        for domain in disallowed_domains:
            if domain in url:
                return False
                
        return True 