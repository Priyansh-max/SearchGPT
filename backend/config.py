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
    
    # Selenium settings
    SELENIUM_HEADLESS: bool = os.getenv("SELENIUM_HEADLESS", "True").lower() in ["true", "1", "t"]
    SELENIUM_TIMEOUT: int = int(os.getenv("SELENIUM_TIMEOUT", "30"))
    
    # User agent to be used in requests/Selenium
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    
    # News API settings
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    NEWS_API_URL: str = "https://newsapi.org/v2/everything"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # In production, replace with specific origins
    
    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() in ["true", "1", "t"]
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour

# Create settings instance
settings = Settings() 