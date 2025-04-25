import os
import time
import logging
import platform
import subprocess
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from config import settings

logger = logging.getLogger(__name__)

class SeleniumBrowser:
    """
    A utility class for Selenium browser automation
    """
    
    def __init__(self, headless=True):
        """
        Initialize the browser
        """
        self.headless = headless
        self.driver = None
        self.max_retry_count = 3
        
    async def start(self):
        """
        Start the browser
        """
        options = Options()
        
        if self.headless:
            # Use the more stable approach for headless mode
            options.add_argument('--headless=new')  # Updated headless mode for newer Chrome
            
        # Basic required options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={settings.USER_AGENT}')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        
        # Additional stability options
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set window size to avoid rendering issues
        options.add_argument('--window-size=1920,1080')
        
        try:
            # Determine system architecture
            is_64bits = platform.architecture()[0] == '64bit'
            logger.info(f"System architecture: {'64-bit' if is_64bits else '32-bit'}")
            
            # Get Chrome version if available
            chrome_version = self._get_chrome_version()
            if chrome_version:
                logger.info(f"Detected Chrome version: {chrome_version}")
            
            # Clear ChromeDriver cache
            self._clear_driver_cache()
            
            retry_count = 0
            last_exception = None
            
            while retry_count < self.max_retry_count:
                try:
                    if retry_count > 0:
                        logger.info(f"Retry attempt {retry_count} to start browser")
                    
                    # First attempt: Use ChromeDriverManager 
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Selenium browser started successfully using ChromeDriverManager")
                    break
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Failed to start browser with ChromeDriverManager: {str(e)}")
                    retry_count += 1
                    
                    if retry_count >= self.max_retry_count:
                        logger.info("Trying alternative methods after ChromeDriverManager failed")
                        
                        try:
                            # Second attempt: Try to use Chrome's built-in driver support
                            self.driver = webdriver.Chrome(options=options)
                            logger.info("Selenium browser started successfully using Chrome's built-in driver")
                            break
                        except Exception as e2:
                            logger.warning(f"Failed to start browser with built-in driver: {str(e2)}")
                            
                            # Third attempt: Try finding Chrome manually
                            try:
                                chrome_path = self._find_chrome_path()
                                if chrome_path:
                                    logger.info(f"Found Chrome installation at: {chrome_path}")
                                    options.binary_location = chrome_path
                                    
                                    # Try uninstalling previous ChromeDriver
                                    try:
                                        from webdriver_manager.chrome import ChromeDriverManager
                                        ChromeDriverManager().uninstall()
                                        logger.info("Uninstalled previous ChromeDriver")
                                    except Exception as uninstall_error:
                                        logger.warning(f"Could not uninstall ChromeDriver: {str(uninstall_error)}")
                                    
                                    # Try with manual Chrome path
                                    self.driver = webdriver.Chrome(options=options)
                                    logger.info("Selenium browser started successfully using manual Chrome path")
                                    break
                                else:
                                    raise Exception("Could not find Chrome installation")
                            except Exception as e3:
                                logger.error(f"All attempts to start Chrome failed: {str(e3)}")
                                raise Exception(f"Failed to start Chrome browser after multiple attempts. Last error: {str(e3)}")
            
            if not self.driver:
                raise Exception(f"Failed to start Chrome browser. Last error: {str(last_exception)}")
            
            # Configure driver
            self.driver.set_page_load_timeout(settings.SELENIUM_TIMEOUT)
            
        except Exception as e:
            logger.error(f"Failed to start Selenium browser: {str(e)}")
            raise
    
    def _get_chrome_version(self):
        """Get Chrome version if possible"""
        try:
            if sys.platform.startswith('win'):
                # Windows
                chrome_paths = [
                    os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
                    os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe'),
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe')
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        try:
                            result = subprocess.run([path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            if result.stdout:
                                return result.stdout.strip()
                        except Exception:
                            pass
            return None
        except Exception as e:
            logger.warning(f"Unable to get Chrome version: {str(e)}")
            return None
            
    def _clear_driver_cache(self):
        """Clear ChromeDriver cache"""
        try:
            # Clear old driver cache if it exists
            cache_path = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver")
            if os.path.exists(cache_path):
                logger.info(f"Clearing old ChromeDriver cache at {cache_path}")
                import shutil
                try:
                    shutil.rmtree(cache_path)
                except Exception as e:
                    logger.warning(f"Failed to clear cache: {str(e)}")
        except Exception as e:
            logger.warning(f"Error during cache clearing: {str(e)}")
    
    def _find_chrome_path(self):
        """Find Chrome installation path"""
        try:
            # Common Chrome paths on Windows
            chrome_paths = [
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe')
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    return path
            return None
        except Exception as e:
            logger.warning(f"Error finding Chrome path: {str(e)}")
            return None
            
    async def stop(self):
        """
        Stop the browser
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium browser stopped")
            except Exception as e:
                logger.error(f"Error stopping Selenium browser: {str(e)}")
    
    async def navigate(self, url):
        """
        Navigate to a URL
        """
        if not self.driver:
            await self.start()
            
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            return True
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return False
    
    async def get_page_source(self):
        """
        Get the page source
        """
        if not self.driver:
            return ""
            
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page source: {str(e)}")
            return ""
    
    async def get_current_url(self):
        """
        Get the current URL
        """
        if not self.driver:
            return ""
            
        try:
            return self.driver.current_url
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
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Accept')]"))
                    ).click()
                    logger.info("Accepted Google cookies")
                    time.sleep(1)
                except Exception:
                    logger.debug("No cookie dialog found or could not accept")
                
                # Find search box and enter query with explicit waits
                try:
                    logger.debug("Looking for search input")
                    search_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "q"))
                    )
                    search_box.clear()
                    search_box.send_keys(query)
                    search_box.submit()
                    logger.info("Submitted search query")
                except Exception as e:
                    logger.error(f"Failed to input search query: {str(e)}")
                    raise
                
                # Wait for results to load with multiple possible selectors
                try:
                    selectors = [
                        "div.g", 
                        "div[data-hveid]", 
                        "div.MjjYud", 
                        "div[data-header-feature]",
                        "h3"
                    ]
                    
                    for selector in selectors:
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            logger.info(f"Search results loaded with selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                    
                except TimeoutException:
                    logger.warning("Timed out waiting for search results. Using current page anyway.")
                
                # Save page source for debugging if needed
                try:
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    with open(os.path.join(debug_dir, "google_search.html"), "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.info("Saved search page source for debugging")
                except Exception as e:
                    logger.debug(f"Could not save debug page source: {str(e)}")
                
                # Give the page a moment to stabilize
                time.sleep(2)
                
                # Extract results using multiple selectors for modern Google search
                result_elements = []
                
                # Method 1: Try the traditional Google result containers
                selectors = [
                    "div.g", 
                    "div.MjjYud",
                    "div[data-sokoban-container]",
                    "div[data-header-feature]",
                    "div.v7W49e"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"Found {len(elements)} results with selector: {selector}")
                            result_elements = elements
                            break
                    except Exception:
                        continue
                
                # If no results found with traditional selectors, try a more aggressive approach
                if not result_elements:
                    logger.warning("No results found with traditional selectors, trying alternative approach")
                    
                    # Extract all links and headings
                    h3_elements = self.driver.find_elements(By.TAG_NAME, "h3")
                    if h3_elements:
                        logger.info(f"Found {len(h3_elements)} heading elements")
                        result_elements = h3_elements
                
                # Process the result elements
                position = 0
                processed_urls = set()  # To avoid duplicates
                
                # Method 2: If traditional containers don't work, try direct a-h3 pairs
                if not result_elements or len(result_elements) < 3:
                    logger.info("Trying direct a-h3 pairs extraction")
                    
                    h3_elements = self.driver.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        try:
                            # Find the closest parent with a link
                            current = h3
                            link = None
                            
                            # Try to find an ancestor with a link up to 5 levels up
                            for _ in range(5):
                                try:
                                    # First try to find a direct child link
                                    links = current.find_elements(By.TAG_NAME, "a")
                                    if links:
                                        link = links[0]
                                        break
                                    
                                    # If no direct child, try to get the parent and check again
                                    current = current.find_element(By.XPATH, "./..")
                                except Exception:
                                    break
                            
                            if not link:
                                # Try to find the next sibling or parent's next sibling with a link
                                try:
                                    siblings = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), '{h3.text}')]/following::a")
                                    if siblings:
                                        link = siblings[0]
                                except Exception:
                                    pass
                            
                            if link:
                                url = link.get_attribute("href")
                                if url and url not in processed_urls and "google.com" not in url:
                                    position += 1
                                    
                                    # Look for a snippet near the heading
                                    snippet = "No description available"
                                    try:
                                        # Try different approaches to find text content near the heading
                                        parent = h3.find_element(By.XPATH, "./../../..")
                                        snippet_candidates = parent.find_elements(By.TAG_NAME, "span")
                                        
                                        # Combine texts from spans that might contain the description
                                        candidate_texts = []
                                        for span in snippet_candidates:
                                            if len(span.text) > 40:  # Only consider substantial text
                                                candidate_texts.append(span.text)
                                        
                                        if candidate_texts:
                                            snippet = " ".join(candidate_texts)
                                    except Exception:
                                        pass
                                    
                                    results.append({
                                        "title": h3.text,
                                        "url": url,
                                        "snippet": snippet,
                                        "position": position
                                    })
                                    
                                    processed_urls.add(url)
                        except Exception as e:
                            logger.debug(f"Error processing heading: {str(e)}")
                
                # Method 3: Process the result elements found earlier with traditional approach
                if result_elements and len(results) < 5:  # Only if we don't have enough results yet
                    for element in result_elements:
                        try:
                            url = ""
                            title = ""
                            snippet = ""
                            
                            # Extract URL first - we need this to deduplicate and validate
                            try:
                                # Try different approaches to find the link
                                link_element = None
                                
                                # 1. Direct child a tag
                                links = element.find_elements(By.TAG_NAME, "a")
                                if links:
                                    link_element = links[0]
                                
                                # 2. CSS selector for common Google link locations
                                if not link_element:
                                    link_selectors = [
                                        "a[ping]", 
                                        "a[jsname]", 
                                        "a[data-ved]",
                                        "div.yuRUbf > a",
                                        "div.DhN8Cf > a",
                                        "h3 > a",
                                        "a"
                                    ]
                                    for selector in link_selectors:
                                        try:
                                            links = element.find_elements(By.CSS_SELECTOR, selector)
                                            if links:
                                                link_element = links[0]
                                                break
                                        except Exception:
                                            continue
                                
                                # Extract URL if we found a link
                                if link_element:
                                    url = link_element.get_attribute("href")
                                    
                                    # Skip URLs that are not valid or already processed
                                    if not url or "google.com" in url or url in processed_urls:
                                        continue
                                    
                                    processed_urls.add(url)
                            except Exception as url_error:
                                logger.debug(f"Error extracting URL: {str(url_error)}")
                                continue  # Skip this result if we can't get a URL
                            
                            # Extract title
                            try:
                                # Try different approaches to find the title
                                title_element = None
                                
                                # 1. Look for h3 tags
                                h3s = element.find_elements(By.TAG_NAME, "h3")
                                if h3s:
                                    title_element = h3s[0]
                                
                                # 2. Common Google title selectors
                                if not title_element:
                                    title_selectors = [
                                        "a[href] h3", 
                                        ".LC20lb", 
                                        ".DKV0Md",
                                        "[role='heading']",
                                        ".vvjwJb"
                                    ]
                                    for selector in title_selectors:
                                        try:
                                            titles = element.find_elements(By.CSS_SELECTOR, selector)
                                            if titles and titles[0].text.strip():
                                                title_element = titles[0]
                                                break
                                        except Exception:
                                            continue
                                
                                # Extract text if we found a title element
                                if title_element:
                                    title = title_element.text.strip()
                                
                                # If still no title, try to get it from the link text
                                if not title and link_element:
                                    link_text = link_element.text.strip()
                                    if link_text and len(link_text) > 10:
                                        title = link_text
                                
                                # Default title if we couldn't extract one
                                if not title:
                                    title = "No title"
                            except Exception as title_error:
                                logger.debug(f"Error extracting title: {str(title_error)}")
                                title = "No title"
                            
                            # Extract snippet
                            try:
                                # Try different approaches to find the snippet
                                snippet_element = None
                                
                                # Try common Google snippet selectors
                                snippet_selectors = [
                                    ".VwiC3b", 
                                    ".lyLwlc",
                                    ".lEBKkf",
                                    ".MUxGbd",
                                    ".yXK7lf",
                                    ".CbQ4Cf",
                                    "span[style]"  # Often contains description text
                                ]
                                
                                for selector in snippet_selectors:
                                    try:
                                        snippets = element.find_elements(By.CSS_SELECTOR, selector)
                                        # Get the longest text which is likely the snippet
                                        longest_text = ""
                                        for s in snippets:
                                            if s.text and len(s.text) > len(longest_text):
                                                longest_text = s.text
                                        
                                        if longest_text:
                                            snippet = longest_text
                                            break
                                    except Exception:
                                        continue
                                
                                # If no snippet found, try to get any substantial text
                                if not snippet:
                                    # Try to find all spans with substantial text
                                    spans = element.find_elements(By.TAG_NAME, "span")
                                    candidate_texts = []
                                    for span in spans:
                                        span_text = span.text.strip()
                                        if span_text and len(span_text) > 40 and span_text != title:
                                            candidate_texts.append(span_text)
                                    
                                    if candidate_texts:
                                        # Use the longest text as the snippet
                                        snippet = max(candidate_texts, key=len)
                                
                                # Default snippet if we couldn't extract one
                                if not snippet:
                                    snippet = "No description available"
                            except Exception as snippet_error:
                                logger.debug(f"Error extracting snippet: {str(snippet_error)}")
                                snippet = "No description available"
                            
                            # Add result if we have at least a URL and title
                            if url and title != "No title":
                                position += 1
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "position": position
                                })
                            
                        except Exception as item_error:
                            logger.warning(f"Error processing search result item: {str(item_error)}")
                
                # Method 4: Last resort - direct extraction from all links
                if len(results) < 3:
                    logger.info("Not enough results found, trying direct link extraction")
                    
                    # Get all links on the page
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    logger.info(f"Found {len(all_links)} total links on the page")
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute("href")
                            text = link.text.strip()
                            
                            # Filter for good links
                            if (href and text and len(text) > 15 and 
                                href not in processed_urls and
                                href.startswith("http") and 
                                "google." not in href and
                                "/search?" not in href and
                                "/url?" not in href):
                                
                                position += 1
                                processed_urls.add(href)
                                
                                try:
                                    # Try to get the parent to look for a description
                                    parent = link.find_element(By.XPATH, "./..")
                                    all_text = parent.text
                                    
                                    # Remove the link text from the parent text
                                    description = all_text.replace(text, "").strip()
                                    if not description or len(description) < 40:
                                        description = "No description available"
                                except Exception:
                                    description = "No description available"
                                
                                results.append({
                                    "title": text,
                                    "url": href,
                                    "snippet": description,
                                    "position": position
                                })
                                
                                # Limit to a reasonable number of results
                                if len(results) >= settings.SEARCH_RESULTS_LIMIT:
                                    break
                        except Exception:
                            continue
                
                logger.info(f"Successfully extracted {len(results)} search results")
                
                # Sort results by position
                results.sort(key=lambda x: x["position"])
                
                # If we got some results, break the retry loop
                if results:
                    break
                else:
                    logger.warning("No search results extracted, will retry")
                    retry_count += 1
                    
            except Exception as e:
                logger.error(f"Error during Google search: {str(e)}")
                retry_count += 1
                
                # If this is the last retry and we have no results, try the URL-based approach
                if retry_count >= max_retries and not results:
                    logger.info("Trying URL-based search approach as last resort")
                    try:
                        # Restart browser for a fresh attempt
                        await self.stop()
                        await self.start()
                        
                        # Direct search with URL
                        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                        success = await self.navigate(search_url)
                        
                        if success:
                            # Use DuckDuckGo if Google is having issues
                            if not results:
                                logger.info("Trying DuckDuckGo as alternative search engine")
                                await self.navigate(f"https://duckduckgo.com/?q={query.replace(' ', '+')}")
                                time.sleep(2)
                                
                                # Extract links from DuckDuckGo
                                duck_links = self.driver.find_elements(By.CSS_SELECTOR, ".result__a")
                                position = 0
                                
                                for link in duck_links:
                                    try:
                                        href = link.get_attribute("href")
                                        if href and href not in processed_urls:
                                            position += 1
                                            processed_urls.add(href)
                                            
                                            # Get snippet from the result__snippet
                                            snippet = "No description available"
                                            try:
                                                parent = link.find_element(By.XPATH, "../..")
                                                snippet_element = parent.find_element(By.CSS_SELECTOR, ".result__snippet")
                                                if snippet_element:
                                                    snippet = snippet_element.text
                                            except Exception:
                                                pass
                                            
                                            results.append({
                                                "title": link.text,
                                                "url": href,
                                                "snippet": snippet,
                                                "position": position
                                            })
                                    except Exception:
                                        continue
                    except Exception as alt_error:
                        logger.error(f"Alternative search approach failed: {str(alt_error)}")
            
            # Sleep between retries
            if retry_count < max_retries and not results:
                logger.info(f"Retrying search after a short delay (attempt {retry_count+1}/{max_retries})")
                time.sleep(2)
        
        # Ensure we return the top X results as specified in settings
        return results[:settings.SEARCH_RESULTS_LIMIT]
    
    async def get_element_text(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """
        Get text from an element
        """
        if not self.driver:
            return ""
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text
        except Exception as e:
            logger.error(f"Error getting element text: {str(e)}")
            return ""
    
    async def scroll_to_bottom(self, scroll_pause_time=1.0):
        """
        Scroll to the bottom of the page gradually
        """
        if not self.driver:
            return
            
        try:
            # Get scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                time.sleep(scroll_pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {str(e)}")

# Create a singleton instance that can be imported by other modules
browser = SeleniumBrowser(headless=settings.SELENIUM_HEADLESS) 