import asyncio
import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config import settings
import time

logger = logging.getLogger(__name__)

class PlaywrightBrowser:
    """
    A utility class for Playwright browser automation - replacing Selenium
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.timeout = settings.PLAYWRIGHT_TIMEOUT * 1000  # Convert to milliseconds
        
    async def start(self):
        """Start the Playwright browser"""
        if self.browser:
            logger.info("Browser already started")
            return True
            
        try:
            logger.info("Starting Playwright browser...")
            
            # Launch playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with optimized settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-notifications',
                    '--disable-popup-blocking',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create context with stealth settings
            self.context = await self.browser.new_context(
                user_agent=settings.USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(self.timeout)
            
            # Add stealth script
            await self.page.add_init_script("""
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
            """)
            
            logger.info("Playwright browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Playwright browser: {str(e)}")
            return False
    
    async def stop(self):
        """Stop the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("Playwright browser stopped")
        except Exception as e:
            logger.error(f"Error stopping Playwright browser: {str(e)}")
    
    async def navigate(self, url: str) -> bool:
        """Navigate to a URL"""
        if not self.page:
            await self.start()
            
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='domcontentloaded')
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False
    
    async def get_page_source(self) -> str:
        """Get the page source"""
        if not self.page:
            return ""
            
        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Error getting page source: {str(e)}")
            return ""
    
    async def get_current_url(self) -> str:
        """Get the current URL"""
        if not self.page:
            return ""
            
        try:
            return self.page.url
        except Exception as e:
            logger.error(f"Error getting current URL: {str(e)}")
            return ""
    
    async def scroll_to_bottom(self, scroll_pause_time: float = 1.0):
        """Scroll to the bottom of the page gradually"""
        if not self.page:
            return
            
        try:
            # Get initial scroll height
            last_height = await self.page.evaluate("document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                await asyncio.sleep(scroll_pause_time)
                
                # Calculate new scroll height
                new_height = await self.page.evaluate("document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {str(e)}")
    
    async def wait_for_selector(self, selector: str, timeout: int = None) -> bool:
        """Wait for a selector to appear"""
        if not self.page:
            return False
            
        try:
            timeout = timeout or self.timeout
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error waiting for selector {selector}: {str(e)}")
            return False
    
    async def click(self, selector: str) -> bool:
        """Click an element"""
        if not self.page:
            return False
            
        try:
            await self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Error clicking selector {selector}: {str(e)}")
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into an element"""
        if not self.page:
            return False
            
        try:
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            logger.error(f"Error typing text into {selector}: {str(e)}")
            return False
    
    async def get_element_text(self, selector: str) -> str:
        """Get text from an element"""
        if not self.page:
            return ""
            
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return ""
        except Exception as e:
            logger.error(f"Error getting text from {selector}: {str(e)}")
            return ""
    
    async def screenshot(self, path: str) -> bool:
        """Take a screenshot"""
        if not self.page:
            return False
            
        try:
            await self.page.screenshot(path=path)
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return False

# Create a singleton instance
playwright_browser = PlaywrightBrowser(headless=True) 