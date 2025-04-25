import logging
import asyncio
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import aiohttp
import os
import urllib.parse

from utils.selenium_utils import browser
from config import settings
from services.query_analyzer import QueryAnalyzer
from services.web_searcher import WebSearcher

logger = logging.getLogger(__name__)

class NewsSearcher:
    """
    Service to search for news articles directly using APIs and RSS feeds
    """
    
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.web_searcher = WebSearcher()
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for news articles related to the query
        """
        if not query:
            return []
            
        try:
            logger.info(f"Searching for news articles: {query}")
            
            # Try using GNews API
            gnews_results = await self.search_gnews(query)
            if gnews_results:
                logger.info(f"Found {len(gnews_results)} news results from GNews")
                return gnews_results
                
            # If GNews fails, try direct RSS feeds
            rss_results = await self.search_rss_feeds(query)
            if rss_results:
                logger.info(f"Found {len(rss_results)} news results from RSS feeds")
                return rss_results
                
            # Last resort: standard web search limited to news sites
            logger.info("Trying fallback to web search for news")
            return await self.fallback_news_search(query)
            
        except Exception as e:
            logger.error(f"Error searching for news: {str(e)}")
            try:
                # Last fallback - use standard Google search
                logger.info("Attempting last resort fallback to standard search")
                search_results = await self.web_searcher.search(f"{query} news recent")
                
                # Convert to news format
                news_results = []
                for result in search_results:
                    news_results.append({
                        "title": result.get("title", "No title"),
                        "source": self.extract_domain(result.get("url", "")),
                        "url": result.get("url", ""),
                        "published_date": datetime.now().isoformat(),
                        "snippet": result.get("snippet", "No description available")
                    })
                return news_results
            except:
                return []
    
    async def search_gnews(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for news using GNews API-like endpoints
        """
        try:
            # Multiple possible endpoints to try
            endpoints = [
                "https://gnews.io/api/v4/search",  # Requires API key but works well
                "https://newsapi.org/v2/everything"  # NewsAPI
            ]
            
            for endpoint in endpoints:
                try:
                    # Configure parameters
                    params = {
                        'q': query,
                        'lang': 'en',
                        'country': 'us',
                        'max': 10
                    }
                    
                    # Add API key if available
                    if settings.NEWS_API_KEY and "newsapi.org" in endpoint:
                        params['apiKey'] = settings.NEWS_API_KEY
                    elif settings.NEWS_API_KEY and "gnews.io" in endpoint:
                        params['token'] = settings.NEWS_API_KEY
                    else:
                        # Skip if no API key
                        continue
                    
                    # Make request
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, params=params, timeout=15) as response:
                            if response.status != 200:
                                logger.warning(f"Error from {endpoint}: {response.status}")
                                continue
                                
                            data = await response.json()
                            
                            # Process response based on API format
                            articles = []
                            if "articles" in data:
                                articles = data.get("articles", [])
                            elif "results" in data:
                                articles = data.get("results", [])
                            
                            if not articles:
                                continue
                                
                            # Format results
                            results = []
                            for i, article in enumerate(articles):
                                # Handle different API response formats
                                title = article.get('title', 'No title')
                                url = article.get('url', article.get('link', ''))
                                published_date = article.get('publishedAt', article.get('pubDate', ''))
                                
                                # Extract source
                                source = ""
                                if isinstance(article.get('source'), dict):
                                    source = article.get('source', {}).get('name', '')
                                else:
                                    source = article.get('source', '')
                                    
                                if not source:
                                    source = self.extract_domain(url)
                                
                                # Get snippet
                                snippet = article.get('description', 'No description available')
                                
                                results.append({
                                    "title": title,
                                    "source": source,
                                    "url": url,
                                    "published_date": published_date,
                                    "snippet": snippet
                                })
                            
                            if results:
                                return results
                                
                except Exception as e:
                    logger.warning(f"Error with {endpoint}: {str(e)}")
                    continue
            
            return []
                    
        except Exception as e:
            logger.error(f"Error searching news APIs: {str(e)}")
            return []
    
    async def search_rss_feeds(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for news using RSS feeds
        """
        try:
            # Prepare query
            encoded_query = urllib.parse.quote(query)
            
            # List of RSS feeds to try
            rss_feeds = [
                f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en",
                f"https://www.bing.com/news/search?q={encoded_query}&format=rss"
            ]
            
            all_results = []
            
            # Process each RSS feed
            async with aiohttp.ClientSession() as session:
                for feed_url in rss_feeds:
                    try:
                        async with session.get(feed_url, timeout=10) as response:
                            if response.status != 200:
                                logger.warning(f"Error from RSS feed {feed_url}: {response.status}")
                                continue
                                
                            # Parse XML content
                            xml_content = await response.text()
                            
                            # Simple XML parsing
                            items = re.findall(r'<item>(.*?)</item>', xml_content, re.DOTALL)
                            
                            feed_results = []
                            for item in items[:10]:  # Limit to 10 items
                                try:
                                    # Extract title
                                    title_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                                    title = title_match.group(1) if title_match else "No title"
                                    title = self._clean_xml_text(title)
                                    
                                    # Extract link
                                    link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
                                    url = link_match.group(1) if link_match else ""
                                    
                                    # Extract description
                                    desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                                    snippet = desc_match.group(1) if desc_match else "No description available"
                                    snippet = self._clean_xml_text(snippet)
                                    
                                    # Extract publication date
                                    date_match = re.search(r'<pubDate>(.*?)</pubDate>', item, re.DOTALL)
                                    published_date = date_match.group(1) if date_match else ""
                                    
                                    # Extract source
                                    source_match = re.search(r'<source>(.*?)</source>', item, re.DOTALL)
                                    if source_match:
                                        source = source_match.group(1)
                                    else:
                                        source = self.extract_domain(url)
                                    
                                    feed_results.append({
                                        "title": title,
                                        "source": source,
                                        "url": url,
                                        "published_date": published_date,
                                        "snippet": snippet
                                    })
                                except Exception as e:
                                    logger.warning(f"Error parsing RSS item: {str(e)}")
                                    continue
                            
                            all_results.extend(feed_results)
                            
                            if feed_results:
                                logger.info(f"Found {len(feed_results)} results from {feed_url}")
                                
                    except Exception as e:
                        logger.warning(f"Error processing RSS feed {feed_url}: {str(e)}")
            
            # Return results if found
            if all_results:
                # Sort by source diversity to avoid all results from same source
                sources = {}
                for result in all_results:
                    source = result.get("source", "")
                    if source not in sources:
                        sources[source] = []
                    sources[source].append(result)
                
                # Collect results ensuring source diversity
                diverse_results = []
                for source_results in sources.values():
                    diverse_results.extend(source_results[:3])  # Up to 3 per source
                
                return diverse_results[:10]  # Return up to 10 results
                
            return []
            
        except Exception as e:
            logger.error(f"Error searching RSS feeds: {str(e)}")
            return []
    
    def _clean_xml_text(self, text):
        """Clean XML/HTML text"""
        # Remove CDATA if present
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        text = self._decode_html_entities(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _decode_html_entities(self, text):
        """Simple HTML entity decoder"""
        entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        for entity, char in entities.items():
            text = text.replace(entity, char)
        return text
            
    async def fallback_news_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback method using standard web search limited to news sites
        """
        try:
            # Add news-related terms and site-specific searches
            news_sites = ['site:bbc.com OR site:cnn.com OR site:nytimes.com OR site:reuters.com']
            fallback_query = f"{query} news recent {' '.join(news_sites)}"
            
            # Use the regular web search
            search_results = await self.web_searcher.search(fallback_query)
            
            # Convert to news format
            news_results = []
            for result in search_results:
                news_results.append({
                    "title": result.get("title", "No title"),
                    "source": self.extract_domain(result.get("url", "")),
                    "url": result.get("url", ""),
                    "published_date": datetime.now().isoformat(),  # We don't have the actual date
                    "snippet": result.get("snippet", "No description available")
                })
            
            return news_results
        except Exception as e:
            logger.error(f"Error in fallback news search: {str(e)}")
            return []
    
    def extract_domain(self, url: str) -> str:
        """
        Extract domain name from URL
        """
        if not url:
            return "Unknown source"
            
        try:
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                return domain_match.group(1)
            return "Unknown source"
        except Exception:
            return "Unknown source" 