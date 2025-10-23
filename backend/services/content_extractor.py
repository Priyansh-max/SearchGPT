import logging
import asyncio
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import time

from utils.playwright_utils import playwright_browser
from utils.text_utils import TextProcessor
from config import settings
from services.web_searcher import web_searcher

logger = logging.getLogger(__name__)

class ScraperResult(BaseModel):
    url: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ContentExtractor:
    """
    Service to extract content from web pages using Playwright
    """
    
    def __init__(self):
        self.web_searcher = web_searcher
        self.text_processor = TextProcessor()
        self.browser = playwright_browser
        
    async def extract_from_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content from search results
        """
        if not search_results:
            return []
            
        # Get URLs from search results
        urls = await self.web_searcher.extract_urls_from_results(search_results)
        
        # Filter valid URLs
        valid_urls = [url for url in urls if self.web_searcher.is_valid_url(url)]
        
        # Limit the number of pages to scrape
        urls_to_scrape = valid_urls[:settings.MAX_PAGES_TO_SCRAPE]
        
        logger.info(f"Extracting content from {len(urls_to_scrape)} URLs")
        
        # Create tasks for scraping each URL
        tasks = []
        for url in urls_to_scrape:
            tasks.append(self.extract_from_url(url))
            
        # Run tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error scraping URL: {str(result)}")
            elif result:
                valid_results.append(result)
                
        return valid_results
    
    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL using Playwright
        """
        if not url:
            return None
            
        try:
            logger.info(f"Extracting content from: {url}")
            
            # First try with Newspaper3k (fast and clean extraction)
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                content = article.text
                title = article.title
                
                # If content is too short, try with Playwright
                if len(content) < 500:
                    raise Exception("Content too short, trying with Playwright")
                    
                metadata = {
                    "published_date": article.publish_date.isoformat() if article.publish_date else None,
                    "authors": article.authors,
                    "keywords": article.keywords,
                    "summary": article.summary,
                    "extraction_method": "newspaper3k"
                }
                
            except Exception as e:
                logger.info(f"Newspaper3k extraction failed: {str(e)}, trying Playwright")
                
                # Navigate to URL with Playwright
                success = await self.browser.navigate(url)
                if not success:
                    raise Exception(f"Failed to navigate to {url}")
                    
                # Wait for page to load
                await asyncio.sleep(2)
                
                # Scroll to load all content
                try:
                    await self.browser.scroll_to_bottom(scroll_pause_time=0.5)
                except Exception as e:
                    logger.warning(f"Error while scrolling, continuing anyway: {str(e)}")
                
                # Get page source
                html = await self.browser.get_page_source()
                if not html:
                    raise Exception("Failed to get page source")
                    
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'lxml')
                if not soup:
                    raise Exception("Failed to parse HTML with BeautifulSoup")
                
                # Extract title
                title_tag = soup.find('title')
                title = title_tag.text if title_tag else "No title"
                
                # Try to find main content
                main_content = None
                
                # Look for common content containers
                for selector in ['article', 'main', '.content', '#content', '.post', '.article', '.entry']:
                    try:
                        container = soup.select_one(selector)
                        if container and len(container.text.strip()) > 500:
                            main_content = container
                            break
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Error selecting {selector}: {str(e)}")
                        continue
                
                # If no container found, use body
                if not main_content:
                    main_content = soup.find('body')
                
                # If we still don't have a main content container, use the entire soup
                if not main_content:
                    logger.warning(f"No main content container found for {url}, using entire document")
                    main_content = soup
                
                # Remove navigation, sidebars, footers, etc.
                try:
                    for tag in main_content.select('nav, header, footer, sidebar, .sidebar, .navigation, .footer, .header, .nav, .menu, .comments, .comment, script, style, [role=banner], [role=navigation]'):
                        tag.decompose()
                except (AttributeError, Exception) as e:
                    logger.warning(f"Error removing tags: {str(e)}")
                
                # Convert to text
                content = self.text_processor.html_to_text(str(main_content))
                
                # Extract main content
                content = self.text_processor.extract_main_content(content)
                
                metadata = {
                    "extraction_method": "playwright",
                    "url": await self.browser.get_current_url(),  # In case of redirects
                }
            
            # Create result
            result = {
                "url": url,
                "title": title,
                "content": content,
                "metadata": metadata
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            raise e
    
    async def extract_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Extract content from multiple URLs concurrently
        """
        if not urls:
            return []
            
        logger.info(f"Extracting content from {len(urls)} URLs concurrently")
        
        # Create tasks for concurrent extraction
        tasks = []
        for url in urls:
            tasks.append(self.extract_from_url(url))
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error in concurrent extraction: {str(result)}")
            elif result:
                valid_results.append(result)
        
        return valid_results
    
    async def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """
        Extract structured data (JSON-LD, etc.) from HTML
        """
        if not html:
            return {}
            
        try:
            structured_data = {}
            
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            if not soup:
                return {}
            
            # Find JSON-LD scripts
            try:
                json_ld_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_ld_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if '@type' in data:
                            structured_data[data['@type']] = data
                    except Exception as e:
                        logger.warning(f"Error parsing JSON-LD: {str(e)}")
            except Exception as e:
                logger.warning(f"Error finding JSON-LD scripts: {str(e)}")
                    
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {}
    
    async def cleanup(self):
        """
        Clean up resources
        """
        try:
            await self.browser.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Create a singleton instance
content_extractor = ContentExtractor() 