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

    # ---------------- Wrap-up additions (Problems 1-6) ----------------

    # LLM fallback (Problem 3) — OpenAI is optional; unset = Gemini-only
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_PRIMARY: str = os.getenv("LLM_PRIMARY", "gemini")
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))

    # Retrieval / RAG (Problem 2)
    MAX_SOURCES: int = int(os.getenv("MAX_SOURCES", "10"))
    EMBEDDING_MODE: str = os.getenv("EMBEDDING_MODE", "local")  # local | openai | hashing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    RETRIEVAL_TOKEN_BUDGET: int = int(os.getenv("RETRIEVAL_TOKEN_BUDGET", "90000"))

    # Concurrency lanes + memory guard (Problem 1)
    SIGNEDIN_SLOTS: int = int(os.getenv("SIGNEDIN_SLOTS", "2"))
    DEMO_SLOTS: int = int(os.getenv("DEMO_SLOTS", "1"))
    MEMORY_GUARD_MB: int = int(os.getenv("MEMORY_GUARD_MB", "120"))
    BLOCK_RESOURCES: bool = os.getenv("BLOCK_RESOURCES", "True").lower() in ["true", "1", "t"]

    # Auth / hosted add-ons (toggles — OFF-friendly defaults keep self-host simple)
    AUTH_MODE: str = os.getenv("AUTH_MODE", "static")  # supabase | static | off
    API_KEY: str = os.getenv("API_KEY", "")  # static self-host key (AUTH_MODE=static)
    QUOTA_ENABLED: bool = os.getenv("QUOTA_ENABLED", "False").lower() in ["true", "1", "t"]
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "False").lower() in ["true", "1", "t"]

    # Supabase (hosted only — analytics, multi-user keys)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Admin dashboard (Problem 5) — gate enforced server-side
    ADMIN_USER: str = os.getenv("ADMIN_USER", "")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")  # bcrypt hash, never plaintext
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")

# Create settings instance
settings = Settings() 