import logging
import asyncio
from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
import time
from config import settings

logger = logging.getLogger(__name__)

class SerpApiSearcher:
    """
    Service to perform web searches using SerpAPI
    """
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.engine = settings.SERPAPI_ENGINE
        self.timeout = settings.SERPAPI_TIMEOUT
        
        if not self.api_key:
            logger.warning("SERPAPI_KEY not found in environment variables")
            raise ValueError("SERPAPI_KEY is required for SerpAPI integration")
        
        logger.info(f"SerpAPI searcher initialized with engine: {self.engine}")
    
    async def search_google(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Search Google using SerpAPI
        """
        if not query:
            return []
        
        num_results = num_results or settings.SEARCH_RESULTS_LIMIT
        
        try:
            logger.info(f"Searching Google for: {query}")
            
            # Configure search parameters
            search_params = {
                "q": query,
                "engine": "google",
                "api_key": self.api_key,
                "num": num_results,
                "safe": "off",
                "gl": "us",  # Country
                "hl": "en",  # Language
            }
            
            # Execute search
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            # Parse results
            parsed_results = self._parse_google_results(results)
            
            logger.info(f"Found {len(parsed_results)} Google search results")
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error searching Google with SerpAPI: {str(e)}")
            return []
    
    async def search_bing(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Search Bing using SerpAPI
        """
        if not query:
            return []
        
        num_results = num_results or settings.SEARCH_RESULTS_LIMIT
        
        try:
            logger.info(f"Searching Bing for: {query}")
            
            # Configure search parameters
            search_params = {
                "q": query,
                "engine": "bing",
                "api_key": self.api_key,
                "count": num_results,
                "cc": "US",  # Country
                "mkt": "en-US",  # Market
            }
            
            # Execute search
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            # Parse results
            parsed_results = self._parse_bing_results(results)
            
            logger.info(f"Found {len(parsed_results)} Bing search results")
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error searching Bing with SerpAPI: {str(e)}")
            return []
    
    async def search(self, query: str, engine: str = None, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Generic search method that routes to appropriate engine
        """
        engine = engine or self.engine
        
        if engine.lower() == "google":
            return await self.search_google(query, num_results)
        elif engine.lower() == "bing":
            return await self.search_bing(query, num_results)
        else:
            logger.warning(f"Unsupported search engine: {engine}, defaulting to Google")
            return await self.search_google(query, num_results)
    
    def _parse_google_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Google search results from SerpAPI response
        """
        parsed_results = []
        
        # Get organic results
        organic_results = results.get("organic_results", [])
        
        for i, result in enumerate(organic_results):
            try:
                parsed_result = {
                    "title": result.get("title", "No title"),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", "No description available"),
                    "position": i + 1,
                    "source": "Google (SerpAPI)",
                    "displayed_link": result.get("displayed_link", ""),
                    "metadata": {
                        "engine": "google",
                        "serpapi_result": True,
                        "cached_url": result.get("cached_page_link", ""),
                        "related_pages": result.get("related_pages_link", ""),
                    }
                }
                
                # Only add if we have essential fields
                if parsed_result["title"] and parsed_result["url"]:
                    parsed_results.append(parsed_result)
                    
            except Exception as e:
                logger.warning(f"Error parsing Google result {i}: {str(e)}")
                continue
        
        return parsed_results
    
    def _parse_bing_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bing search results from SerpAPI response
        """
        parsed_results = []
        
        # Get organic results
        organic_results = results.get("organic_results", [])
        
        for i, result in enumerate(organic_results):
            try:
                parsed_result = {
                    "title": result.get("title", "No title"),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", "No description available"),
                    "position": i + 1,
                    "source": "Bing (SerpAPI)",
                    "displayed_link": result.get("displayed_link", ""),
                    "metadata": {
                        "engine": "bing",
                        "serpapi_result": True,
                        "cached_url": result.get("cached_page_link", ""),
                    }
                }
                
                # Only add if we have essential fields
                if parsed_result["title"] and parsed_result["url"]:
                    parsed_results.append(parsed_result)
                    
            except Exception as e:
                logger.warning(f"Error parsing Bing result {i}: {str(e)}")
                continue
        
        return parsed_results
    
    def get_search_info(self) -> Dict[str, Any]:
        """
        Get information about the current search configuration
        """
        return {
            "engine": self.engine,
            "api_key_configured": bool(self.api_key),
            "timeout": self.timeout,
            "max_results": settings.SEARCH_RESULTS_LIMIT,
        }

# Create a singleton instance
serpapi_searcher = SerpApiSearcher() 