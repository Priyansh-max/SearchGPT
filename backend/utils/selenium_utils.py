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
import traceback
from shutil import which
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

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
         self.max_retry_count = 1
         self.debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")

    async def start(self):
        """Start the Selenium browser"""
        if self.driver:
            logger.info("Browser already started")
            return True
            
        try:
            # Log the system architecture
            system_arch = platform.architecture()[0]
            logger.info(f"System architecture: {system_arch}")
            
            # Set up Chrome options with anti-detection measures
            chrome_options = Options()
            
            # Set up Chrome options for headless mode with improved stealth
            if self.headless:
                # Use Selenium's new headless mode
                chrome_options.add_argument("--headless=new")
                
                # Add window size that looks like a normal desktop
                chrome_options.add_argument("--window-size=1920,1080")
                
                # Disable automation flags
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option("useAutomationExtension", False)
                
                # Hide WebDriver usage with CDP
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Add additional options for performance and compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            # Add more humanlike settings
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--lang=en-US,en;q=0.9")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-popup-blocking")
            
            # Use a more realistic user agent to reduce detection
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ]
            import random
            user_agent = random.choice(user_agents)
            logger.info(f"Using user agent: {user_agent}")
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Create debug directory if it doesn't exist
            os.makedirs(self.debug_dir, exist_ok=True)
            
            # Check if we're running in Docker
            is_docker = os.environ.get('DOCKER_CONTAINER', False) or os.path.exists('/.dockerenv')
            logger.info(f"Running in Docker: {is_docker}")
            
            # Check for environment variables 
            chrome_path = os.environ.get('CHROME_BIN', None)
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', None)
            
            logger.info(f"Chrome path from env: {chrome_path}")
            logger.info(f"ChromeDriver path from env: {chromedriver_path}")
            
            webdriver_service = None
            
            # First priority: Use the ChromeDriver specified in environment variables
            if chromedriver_path and os.path.exists(chromedriver_path):
                logger.info(f"Using system ChromeDriver at: {chromedriver_path}")
                webdriver_service = Service(executable_path=chromedriver_path)
            else:
                # Second priority: Search for ChromeDriver in PATH
                path_chromedriver = which('chromedriver')
                if path_chromedriver:
                    logger.info(f"Found ChromeDriver in PATH: {path_chromedriver}")
                    webdriver_service = Service(executable_path=path_chromedriver)
                else:
                    # Last resort: Use webdriver_manager to download ChromeDriver
                    logger.info("No system ChromeDriver found, using webdriver_manager")
                    try:
                        driver_path = ChromeDriverManager().install()
                        logger.info(f"Downloaded ChromeDriver to: {driver_path}")
                        webdriver_service = Service(driver_path)
                    except Exception as e:
                        logger.error(f"Failed to download ChromeDriver: {str(e)}")
                        raise Exception("Could not find or install ChromeDriver")
            
            # Set Chrome binary location if specified in environment
            if chrome_path and os.path.exists(chrome_path):
                logger.info(f"Setting Chrome binary path to: {chrome_path}")
                chrome_options.binary_location = chrome_path
            
            # Start the browser
            logger.info("Launching Chrome browser...")
            self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(settings.SELENIUM_TIMEOUT)
            
            # Execute JavaScript to hide automation
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en', 'fr']
                    });
                """
            })
            
            # Take screenshot to confirm browser started
            self.driver.save_screenshot(os.path.join(self.debug_dir, "browser_started.png"))
            
            logger.info("Browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    #not used anywhere
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

    #not used anywhere
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

    #not used anywhere
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
    #not used anywhere
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
        Perform a web search using Bing directly (renamed for compatibility)
        """
        if not query:
            return []
            
        # Search with Bing directly
        results = await self._search_bing(query)
        
        # If Bing failed, try alternative search engines
        if not results:
            logger.warning("Bing search failed, trying API-based alternatives")
            results = await self._search_api_based(query)
            
        return results[:settings.SEARCH_RESULTS_LIMIT]
        
    async def _search_google_directly(self, query):
        """
        Legacy method kept for compatibility, redirects to Bing search
        """
        logger.warning("Google search is no longer used due to CAPTCHA issues, redirecting to Bing")
        return await self._search_bing(query)
    
    async def _search_bing(self, query):
        """Search using Bing search engine"""
        results = []
        retry_count = 0
        max_retries = 2
        
        while retry_count < max_retries:
            try:
                logger.info(f"Directly searching Bing for: {query}")
                success = await self.navigate("https://www.bing.com/")
                if success:
                    # Take screenshot
                    self.driver.save_screenshot(os.path.join(self.debug_dir, "bing_homepage.png"))
                    
                    # Find the search box
                    try:
                        search_box = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.ID, "sb_form_q"))
                        )
                        search_box.clear()
                        
                        # Type query with random delays
                        import random
                        for char in query:
                            search_box.send_keys(char)
                            time.sleep(random.uniform(0.03, 0.12))
                            
                        # Submit search
                        search_box.send_keys(Keys.RETURN)
                        logger.info("Submitted Bing search query")
                        
                        # Wait for results
                        time.sleep(3)
                        self.driver.save_screenshot(os.path.join(self.debug_dir, "bing_results.png"))
                        
                        # Save page source for debugging
                        with open(os.path.join(self.debug_dir, "bing_results.html"), "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        
                        # First try direct extraction
                        links = self.driver.find_elements(By.CSS_SELECTOR, "#b_results > li.b_algo")
                        logger.info(f"Found {len(links)} Bing results")
                        
                        position = 0
                        for result in links:
                            try:
                                # Extract title
                                title_elem = result.find_element(By.CSS_SELECTOR, "h2 a")
                                title = title_elem.text.strip()
                                
                                # Extract URL - first from the main link
                                url = title_elem.get_attribute("href")
                                
                                # Ensure URL is not None
                                if not url:
                                    # Try getting the URL from the cite element
                                    try:
                                        cite_elem = result.find_element(By.CSS_SELECTOR, "cite")
                                        cite_url = cite_elem.text.strip()
                                        if cite_url and cite_url.startswith(('http://', 'https://')):
                                            url = cite_url
                                        else:
                                            # Construct a URL if possible
                                            if cite_url and not cite_url.startswith(('http://', 'https://')):
                                                url = "https://" + cite_url
                                    except:
                                        # Skip this result if we can't get a valid URL
                                        logger.warning(f"Skipping Bing result with no URL: {title[:30]}...")
                                        continue
                                
                                # Skip if URL is still None or empty
                                if not url:
                                    logger.warning(f"Skipping Bing result with no URL: {title[:30]}...")
                                    continue
                                
                                # Extract snippet
                                snippet = "No description available"
                                try:
                                    # Try different potential selectors for snippets
                                    for snippet_selector in ["p", ".b_caption p", ".b_snippet"]:
                                        try:
                                            snippet_elem = result.find_element(By.CSS_SELECTOR, snippet_selector)
                                            potential_snippet = snippet_elem.text.strip()
                                            if potential_snippet and len(potential_snippet) > 20:
                                                snippet = potential_snippet
                                                break
                                        except:
                                            continue
                                except:
                                    # Keep default snippet if extraction fails
                                    pass
                                
                                # Validate that we have all required fields before adding the result
                                if title and url and snippet:
                                    position += 1
                                    logger.info(f"Extracted Bing result {position}: '{title[:30]}...' -> {url[:50]}...")
                                    
                                    results.append({
                                        "title": title,
                                        "url": url,
                                        "snippet": snippet,
                                        "position": position,
                                        "source": "Bing"  # Mark the source
                                    })
                                    
                                    if position >= settings.SEARCH_RESULTS_LIMIT:
                                        break
                                else:
                                    logger.warning(f"Skipping incomplete Bing result: title={bool(title)}, url={bool(url)}, snippet={bool(snippet)}")
                            except Exception as e:
                                logger.debug(f"Error extracting Bing result: {str(e)}")
                                continue
                        
                        # If we didn't get enough results with direct extraction, try BeautifulSoup
                        if len(results) < 3:
                            logger.info("Trying BeautifulSoup extraction for Bing results")
                            try:
                                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                                result_elements = soup.select("#b_results > li.b_algo")
                                
                                for result in result_elements:
                                    try:
                                        # Extract title and URL
                                        title_elem = result.select_one("h2 a")
                                        if not title_elem:
                                            continue
                                            
                                        title = title_elem.get_text().strip()
                                        url = title_elem.get('href', '')
                                        
                                        # Ensure URL is not None or empty
                                        if not url:
                                            # Try getting the URL from the cite element
                                            cite_elem = result.select_one("cite")
                                            if cite_elem:
                                                cite_url = cite_elem.get_text().strip()
                                                if cite_url and cite_url.startswith(('http://', 'https://')):
                                                    url = cite_url
                                                elif cite_url and not cite_url.startswith(('http://', 'https://')):
                                                    url = "https://" + cite_url
                                        
                                        # Skip if URL is still None or empty
                                        if not url:
                                            continue
                                        
                                        # Extract snippet
                                        snippet = "No description available"
                                        snippet_elem = result.select_one("p") or result.select_one(".b_caption p") or result.select_one(".b_snippet")
                                        if snippet_elem:
                                            snippet = snippet_elem.get_text().strip()
                                        
                                        # Validate that we have all required fields before adding the result
                                        if title and url and snippet:
                                            position += 1
                                            logger.info(f"Extracted Bing result {position} (BS): '{title[:30]}...' -> {url[:50]}...")
                                            
                                            results.append({
                                                "title": title,
                                                "url": url,
                                                "snippet": snippet,
                                                "position": position,
                                                "source": "Bing (BS)"  # Mark the source
                                            })
                                            
                                            if position >= settings.SEARCH_RESULTS_LIMIT:
                                                break
                                    except Exception as e:
                                        logger.debug(f"Error extracting Bing result with BeautifulSoup: {str(e)}")
                                        continue
                            except Exception as bs_error:
                                logger.error(f"Error during BeautifulSoup extraction for Bing: {str(bs_error)}")
                    except Exception as e:
                        logger.error(f"Error with Bing search input: {str(e)}")
            except Exception as e:
                logger.error(f"Error using Bing search: {str(e)}")
                retry_count += 1
                time.sleep(2)
                continue
            
            # If we have results, break out of retry loop
            if results:
                break
                
            retry_count += 1
        
        return results
        
    async def _search_alternative_engines(self, query):
        """Legacy method kept for compatibility, redirects to API-based search"""
        logger.warning("Using API-based search instead of alternative engines")
        return await self._search_api_based(query)
    
    async def _search_api_based(self, query):
        """Search using API-based providers that don't require browser automation"""
        results = []
        
        logger.info("Attempting API-based search")
        try:
            # Use an API-based search provider that doesn't require browser automation
            import requests
            from urllib.parse import quote_plus
            
            # Try Searx, a privacy-focused metasearch engine
            searx_instances = [
                "https://searx.be/search",
                "https://search.disroot.org/search",
                "https://search.mdosch.de/search"
            ]
            
            for instance in searx_instances:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9"
                    }
                    
                    params = {
                        "q": query,
                        "format": "json"
                    }
                    
                    response = requests.get(instance, params=params, headers=headers, timeout=10)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            if "results" in data and len(data["results"]) > 0:
                                position = 0
                                
                                for item in data["results"]:
                                    try:
                                        title = item.get("title", "").strip()
                                        url = item.get("url", "")
                                        snippet = item.get("content", item.get("snippet", "No description available")).strip()
                                        
                                        # Validate that we have all required fields
                                        if title and url and snippet:
                                            position += 1
                                            
                                            results.append({
                                                "title": title,
                                                "url": url,
                                                "snippet": snippet,
                                                "position": position,
                                                "source": "Searx API"
                                            })
                                            
                                            if position >= settings.SEARCH_RESULTS_LIMIT:
                                                break
                                    except:
                                        continue
                                
                                if results:
                                    logger.info(f"Found {len(results)} results using Searx API")
                                    break
                        except:
                            # If JSON parsing fails, the instance may not support JSON output
                            continue
                except:
                    continue
            
            #show we are facing heavy traffic

            if not results:
                logger.warning("All search methods failed, creating fallback results")
                results.append({
                    "title":"We are facing heavy traffic, please try again later",
                    "url":"https://www.bing.com/search?q=We+are+facing+heavy+traffic,+please+try+again+later",
                    "snippet":"We are facing heavy traffic, please try again later",
                    "position":1,
                    "source":"API-based search"
                })
                
                logger.info("Added 1 fallback search results")
        except Exception as e:
            logger.error(f"Error with API-based search fallback: {str(e)}")
        
        logger.info(f"API-based search found {len(results)} valid results")
        return results
     
    #not used anywhere
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
             # Check if document.body exists and has a scrollHeight property
             has_body = self.driver.execute_script("""
                 return (document.body !== null && 
                         document.body !== undefined && 
                         typeof document.body.scrollHeight !== 'undefined');
             """)
             
             if not has_body:
                 # Try to use document.documentElement (HTML) instead
                 has_html = self.driver.execute_script("""
                     return (document.documentElement !== null && 
                             document.documentElement !== undefined && 
                             typeof document.documentElement.scrollHeight !== 'undefined');
                 """)
                 
                 if not has_html:
                     logger.warning("Cannot scroll as both document.body and document.documentElement are missing scrollHeight")
                     return
                 
                 # Use document.documentElement for scrolling
                 scroll_script = "document.documentElement.scrollHeight"
                 scroll_to_script = "window.scrollTo(0, document.documentElement.scrollHeight);"
             else:
                 # Use document.body for scrolling (default)
                 scroll_script = "document.body.scrollHeight"
                 scroll_to_script = "window.scrollTo(0, document.body.scrollHeight);"
             
             # Get initial scroll height
             last_height = self.driver.execute_script(f"return {scroll_script}")
             
             # Scroll down in multiple steps to trigger lazy loading
             scroll_attempts = 0
             max_attempts = 5  # Limit attempts to prevent infinite loops
             
             while scroll_attempts < max_attempts:
                 # Scroll down to bottom
                 self.driver.execute_script(scroll_to_script)
                 
                 # Wait to load page
                 time.sleep(scroll_pause_time)
                 
                 # Calculate new scroll height and compare with last scroll height
                 new_height = self.driver.execute_script(f"return {scroll_script}")
                 
                 if new_height == last_height:
                     # We've reached the bottom
                     break
                     
                 last_height = new_height
                 scroll_attempts += 1
                 
         except Exception as e:
             logger.error(f"Error scrolling to bottom: {str(e)}")
 
# Create a singleton instance that can be imported by other modules
browser = SeleniumBrowser(headless=settings.SELENIUM_HEADLESS) 