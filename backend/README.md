# SearchGPT Agent Backend

This is the backend API for the SearchGPT web research agent, which provides various tools for web search, content extraction, analysis, and news aggregation using modern APIs and browser automation.

## Features

- **Query Analysis**: Understands and optimizes user queries for effective searching
- **Web Search**: High-speed searches using SerpAPI (Google, Bing)
- **Web Scraping**: Fast content extraction using Playwright browser automation
- **Content Analysis**: AI-powered synthesis using Google Gemini
- **News Aggregation**: Multi-source news search and aggregation
- **LLM Integration**: Advanced query processing and content synthesis

## Architecture

### New High-Performance Stack
- **Search Engine**: SerpAPI for reliable, fast search results
- **Browser Automation**: Playwright for efficient content extraction
- **AI Processing**: Google Gemini for intelligent content synthesis
- **Performance**: 5-10x faster than previous Selenium-based approach

## Setup

### Prerequisites

- Python 3.9+ (recommended: Python 3.10)
- SerpAPI account and API key
- Google Gemini API key
- Node.js (for Playwright browser installation)

### Installation

1. **Clone the repository and navigate to the backend directory:**

```bash
cd backend
```

2. **Create a virtual environment and activate it:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers:**

```bash
playwright install chromium
playwright install-deps chromium
```

5. **Download NLTK data:**

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

### Environment Configuration

Create a `.env` file in the backend directory with the following configuration:

```bash
# Required API Keys
SERPAPI_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Search Engine Settings
SERPAPI_ENGINE=google
SERPAPI_TIMEOUT=10
SEARCH_RESULTS_LIMIT=10
MAX_PAGES_TO_SCRAPE=5

# Optional: Playwright Settings
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_TIMEOUT=30000
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_VIEWPORT_WIDTH=1920
PLAYWRIGHT_VIEWPORT_HEIGHT=1080

# Optional: Performance Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=0.5
MIN_CONTENT_LENGTH=500
MAX_CONTENT_LENGTH=50000

# Optional: Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Optional: Retry Settings
MAX_RETRIES=3
RETRY_DELAY=1.0

# Optional: News API (for news aggregation)
NEWS_API_KEY=your_news_api_key_here

# Optional: Application Settings
DEBUG=False
LOG_LEVEL=INFO
CACHE_ENABLED=True
CACHE_TTL=3600
```

### Getting API Keys

#### 1. SerpAPI Key (Required)
1. Visit [SerpAPI](https://serpapi.com/)
2. Create a free account
3. Get your API key from the dashboard
4. Free tier includes 100 searches/month

#### 2. Google Gemini API Key (Required)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

#### 3. News API Key (Optional)
1. Visit [NewsAPI](https://newsapi.org/)
2. Create a free account for news aggregation features

## Running the Server

### Development Mode

```bash
python app.py
```

### Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

### Using Gunicorn (Recommended for Production)

```bash
gunicorn app:app --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker --timeout 300 --workers 1
```

## API Endpoints

The API provides the following endpoints:

### Core Search & Extraction
- `POST /api/search`: Fast web search using SerpAPI
- `POST /api/scrape`: Extract content from web pages using Playwright
- `POST /api/analyze`: AI-powered content analysis and synthesis

### Specialized Tools
- `POST /api/news`: News article search and aggregation
- `POST /api/query`: Query analysis and optimization

### Request Format

All endpoints accept JSON requests with this structure:

```json
{
    "query": "your search query here",
    "tool": "search|scrape|analyze|news",
    "use_llm": true
}
```

### Example Usage

```bash
curl -X POST "http://localhost:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "latest AI developments", "use_llm": true}'
```

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t searchgpt-backend .

# Run the container
docker run -p 8000:8000 \
  -e SERPAPI_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  searchgpt-backend
```

### Using Docker Compose

```bash
docker-compose up --build
```

## Performance Optimization

### Concurrent Processing
- Supports concurrent URL scraping
- Configurable request limits and delays
- Built-in rate limiting and retry logic

### Caching
- Response caching for improved performance
- Configurable TTL settings
- Memory-efficient content processing

### Browser Management
- Persistent browser contexts
- Optimized Playwright configuration
- Minimal resource usage

## Troubleshooting

### Common Issues

1. **SerpAPI Key Issues**
   ```bash
   # Test your SerpAPI key
   curl "https://serpapi.com/search.json?q=test&api_key=YOUR_KEY"
   ```

2. **Playwright Browser Issues**
   ```bash
   # Reinstall browsers
   playwright install chromium --force
   ```

3. **Memory Issues**
   ```bash
   # Reduce concurrent requests
   export MAX_CONCURRENT_REQUESTS=2
   export MAX_PAGES_TO_SCRAPE=3
   ```

### Debugging

Enable debug mode for detailed logging:

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
```

## Migration from Selenium

If upgrading from the previous Selenium-based version:

1. Remove old Chrome/ChromeDriver dependencies
2. Install Playwright as shown above
3. Update environment variables (remove SELENIUM_* settings)
4. Test with new API endpoints

## Performance Benchmarks

### Before (Selenium)
- Search: 3-5 seconds
- Scraping: 2-4 seconds per page
- Memory: 200-500MB per browser instance

### After (SerpAPI + Playwright)
- Search: 0.5-1 second
- Scraping: 1-2 seconds per page
- Memory: 50-100MB total

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[MIT License](../LICENSE) 