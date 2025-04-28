import logging
import asyncio
import re
import time
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        """
        if not query:
            return []
            
        try:
            # Make sure browser is started
            if not browser.driver:
                await browser.start()
                
            # Navigate to Google
            await browser.navigate("https://www.google.com")
            
            # Wait for search box to appear
            try:
                search_box = WebDriverWait(browser.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                
                # Type slowly like a human
                search_box.clear()
                for char in query:
                    search_box.send_keys(char)
                    time.sleep(0.1)  # Small delay between keypresses
                
                # Wait for suggestions to appear
                time.sleep(2)
                
                # Try different selectors for suggestions
                suggestions = []
                selectors = [
                    "li.sbct",
                    "div.wM6W7d",
                    "ul.G43f7e li",
                    "ul[role='listbox'] li",
                    "div.UUbT9 div.aypzV",
                    "div.OBMEnb ul li"
                ]
                
                for selector in selectors:
                    try:
                        elements = browser.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            for element in elements:
                                try:
                                    # Try to get inner text element
                                    text_element = element.find_element(By.CSS_SELECTOR, "div.wM6W7d, span.G43f7e")
                                    suggestion_text = text_element.text.strip()
                                except:
                                    # If can't find text element, use the element's own text
                                    suggestion_text = element.text.strip()
                                    
                                if suggestion_text and suggestion_text not in suggestions:
                                    suggestions.append(suggestion_text)
                            
                            if suggestions:
                                logger.info(f"Found {len(suggestions)} suggestions using selector: {selector}")
                                break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {str(e)}")
                
                # Take a screenshot for debugging
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                browser.driver.save_screenshot(os.path.join(debug_dir, "suggestions.png"))
                
                return suggestions[:10]  # Return at most 10 suggestions
                
            except Exception as e:
                logger.warning(f"Error extracting suggestions: {str(e)}")
                return []
                
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