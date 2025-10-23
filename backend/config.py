import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    # App settings
    APP_NAME: str = "SearchGPT Agent"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]
    
    # API settings
    API_PREFIX: str = "/api"
    
    # Web search settings
    SEARCH_RESULTS_LIMIT: int = int(os.getenv("SEARCH_RESULTS_LIMIT", "10"))
    MAX_PAGES_TO_SCRAPE: int = int(os.getenv("MAX_PAGES_TO_SCRAPE", "10"))
    
    # SerpAPI settings
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    SERPAPI_ENGINE: str = os.getenv("SERPAPI_ENGINE", "google")  # google, bing, etc.
    SERPAPI_TIMEOUT: int = int(os.getenv("SERPAPI_TIMEOUT", "10"))
    
    # Playwright settings
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "True").lower() in ["true", "1", "t"]
    PLAYWRIGHT_TIMEOUT: int = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))  # milliseconds
    PLAYWRIGHT_BROWSER: str = os.getenv("PLAYWRIGHT_BROWSER", "chromium")  # chromium, firefox, webkit
    PLAYWRIGHT_VIEWPORT_WIDTH: int = int(os.getenv("PLAYWRIGHT_VIEWPORT_WIDTH", "1920"))
    PLAYWRIGHT_VIEWPORT_HEIGHT: int = int(os.getenv("PLAYWRIGHT_VIEWPORT_HEIGHT", "1080"))
    
    # User agent to be used in requests/Playwright
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    
    # LLM settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # News API settings
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    NEWS_API_URL: str = "https://newsapi.org/v2/everything"
    
    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "0.5"))  # seconds between requests
    
    # Content extraction settings
    MIN_CONTENT_LENGTH: int = int(os.getenv("MIN_CONTENT_LENGTH", "500"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # In production, replace with specific origins
    
    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() in ["true", "1", "t"]
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() in ["true", "1", "t"]
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # seconds
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds

# Create settings instance
settings = Settings() 