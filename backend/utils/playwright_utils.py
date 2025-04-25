import os
import time
import logging
import platform
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, ElementHandle
from bs4 import BeautifulSoup

from config import settings

logger = logging.getLogger(__name__)

class PlaywrightBrowser:
    """
    A utility class for Playwright browser automation
    """
    
    def __init__(self, headless=True):
        """
        Initialize the browser
        """
        self.headless = headless
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        
    async def start(self):
        """
        Start the browser
        """
        if self.browser is not None:
            return
            
        try:
            # Determine system architecture
            is_64bits = platform.architecture()[0] == '64bit'
            logger.info(f"System architecture: {'64-bit' if is_64bits else '32-bit'}")
            
            # Launch playwright and browser
            self.playwright = await async_playwright().start()
            
            # Configure browser options
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                f'--user-agent={settings.USER_AGENT}',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-popup-blocking',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1280,1696',
                '--ignore-certificate-errors',
                '--allow-running-insecure-content'
            ]
            
            # Create browser and context with configured settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Create a context (similar to a profile in Selenium)
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 1696},
                user_agent=settings.USER_AGENT
            )
            
            # Create a new page
            self.page = await self.context.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(settings.SELENIUM_TIMEOUT * 1000)
            
            # Log success
            logger.info("Playwright browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {str(e)}")
            # Clean up partially initialized resources
            await self.stop()
            raise
    
    async def stop(self):
        """
        Stop the browser
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Playwright browser stopped")
        except Exception as e:
            logger.error(f"Error stopping Playwright browser: {str(e)}")
    
    async def navigate(self, url):
        """
        Navigate to a URL
        """
        if not self.page:
            await self.start()
            
        try:
            logger.info(f"Navigating to: {url}")
            response = await self.page.goto(url, wait_until="domcontentloaded")
            return response.ok
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return False
    
    async def get_page_source(self):
        """
        Get the page source
        """
        if not self.page:
            return ""
            
        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Error getting page source: {str(e)}")
            return ""
    
    async def get_current_url(self):
        """
        Get the current URL
        """
        if not self.page:
            return ""
            
        try:
            return self.page.url
        except Exception as e:
            logger.error(f"Error getting current URL: {str(e)}")
            return ""
    
    async def search_google(self, query):
        """
        Perform a Google search and extract results
        """
        if not query:
            return []
            
        results = []
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Navigate to Google
                logger.info(f"Navigating to Google for search: {query}")
                success = await self.navigate("https://www.google.com")
                if not success:
                    raise Exception("Failed to navigate to Google")
                
                # Accept cookies if the dialog appears
                try:
                    cookie_buttons = await self.page.get_by_role("button").filter(has_text=r"Accept all|I agree|Accept").all()
                    if cookie_buttons:
                        await cookie_buttons[0].click()
                        logger.info("Accepted Google cookies")
                        await asyncio.sleep(1)
                except Exception:
                    logger.debug("No cookie dialog found or could not accept")
                
                # Find search box and enter query
                try:
                    logger.debug("Looking for search input")
                    search_box = await self.page.query_selector('input[name="q"]')
                    if search_box:
                        await search_box.fill("")
                        await search_box.fill(query)
                        await search_box.press("Enter")
                        logger.info("Submitted search query")
                    else:
                        raise Exception("Search input not found")
                except Exception as e:
                    logger.error(f"Failed to input search query: {str(e)}")
                    raise
                
                # Wait for results to load
                results_loaded = False
                selectors = [
                    "div.g", 
                    "div[data-hveid]", 
                    "div.MjjYud", 
                    "div[data-header-feature]",
                    "h3",
                    "#search",
                    "#rso",
                    "div.v7W49e",
                    "div.ULSxyf",
                    "[data-sokoban-container]"
                ]
                
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        logger.info(f"Search results loaded with selector: {selector}")
                        results_loaded = True
                        break
                    except Exception:
                        continue
                
                if not results_loaded:
                    logger.warning("Failed to detect search results with any selectors")
                
                # Save page source for debugging
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, "google_search.html"), "w", encoding="utf-8") as f:
                    f.write(await self.get_page_source())
                logger.info("Saved search page source for debugging")
                
                # Give the page a moment to stabilize
                await asyncio.sleep(3)
                
                # Try the more direct approach to find all links
                logger.info("Trying direct link extraction")
                links = await self.page.query_selector_all("a")
                logger.info(f"Found {len(links)} total links on the page")
                
                # Process links - focusing on those that are likely search results
                position = 0
                processed_urls = set()
                
                for link in links:
                    try:
                        # Get link attributes
                        href = await link.get_attribute("href") or ""
                        classes = await link.get_attribute("class") or ""
                        
                        # Skip Google internal links, navigation links, and image links
                        if (not href or 
                            "google.com" in href or 
                            href in processed_urls or
                            href.startswith("#") or
                            "settings" in href or
                            "accounts.google" in href or
                            "images" in href or
                            "maps" in href or
                            "javascript:" in href or
                            "navigation" in classes.lower() or
                            "menu" in classes.lower()):
                            continue
                        
                        # Get link text
                        link_text = await link.inner_text()
                        link_text = link_text.strip()
                        
                        # If link has no text, try to find h3 within it
                        if not link_text:
                            try:
                                parent = await link.evaluate('el => el.parentElement')
                                if parent:
                                    h3 = await self.page.evaluate('parent => {const h3 = parent.querySelector("h3"); return h3 ? h3.textContent : "";}', parent)
                                    if h3:
                                        link_text = h3.strip()
                            except Exception:
                                pass
                        
                        # Only include links that have text and look like result titles
                        if link_text and len(link_text) > 10:
                            position += 1
                            processed_urls.add(href)
                            
                            # Look for snippet text near the link
                            snippet = "No description available"
                            try:
                                # Try to get the parent element for snippet extraction
                                parent_div = await link.evaluate('el => {const parent = el.closest("div[data-hveid]") || el.parentElement.parentElement; return parent;}')
                                if parent_div:
                                    # Try to extract text from spans (common in Google results)
                                    spans_text = await self.page.evaluate('''
                                        parent => {
                                            const spans = parent.querySelectorAll("span");
                                            const candidateTexts = [];
                                            spans.forEach(span => {
                                                const text = span.textContent.trim();
                                                if (text && text.length > 40) {
                                                    candidateTexts.push(text);
                                                }
                                            });
                                            return candidateTexts.join(' ');
                                        }
                                    ''', parent_div)
                                    
                                    if spans_text:
                                        snippet = spans_text
                                    else:
                                        # Try divs if spans don't have content
                                        divs_text = await self.page.evaluate('''
                                            parent => {
                                                const divs = parent.querySelectorAll("div");
                                                for (const div of divs) {
                                                    const text = div.textContent.trim();
                                                    if (text && text.length > 40) {
                                                        return text;
                                                    }
                                                }
                                                return "";
                                            }
                                        ''', parent_div)
                                        
                                        if divs_text:
                                            snippet = divs_text
                            except Exception:
                                pass
                                
                            results.append({
                                "title": link_text,
                                "url": href,
                                "snippet": snippet,
                                "position": position
                            })
                            
                            # Limit number of results
                            if position >= settings.SEARCH_RESULTS_LIMIT:
                                break
                    except Exception as e:
                        logger.debug(f"Error processing link: {str(e)}")
                
                logger.info(f"Successfully extracted {len(results)} search results")
                
                # If we have results, exit the retry loop
                if results:
                    break
                    
                # If no results, retry
                logger.warning("No search results extracted, will retry")
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Error during Google search: {str(e)}")
                retry_count += 1
            
            # Sleep between retries
            if retry_count < max_retries and not results:
                logger.info(f"Retrying search after a short delay (attempt {retry_count+1}/{max_retries})")
                await asyncio.sleep(2)
        
        # Ensure we return the top X results as specified in settings
        return results[:settings.SEARCH_RESULTS_LIMIT]
    
    async def get_element_text(self, selector, timeout=10):
        """
        Get text from an element
        """
        if not self.page:
            return ""
            
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout * 1000)
            if element:
                return await element.inner_text()
            return ""
        except Exception as e:
            logger.error(f"Error getting element text: {str(e)}")
            return ""
    
    async def scroll_to_bottom(self, scroll_pause_time=1.0):
        """
        Scroll to the bottom of the page gradually
        """
        if not self.page:
            return
            
        try:
            # Get scroll height
            last_height = await self.page.evaluate("document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait to load page
                await asyncio.sleep(scroll_pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {str(e)}")

# Create a singleton instance that can be imported by other modules
browser = PlaywrightBrowser(headless=settings.SELENIUM_HEADLESS) 