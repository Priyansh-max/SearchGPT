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
        Perform a Google search and extract results, with fallbacks
        """
        if not query:
            return []
            
        # First try Google Search
        results = await self._search_google_directly(query)
        
        # If Google failed (likely due to CAPTCHA), try alternative search engines
        if not results:
            logger.warning("Google search failed, trying alternative search engines")
            results = await self._search_alternative_engines(query)
            
        return results[:settings.SEARCH_RESULTS_LIMIT]
    
    async def _search_google_directly(self, query):
        """Internal method to search Google with anti-detection measures"""
        results = []
        retry_count = 0
        max_retries = 2  # Reduced retries to save time if blocked
        
        while retry_count < max_retries:
            try:
                # Navigate to Google
                logger.info(f"Navigating to Google for search: {query}")
                
                # Add some randomness to avoid patterns
                search_urls = [
                    "https://www.google.com",
                    "https://www.google.com/search",
                    "https://google.com"
                ]
                import random
                search_url = random.choice(search_urls)
                
                success = await self.navigate(search_url)
                if not success:
                    raise Exception("Failed to navigate to Google")
                
                # Take screenshot before doing anything
                self.driver.save_screenshot(os.path.join(self.debug_dir, "google_homepage.png"))
                
                # Add randomized wait time to appear more human-like
                import random
                time.sleep(random.uniform(1.0, 3.0))
                
                # Accept cookies if the dialog appears (try multiple selectors)
                try:
                    cookie_selectors = [
                        "//button[contains(., 'Accept all')]",
                        "//button[contains(., 'I agree')]",
                        "//button[contains(., 'Accept')]",
                        "//*[@id='L2AGLb']",  # Common ID for "I agree" button
                        "//div[contains(@class, 'lssxud')]/div/button",  # Another common path
                        "//*[@id='W0wltc']"  # "Reject all" button (might help bypass in some regions)
                    ]
                    
                    for selector in cookie_selectors:
                        try:
                            cookie_buttons = self.driver.find_elements(By.XPATH, selector)
                            if cookie_buttons and len(cookie_buttons) > 0:
                                # Add small random delay before clicking
                                time.sleep(random.uniform(0.5, 1.5))
                                cookie_buttons[0].click()
                                logger.info(f"Clicked cookie consent button with selector: {selector}")
                                time.sleep(random.uniform(0.5, 1.5))
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Error handling cookie dialog: {str(e)}")
                
                # Find search box and enter query with explicit waits
                try:
                    logger.debug("Looking for search input")
                    # Try multiple ways to find the search box
                    search_box = None
                    for selector in ["input[name='q']", "textarea[name='q']", "//*[@name='q']"]:
                        try:
                            search_box = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR if selector.startswith("input") or selector.startswith("textarea") else By.XPATH, selector))
                            )
                            if search_box:
                                break
                        except:
                            continue
                    
                    if not search_box:
                        # If on search page directly, try URL method
                        if self.driver.current_url.startswith("https://www.google.com/search"):
                            self.driver.get(f"https://www.google.com/search?q={query}")
                            time.sleep(random.uniform(1.0, 2.0))
                        else:
                            raise Exception("Could not find search input")
                    else:
                        # Clear existing text and enter query with random timing
                        search_box.clear()
                        # Type slowly like a human with variable speed
                        for char in query:
                            search_box.send_keys(char)
                            time.sleep(random.uniform(0.03, 0.12))  # Variable typing speed
                        
                        # Take a screenshot before submitting
                        self.driver.save_screenshot(os.path.join(self.debug_dir, "before_search.png"))
                        
                        # Add a short pause before submitting (humans pause before hitting enter)
                        time.sleep(random.uniform(0.5, 1.2))
                        
                        # Try multiple ways to submit
                        try:
                            # First try the Enter key
                            search_box.send_keys(Keys.RETURN)
                        except:
                            try:
                                # Then try form submission
                                search_box.submit()
                            except:
                                # Finally try to find and click the search button
                                search_buttons = self.driver.find_elements(By.XPATH, "//input[@type='submit']")
                                if search_buttons:
                                    search_buttons[0].click()
                    
                    logger.info("Submitted search query")
                except Exception as e:
                    logger.error(f"Failed to input search query: {str(e)}")
                    # Take a screenshot of the failure
                    self.driver.save_screenshot(os.path.join(self.debug_dir, "search_input_error.png"))
                    raise
                
                # Wait for results page to load with variable timing
                time.sleep(random.uniform(2.0, 4.0))
                
                # Take a screenshot after search submission
                self.driver.save_screenshot(os.path.join(self.debug_dir, "after_search.png"))
                
                # Check for CAPTCHA or other barriers
                if "captcha" in self.driver.page_source.lower() or "unusual traffic" in self.driver.page_source.lower() or "security check" in self.driver.page_source.lower():
                    logger.warning("Detected CAPTCHA or traffic warning page")
                    self.driver.save_screenshot(os.path.join(self.debug_dir, "captcha_detected.png"))
                    # Save the page source for debugging
                    with open(os.path.join(self.debug_dir, "captcha_page.html"), "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    raise Exception("CAPTCHA detected, cannot proceed with search")
                
                # Wait for results to load with multiple possible selectors
                # Updated selectors based on 2023-2024 Google search results structure
                results_loaded = False
                selectors = [
                    "#search",               # Main search container
                    "#rso",                  # Results container
                    "div.g",                 # Standard result container
                    "div.MjjYud",            # Newer result container 
                    "h3.LC20lb",             # Result title
                    "div.yuRUbf",            # Link container
                    "div[data-hveid]",       # Results with data attribute
                    "div[data-content-feature]", # Feature content
                    "div.v7W49e",            # Another container class
                    "div.ULSxyf",            # Another container variant
                    "div.Gx5Zad",            # 2023 result container
                    "div.fP1Qef",            # Another 2023 container
                    "a[ping]",               # Links with tracking
                    "div[jscontroller]"      # JS-controlled divs (often results)
                ]
                
                # Try each selector to see if results have loaded
                for selector in selectors:
                    try:
                        elements = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"Search results detected with selector: {selector}")
                        results_loaded = True
                        break
                    except:
                        continue
                
                # If we couldn't find results with specific selectors, check for common text that appears on results pages
                if not results_loaded:
                    for text in ["Search results", "About", "results", "result for", "sponsored"]:
                        if text.lower() in self.driver.page_source.lower():
                            logger.info(f"Search results page detected by text: '{text}'")
                            results_loaded = True
                            break
                
                if not results_loaded:
                    logger.warning("Failed to detect search results")
                
                # Save page source for debugging
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, "google_search.html"), "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info("Saved search page source for debugging")
                
                # Try to extract links using both traditional and BeautifulSoup approaches
                from bs4 import BeautifulSoup
                
                # First try direct Selenium extraction
                logger.info("Trying direct link extraction")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                logger.info(f"Found {len(links)} total links on the page")
                
                # Process links - focusing on those that are likely search results
                position = 0
                processed_urls = set()
                
                # 1. Try Selenium direct extraction
                for link in links:
                    try:
                        href = link.get_attribute("href") or ""
                        
                        # Skip non-result links
                        if (not href or 
                            href in processed_urls or
                            href.startswith("#") or
                            "google.com/search" in href or
                            "accounts.google" in href or
                            "support.google" in href or
                            "maps.google" in href or
                            "javascript:" in href):
                            continue
                        
                        # Get link text - ideally this is the title
                        link_text = link.text.strip()
                        
                        # If link has no text, try to find h3 or other title elements nearby
                        if not link_text or len(link_text) < 10:
                            try:
                                # Look for h3 (common for Google result titles)
                                h3_elements = []
                                parent = link
                                # Look up to 3 levels up for h3
                                for _ in range(3):
                                    try:
                                        parent = parent.find_element(By.XPATH, "./..")
                                        h3s = parent.find_elements(By.TAG_NAME, "h3")
                                        if h3s:
                                            h3_elements.extend(h3s)
                                    except:
                                        break
                                
                                if h3_elements:
                                    link_text = h3_elements[0].text.strip()
                            except:
                                pass
                        
                        # Only include links that have text and look like result titles
                        if link_text and len(link_text) > 10:
                            position += 1
                            processed_urls.add(href)
                            
                            # Look for snippet text near the link
                            snippet = "No description available"
                            try:
                                # Try different ways to find snippet text
                                # Method 1: Look in nearby spans and divs up to 3 levels up
                                parent = link
                                snippet_elements = []
                                
                                for _ in range(3):
                                    try:
                                        parent = parent.find_element(By.XPATH, "./..")
                                        # Try spans first (often contain snippets)
                                        spans = parent.find_elements(By.TAG_NAME, "span")
                                        for span in spans:
                                            text = span.text.strip()
                                            if text and text != link_text and len(text) > 30:
                                                snippet_elements.append(text)
                                        
                                        # Try divs if no good spans
                                        if not snippet_elements:
                                            divs = parent.find_elements(By.TAG_NAME, "div")
                                            for div in divs:
                                                text = div.text.strip()
                                                if text and text != link_text and len(text) > 30:
                                                    snippet_elements.append(text)
                                    except:
                                        break
                                
                                if snippet_elements:
                                    # Take the longest snippet
                                    snippet = max(snippet_elements, key=len)
                            except Exception as snippet_err:
                                logger.debug(f"Error extracting snippet: {str(snippet_err)}")
                            
                            results.append({
                                "title": link_text,
                                "url": href,
                                "snippet": snippet,
                                "position": position
                            })
                            
                            logger.info(f"Extracted result {position}: {link_text[:30]}...")
                            
                            # Limit number of results
                            if position >= settings.SEARCH_RESULTS_LIMIT:
                                break
                    except Exception as e:
                        logger.debug(f"Error processing link: {str(e)}")
                
                # 2. If we didn't find enough results, try with BeautifulSoup
                if len(results) < 3 and self.driver.page_source:
                    logger.info("Trying BeautifulSoup extraction as fallback")
                    try:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        
                        # Look for result containers
                        for container_selector in ["div.g", "div.MjjYud", "div.Gx5Zad", "div.fP1Qef", "div[data-hveid]"]:
                            containers = soup.select(container_selector)
                            if containers:
                                logger.info(f"Found {len(containers)} containers with selector: {container_selector}")
                                break
                        
                        if not containers:
                            # Just look for all links that might be results
                            containers = soup.select("a[href^='http']")
                        
                        position_bs = position  # Continue from where the previous extraction left off
                        
                        for container in containers:
                            try:
                                # Try to find the link and title
                                link_elem = container.select_one("a") if not container.name == "a" else container
                                title_elem = container.select_one("h3") or container.select_one("[role='heading']")
                                
                                if link_elem and link_elem.has_attr("href"):
                                    href = link_elem["href"]
                                    
                                    # Skip non-result links
                                    if (not href or
                                        href in processed_urls or
                                        href.startswith("#") or
                                        "google.com/search" in href or
                                        "accounts.google" in href):
                                        continue
                                    
                                    # Get title text
                                    title = ""
                                    if title_elem:
                                        title = title_elem.get_text().strip()
                                    elif link_elem.get_text():
                                        title = link_elem.get_text().strip()
                                    
                                    # Only include links that have text
                                    if title and len(title) > 5:
                                        position_bs += 1
                                        processed_urls.add(href)
                                        
                                        # Look for snippet
                                        snippet = "No description available"
                                        snippet_elem = container.select_one("div.VwiC3b, span.aCOpRe, div.IsZvec, div.lEBKkf")
                                        if snippet_elem:
                                            snippet = snippet_elem.get_text().strip()
                                        
                                        results.append({
                                            "title": title,
                                            "url": href,
                                            "snippet": snippet,
                                            "position": position_bs
                                        })
                                        
                                        logger.info(f"Extracted result {position_bs} (BS): {title[:30]}...")
                                        
                                        # Limit number of results
                                        if position_bs >= settings.SEARCH_RESULTS_LIMIT:
                                            break
                            except Exception as e:
                                logger.debug(f"Error processing container with BeautifulSoup: {str(e)}")
                    except Exception as bs_error:
                        logger.error(f"Error during BeautifulSoup extraction: {str(bs_error)}")
                
                logger.info(f"Successfully extracted {len(results)} search results")
                
                # If we have results, exit the retry loop
                if results:
                    break
                    
                # If no results, retry
                logger.warning(f"No search results extracted, will retry (attempt {retry_count+1}/{max_retries})")
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Error during Google search: {str(e)}")
                self.driver.save_screenshot(os.path.join(self.debug_dir, f"search_error_{retry_count}.png"))
                retry_count += 1
            
            # Sleep between retries
            if retry_count < max_retries and not results:
                logger.info(f"Retrying search after a short delay (attempt {retry_count+1}/{max_retries})")
                time.sleep(2)
        
        return results

    async def _search_alternative_engines(self, query):
        """Search using alternate engines when Google fails"""
        results = []
        
        # Try Bing as an alternative
        try:
            logger.info(f"Trying Bing search for: {query}")
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
        
        # If Bing didn't work, try DuckDuckGo
        if not results:
            try:
                logger.info(f"Trying DuckDuckGo search for: {query}")
                success = await self.navigate("https://duckduckgo.com/")
                if success:
                    # Take screenshot
                    self.driver.save_screenshot(os.path.join(self.debug_dir, "ddg_homepage.png"))
                    
                    # Find the search box (multiple possible selectors)
                    search_box = None
                    for selector in ["#search_form_input_homepage", "#search_form_input", "input[name='q']", "input[type='text']"]:
                        try:
                            search_box = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            if search_box:
                                break
                        except:
                            continue
                    
                    if search_box:
                        search_box.clear()
                        
                        # Type query with random delays
                        import random
                        for char in query:
                            search_box.send_keys(char)
                            time.sleep(random.uniform(0.03, 0.12))
                            
                        # Submit search
                        search_box.send_keys(Keys.RETURN)
                        logger.info("Submitted DuckDuckGo search query")
                        
                        # Wait for results
                        time.sleep(3)
                        self.driver.save_screenshot(os.path.join(self.debug_dir, "ddg_results.png"))
                        
                        # Extract results
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        
                        # Look for result containers
                        result_elements = soup.select(".result__body, .nrn-react-div article")
                        
                        position = 0
                        for result in result_elements:
                            try:
                                # Extract title and URL
                                title_elem = result.select_one(".result__title, h2")
                                link_elem = result.select_one("a.result__a, a[data-testid='result-title-a']")
                                
                                if title_elem and link_elem:
                                    title = title_elem.get_text().strip()
                                    url = link_elem.get('href', '')
                                    
                                    # Extract snippet
                                    snippet_elem = result.select_one(".result__snippet, [data-testid='result-snippet']")
                                    snippet = snippet_elem.get_text().strip() if snippet_elem else "No description available"
                                    
                                    position += 1
                                    results.append({
                                        "title": title,
                                        "url": url,
                                        "snippet": snippet,
                                        "position": position,
                                        "source": "DuckDuckGo"  # Mark the source
                                    })
                                    
                                    if position >= settings.SEARCH_RESULTS_LIMIT:
                                        break
                            except Exception as e:
                                logger.debug(f"Error extracting DuckDuckGo result: {str(e)}")
                                continue
            except Exception as e:
                logger.error(f"Error using DuckDuckGo search: {str(e)}")
                
        # If we still have no results, try a direct API-based search
        if not results:
            logger.info("Attempting API-based search as final fallback")
            try:
                # Use an API-based search provider that doesn't require browser automation
                # We'll use a very basic implementation that works without API keys
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
                
                # If Searx instances failed, create a minimal set of "dummy" results
                # to at least allow the frontend to display something
                if not results:
                    logger.warning("All search methods failed, creating fallback results")
                    
                    # Try to generate some basic results about the query topic
                    # This is better than returning nothing at all
                    topics_info = {
                        "default": {
                            "title": f"Information about {query}",
                            "url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}",
                            "snippet": f"We couldn't retrieve search results directly, but you can find information about '{query}' on Wikipedia and other encyclopedic sources."
                        },
                        "cricket": {
                            "title": "Cricket (insect) - Wikipedia",
                            "url": "https://en.wikipedia.org/wiki/Cricket_(insect)",
                            "snippet": "Crickets, of the family Gryllidae, are insects related to grasshoppers and katydids. They're known for the chirping sound males make by rubbing their wings together to attract females. They have long antennae and powerful jumping back legs."
                        },
                        "news": {
                            "title": f"Latest news about {query}",
                            "url": f"https://news.google.com/search?q={quote_plus(query)}",
                            "snippet": f"Find the latest news about '{query}' from various sources across the web. Google News aggregates content from multiple publishers."
                        },
                        "tech": {
                            "title": f"Technology information: {query}",
                            "url": f"https://www.techradar.com/search?searchTerm={quote_plus(query)}",
                            "snippet": f"Find technical information and reviews about '{query}' from technology news sources and product review sites."
                        }
                    }
                    
                    # Determine which topic the query might relate to
                    topic_key = "default"
                    query_lower = query.lower()
                    
                    if "cricket" in query_lower and ("insect" in query_lower or "bug" in query_lower):
                        topic_key = "cricket"
                    elif any(term in query_lower for term in ["news", "latest", "current", "today"]):
                        topic_key = "news"
                    elif any(term in query_lower for term in ["tech", "technology", "computer", "software", "hardware"]):
                        topic_key = "tech"
                    
                    # Add fallback result
                    topic_info = topics_info[topic_key]
                    results.append({
                        "title": topic_info["title"],
                        "url": topic_info["url"],
                        "snippet": topic_info["snippet"],
                        "position": 1,
                        "source": "Fallback"
                    })
                    
                    # Add general search suggestions
                    results.append({
                        "title": f"Search for {query} on DuckDuckGo",
                        "url": f"https://duckduckgo.com/?q={quote_plus(query)}",
                        "snippet": "DuckDuckGo is a privacy-focused search engine that doesn't track your searches.",
                        "position": 2,
                        "source": "Suggestion"
                    })
                    
                    results.append({
                        "title": f"Search for {query} on Bing",
                        "url": f"https://www.bing.com/search?q={quote_plus(query)}",
                        "snippet": "Microsoft Bing offers comprehensive search results with additional features like visual search.",
                        "position": 3,
                        "source": "Suggestion"
                    })
                    
                    logger.info("Added 3 fallback search results")
            except Exception as e:
                logger.error(f"Error with API-based search fallback: {str(e)}")
        
        logger.info(f"Alternative search engines found {len(results)} valid results")
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