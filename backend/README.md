# SearchGPT Agent Backend

This is the backend API for the SearchGPT web research agent, which provides various tools for web search, content extraction, analysis, and news aggregation.

## Features

- **Query Analysis**: Understands and optimizes user queries for effective searching
- **Web Search**: Performs Google searches and returns structured results
- **Web Scraping**: Extracts content from web pages using Newspaper3k and Selenium
- **Content Analysis**: Synthesizes information from multiple sources
- **News Aggregation**: Searches for news articles from multiple sources

## Setup

### Prerequisites

- Python 3.8+
- Chrome or Chromium browser (for Selenium)
- ChromeDriver (automatically installed by webdriver-manager)

### Installation

1. Clone the repository and navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Download NLTK data (this will happen automatically on first run, but you can do it manually):

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

5. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

6. Edit the `.env` file to set your configuration values, including an optional News API key.

## Running the Server

Start the FastAPI server:

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

The API provides the following endpoints:

- `POST /api/search`: Perform a web search and return links and snippets
- `POST /api/scrape`: Extract content from multiple web pages based on a query
- `POST /api/analyze`: Analyze content from multiple sources and provide a synthesis
- `POST /api/news`: Search for news articles related to the query
- `POST /api/query`: Analyze a query and provide insights about it

## Using with the Frontend

The backend is designed to work with the SearchE Agent frontend. Make sure to set the correct CORS settings in the `config.py` file if you're running the frontend on a different host or port.

## Notes on Web Scraping

The web scraping features respect robots.txt and include reasonable rate limits to avoid overloading websites. Please use responsibly and in accordance with websites' terms of service.

## License

[MIT License](../LICENSE) 