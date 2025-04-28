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

         self.chrome_binary = os.environ.get('CHROME_BIN')
         self.chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
         
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
         
         # Additional stability options - especially for Render deployment
         options.add_argument('--disable-web-security')
         options.add_argument('--disable-features=IsolateOrigins,site-per-process')
         options.add_argument('--disable-blink-features=AutomationControlled')
         options.add_experimental_option('excludeSwitches', ['enable-automation'])
         options.add_experimental_option('useAutomationExtension', False)
         
         # Specific options for cloud environments
         options.add_argument('--window-size=1280,1696')
         options.add_argument('--ignore-certificate-errors')
         options.add_argument('--allow-running-insecure-content')
         options.add_argument('--disable-setuid-sandbox')
         options.add_argument('--single-process')
         
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
                     
                     # First attempt: Use ChromeDriverManager with explicit class from import 
                     driver_manager = ChromeDriverManager()
                     driver_path = driver_manager.install()
                     service = Service(driver_path)
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
                             # For Render, try specifying a fixed path where Chrome might be installed
                             if not sys.platform.startswith('win'):
                                 # On Linux (including Render), Chrome is often at /usr/bin/chromium-browser
                                 chrome_paths = [
                                     "/usr/bin/chromium-browser",
                                     "/usr/bin/chromium",
                                     "/usr/bin/google-chrome",
                                     "/usr/bin/google-chrome-stable"
                                 ]
                                 
                                 for chrome_path in chrome_paths:
                                     if os.path.exists(chrome_path):
                                         logger.info(f"Found Chrome at {chrome_path}")
                                         options.binary_location = chrome_path
                                         break
                                         
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
                     cookie_buttons = self.driver.find_elements(By.XPATH, 
                         "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Accept')]")
                     if cookie_buttons:
                         cookie_buttons[0].click()
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
                         WebDriverWait(self.driver, 5).until(
                             EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                         )
                         logger.info(f"Search results loaded with selector: {selector}")
                         results_loaded = True
                         break
                     except TimeoutException:
                         continue
                 
                 if not results_loaded:
                     logger.warning("Failed to detect search results with any selectors")
                 
                 # Save page source for debugging - this helps diagnose issues on Render
                 debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
                 os.makedirs(debug_dir, exist_ok=True)
                 with open(os.path.join(debug_dir, "google_search.html"), "w", encoding="utf-8") as f:
                     f.write(self.driver.page_source)
                 logger.info("Saved search page source for debugging")
                 
                 # Give the page a moment to stabilize
                 time.sleep(3)
                 
                 # Try the more direct approach to find all links first
                 logger.info("Trying direct link extraction")
                 links = self.driver.find_elements(By.TAG_NAME, "a")
                 logger.info(f"Found {len(links)} total links on the page")
                 
                 # Process links - focusing on those that are likely search results
                 position = 0
                 processed_urls = set()
                 
                 for link in links:
                     try:
                         # Skip navigation/menu links by checking attributes
                         classes = link.get_attribute("class") or ""
                         href = link.get_attribute("href") or ""
                         
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
                         
                         # Get link text - ideally this is the title
                         link_text = link.text.strip()
                         
                         # If link has no text, try to find h3 within ancestors
                         if not link_text:
                             try:
                                 parent = link.find_element(By.XPATH, "./..")
                                 h3s = parent.find_elements(By.TAG_NAME, "h3")
                                 if h3s:
                                     link_text = h3s[0].text.strip()
                             except Exception:
                                 pass
                         
                         # Only include links that have text and look like result titles
                         if link_text and len(link_text) > 10:
                             position += 1
                             processed_urls.add(href)
                             
                             # Look for snippet text near the link
                             snippet = "No description available"
                             try:
                                 # Try different ways to find snippet text
                                 # Method 1: Look in nearby spans (common in Google results)
                                 parent_div = link.find_element(By.XPATH, "./../..")
                                 spans = parent_div.find_elements(By.TAG_NAME, "span")
                                 snippet_candidates = []
                                 
                                 for span in spans:
                                     span_text = span.text.strip()
                                     if span_text and span_text != link_text and len(span_text) > 40:
                                         snippet_candidates.append(span_text)
                                         
                                 if snippet_candidates:
                                     snippet = snippet_candidates[0]
                                 else:
                                     # Method 2: Look in nearby divs
                                     divs = parent_div.find_elements(By.TAG_NAME, "div")
                                     for div in divs:
                                         div_text = div.text.strip()
                                         if div_text and div_text != link_text and len(div_text) > 40:
                                             snippet = div_text
                                             break
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