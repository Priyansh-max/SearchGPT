import logging
import asyncio
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urlparse
from services.serpapi_searcher import serpapi_searcher
from config import settings

logger = logging.getLogger(__name__)

class WebSearcher:
    """
    Service to perform web searches using SerpAPI (replacing Selenium-based search)
    """
    
    def __init__(self):
        self.serpapi_searcher = serpapi_searcher
        self.max_results = settings.SEARCH_RESULTS_LIMIT
        
    async def search(self, query: str, engine: str = "google", num_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform a web search using SerpAPI
        """
        if not query:
            return []
            
        try:
            logger.info(f"Performing web search for: {query}")
            
            # Use SerpAPI for search
            results = await self.serpapi_searcher.search(query, engine, num_results)
            
            # Filter and validate results
            filtered_results = []
            for result in results:
                if self.is_valid_url(result.get("url", "")):
                    filtered_results.append(result)
            
            logger.info(f"Found {len(filtered_results)} valid search results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            return []
    
    async def search_google(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Search Google specifically
        """
        return await self.search(query, "google", num_results)
    
    async def search_bing(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Search Bing specifically
        """
        return await self.search(query, "bing", num_results)
    
    async def extract_urls_from_results(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract URLs from search results
        """
        urls = []
        for result in search_results:
            url = result.get("url", "")
            if url and self.is_valid_url(url):
                urls.append(url)
        return urls
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and not blacklisted
        """
        if not url:
            return False
            
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be http or https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Blacklisted domains/patterns
            blacklisted_patterns = [
                r'\.pdf$',
                r'\.doc$',
                r'\.docx$',
                r'\.xls$',
                r'\.xlsx$',
                r'\.ppt$',
                r'\.pptx$',
                r'\.zip$',
                r'\.rar$',
                r'\.tar$',
                r'\.gz$',
                r'javascript:',
                r'mailto:',
                r'tel:',
                r'ftp:',
                r'file:',
            ]
            
            blacklisted_domains = [
                'facebook.com',
                'twitter.com',
                'instagram.com',
                'linkedin.com',
                'pinterest.com',
                'youtube.com',
                'tiktok.com',
                'snapchat.com',
            ]
            
            # Check against blacklisted patterns
            for pattern in blacklisted_patterns:
                if re.search(pattern, url.lower()):
                    return False
            
            # Check against blacklisted domains
            for domain in blacklisted_domains:
                if domain in parsed.netloc.lower():
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating URL {url}: {str(e)}")
            return False
    
    def clean_url(self, url: str) -> str:
        """
        Clean and normalize URL
        """
        if not url:
            return ""
            
        try:
            # Remove tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
                '_ga', '_gid', '_gac', '_gl', '_gat',
                'ref', 'referrer', 'source', 'campaign',
            ]
            
            parsed = urlparse(url)
            
            # Remove fragment
            cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Add query parameters (excluding tracking ones)
            if parsed.query:
                query_params = []
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        if key.lower() not in tracking_params:
                            query_params.append(param)
                
                if query_params:
                    cleaned_url += '?' + '&'.join(query_params)
            
            return cleaned_url
            
        except Exception as e:
            logger.warning(f"Error cleaning URL {url}: {str(e)}")
            return url
    
    def get_domain(self, url: str) -> str:
        """
        Extract domain from URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    def get_search_info(self) -> Dict[str, Any]:
        """
        Get information about the search configuration
        """
        return {
            "search_engine": "SerpAPI",
            "max_results": self.max_results,
            "serpapi_info": self.serpapi_searcher.get_search_info(),
        }

# Create a singleton instance
web_searcher = WebSearcher() 