import logging
import asyncio
from typing import List, Dict, Any, Optional
import time
from config import settings
# NOTE: `from serpapi import GoogleSearch` is imported lazily inside the search methods so
# this module (and the whole API) imports even when the package/key isn't present.

logger = logging.getLogger(__name__)

class SerpApiSearcher:
    """
    Service to perform web searches using SerpAPI
    """
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.engine = settings.SERPAPI_ENGINE
        self.timeout = settings.SERPAPI_TIMEOUT
        
        # Lazy/graceful: do NOT raise at import — the engine and tests must load without a
        # SERPAPI_KEY. Searches return [] (and log) if the key is missing at call time.
        if not self.api_key:
            logger.warning("SERPAPI_KEY not set — search will return no results until configured")
        else:
            logger.info(f"SerpAPI searcher initialized with engine: {self.engine}")
    
    async def search_google(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Search Google using SerpAPI
        """
        if not query:
            return []
        
        if not self.api_key:
            logger.error("SERPAPI_KEY not configured — cannot search")
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
            from serpapi import GoogleSearch  # lazy import
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
            from serpapi import GoogleSearch  # lazy import
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

    async def search_images(self, query: str, num_images: int = 4) -> List[Dict[str, Any]]:
        """Fetch visual assets for the playground UI. This is separate from /api/v1 search."""
        if not query or not self.api_key:
            return []
        try:
            from serpapi import GoogleSearch  # lazy import
            params = {
                "engine": "google_images",
                "q": query,
                "api_key": self.api_key,
                "ijn": "0",
                "hl": "en",
                "gl": "us",
                "safe": "off",
            }
            results = GoogleSearch(params).get_dict()
            images = []
            for item in results.get("images_results", []):
                image_url = item.get("original") or item.get("thumbnail") or ""
                source_url = item.get("link") or item.get("source") or ""
                if not self._is_content_image(image_url):
                    continue
                images.append({
                    "title": item.get("title") or query,
                    "image": image_url,
                    "thumbnail": item.get("thumbnail") or image_url,
                    "source_url": source_url,
                    "source": item.get("source") or "Google Images",
                })
                if len(images) >= num_images:
                    break
            return images
        except Exception as e:
            logger.warning(f"Image search failed for playground: {str(e)}")
            return []
    
    @staticmethod
    def _is_content_image(url: str) -> bool:
        if not url or not str(url).startswith(("http://", "https://")):
            return False
        lowered = str(url).lower()
        blocked = ("google.com/s2/favicons", "/favicon", "favicon.", "apple-touch-icon", "logo.svg")
        return not any(token in lowered for token in blocked)

    def _organic_image(self, result: Dict[str, Any]) -> str:
        image = result.get("thumbnail") or ""
        return image if self._is_content_image(image) else ""

    def _parse_google_rich_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        rich_results: List[Dict[str, Any]] = []

        knowledge = results.get("knowledge_graph") or {}
        if knowledge:
            source = knowledge.get("source") or {}
            url = knowledge.get("website") or source.get("link") or knowledge.get("link") or ""
            facts = []
            description = knowledge.get("description")
            if description:
                facts.append(description)
            for key, value in knowledge.items():
                if key in {"title", "type", "description", "source", "website", "thumbnail", "header_images", "images", "profiles"}:
                    continue
                if isinstance(value, (str, int, float)) and value:
                    label = str(key).replace("_", " ").title()
                    facts.append(f"{label}: {value}")
            rich_results.append({
                "title": knowledge.get("title") or "Knowledge panel",
                "url": url,
                "snippet": " ".join(facts[:10]),
                "position": 0,
                "source": source.get("name") or "Google Knowledge Graph",
                "displayed_link": source.get("name") or url,
                "image": self._organic_image(knowledge),
                "metadata": {"engine": "google", "serpapi_result": True, "rich_result": "knowledge_graph"},
            })

        answer = results.get("answer_box") or {}
        if answer:
            url = answer.get("link") or answer.get("displayed_link") or ""
            snippet_parts = [answer.get(key) for key in ("answer", "snippet", "snippet_highlighted_words")]
            snippet = " ".join(str(part) for part in snippet_parts if part)
            rich_results.append({
                "title": answer.get("title") or answer.get("type") or "Answer box",
                "url": url,
                "snippet": snippet,
                "position": 0,
                "source": answer.get("source") or "Google Answer Box",
                "displayed_link": answer.get("displayed_link", ""),
                "image": self._organic_image(answer),
                "metadata": {"engine": "google", "serpapi_result": True, "rich_result": "answer_box"},
            })

        return [item for item in rich_results if item.get("title") and item.get("url")]

    def _parse_google_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Google search results from SerpAPI response
        """
        parsed_results = self._parse_google_rich_results(results)
        seen_urls = {item.get("url") for item in parsed_results}
        
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
                    "image": self._organic_image(result),
                    "metadata": {
                        "engine": "google",
                        "serpapi_result": True,
                        "cached_url": result.get("cached_page_link", ""),
                        "related_pages": result.get("related_pages_link", ""),
                    }
                }
                
                # Only add if we have essential fields
                if parsed_result["title"] and parsed_result["url"] and parsed_result["url"] not in seen_urls:
                    parsed_results.append(parsed_result)
                    seen_urls.add(parsed_result["url"])
                    
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
                    "image": self._organic_image(result),
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