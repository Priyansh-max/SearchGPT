# : SearchGPT

SearchGPT is a powerful web research agent that helps users find, extract, analyze, and synthesize information from the web. It combines web search, content extraction, and information analysis capabilities in a user-friendly interface.

## Features

- **Web Search Tool**: Search the web and retrieve relevant results
- **Web Scraper**: Extract data from websites for further analysis
- **Content Analyzer**: Analyze content from multiple sources to provide comprehensive answers
- **News Aggregator**: Find the latest news articles on any topic

## Project Structure

The project consists of two main parts:

- **Frontend**: React-based user interface
- **Backend**: Python/FastAPI backend with web search and content analysis capabilities

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (or copy from `.env.example`):
```bash
cp .env.example .env
```

5. Edit the `.env` file to configure settings as needed

6. Start the backend server:
```bash
python app.py
```
or
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Usage

1. Open the application in your browser (typically at `http://localhost:5173` for frontend)
2. Select a tool from the available options
3. Enter your search query
4. View the results in the chat interface

## Technical Details

### Frontend

- Built with React and Vite
- Styled with Tailwind CSS
- Features a responsive chat interface

### Backend

- Built with FastAPI
- Uses Selenium for web browsing and content extraction
- Integrates NLTK and other NLP tools for content analysis
- Uses Geminie LLM to process queries and construct responses in a structured manner
- Provides a RESTful API for the frontend

## Notes on Web Scraping

The web scraping features respect robots.txt and include reasonable rate limits to avoid overloading websites. Please use responsibly and in accordance with websites' terms of service.

## License

This project is licensed under the MIT License. 