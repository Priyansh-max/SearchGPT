from fastapi import APIRouter, HTTPException, Depends, Body, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

# Import services
from services.query_analyzer import QueryAnalyzer
from services.web_searcher import web_searcher
from services.content_extractor import content_extractor
from services.information_synthesizer import InformationSynthesizer
from services.news_searcher import NewsSearcher
from services.llm_processor import llm_processor

# Create router
router = APIRouter()
logger = logging.getLogger(__name__)

# Define request/response models
class QueryRequest(BaseModel):
    query: str
    tool: Optional[str] = None
    use_llm: Optional[bool] = True  # Default to using LLM

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    position: int

class WebSearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    tool: str
    llm_response: Optional[str] = None
    refined_query: Optional[str] = None

class ScraperResult(BaseModel):
    url: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class WebScraperResponse(BaseModel):
    results: List[ScraperResult]
    query: str
    tool: str
    llm_response: Optional[str] = None
    refined_query: Optional[str] = None

class AnalysisResult(BaseModel):
    summary: str
    key_points: List[str]
    sources: List[Dict[str, str]]

class ContentAnalyzerResponse(BaseModel):
    result: AnalysisResult
    query: str
    tool: str
    refined_query: Optional[str] = None

class NewsItem(BaseModel):
    title: str
    source: str
    url: str
    published_date: str
    snippet: str

class NewsResponse(BaseModel):
    results: List[NewsItem]
    query: str
    tool: str
    llm_response: Optional[str] = None
    refined_query: Optional[str] = None

# Initialize service instances
query_analyzer = QueryAnalyzer()
information_synthesizer = InformationSynthesizer()
news_searcher = NewsSearcher()

@router.post("/search", response_model=WebSearchResponse)
async def search(query_data: QueryRequest):
    """
    Perform a web search based on the user query using SerpAPI
    """
    logger.info(f"Web search request received: {query_data.query}")
    
    try:
        # Default to traditional query analyzer
        refined_query = query_analyzer.analyze(query_data.query)
        
        # Use LLM to refine the search query if enabled
        if query_data.use_llm:
            llm_refined_query = await llm_processor.refine_search_query(query_data.query)
            if llm_refined_query and llm_refined_query != query_data.query:
                refined_query = llm_refined_query
                logger.info(f"Using LLM refined query: {refined_query}")
        
        # Perform web search using SerpAPI
        search_results = await web_searcher.search(refined_query)
        
        # Process results with LLM if enabled
        formatted_response = None
        if query_data.use_llm:
            formatted_response = await llm_processor.process_search_results(query_data.query, search_results)
        
        return WebSearchResponse(
            results=search_results,
            query=query_data.query,
            tool="search",
            llm_response=formatted_response,
            refined_query=refined_query
        )
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")

@router.post("/scrape", response_model=WebScraperResponse)
async def scrape(query_data: QueryRequest):
    """
    Scrape content from web pages using Playwright based on search results
    """
    logger.info(f"Web scraper request received: {query_data.query}")
    
    try:
        # Default to traditional query analyzer
        refined_query = query_analyzer.analyze(query_data.query)
        
        # Use LLM to refine the search query if enabled
        if query_data.use_llm:
            llm_refined_query = await llm_processor.refine_search_query(query_data.query)
            if llm_refined_query and llm_refined_query != query_data.query:
                refined_query = llm_refined_query
                logger.info(f"Using LLM refined query: {refined_query}")
            
        # First search for relevant pages using SerpAPI
        search_results = await web_searcher.search(refined_query)
        
        # Extract content from search results using Playwright
        scraped_results = await content_extractor.extract_from_search_results(search_results)
        
        # Process scraped content with LLM if enabled
        formatted_response = None
        if query_data.use_llm:
            formatted_response = await llm_processor.process_scraped_content(query_data.query, scraped_results)
        
        return WebScraperResponse(
            results=scraped_results,
            query=query_data.query,
            tool="scraper",
            llm_response=formatted_response,
            refined_query=refined_query
        )
    except Exception as e:
        logger.error(f"Error in web scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Web scraping failed: {str(e)}")

@router.post("/analyze", response_model=ContentAnalyzerResponse)
async def analyze(query_data: QueryRequest):
    """
    Analyze content from multiple web sources using SerpAPI + Playwright
    """
    logger.info(f"Content analyzer request received: {query_data.query}")
    
    try:
        # Default to traditional query analyzer
        refined_query = query_analyzer.analyze(query_data.query)
        
        # Use LLM to refine the search query if enabled
        if query_data.use_llm:
            llm_refined_query = await llm_processor.refine_search_query(query_data.query)
            if llm_refined_query and llm_refined_query != query_data.query:
                refined_query = llm_refined_query
                logger.info(f"Using LLM refined query: {refined_query}")
            
        # Search for relevant content using SerpAPI
        search_results = await web_searcher.search(refined_query)
        
        # Extract content using Playwright
        scraped_results = await content_extractor.extract_from_search_results(search_results)
        
        # Synthesize information
        if query_data.use_llm:
            # Use LLM for synthesis
            analysis_result = await llm_processor.synthesize_information(query_data.query, scraped_results)
        else:
            # Use traditional synthesizer
            analysis_result = await information_synthesizer.synthesize(query_data.query, scraped_results)
        
        return ContentAnalyzerResponse(
            result=analysis_result,
            query=query_data.query,
            tool="analyzer",
            refined_query=refined_query
        )
    except Exception as e:
        logger.error(f"Error in content analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.post("/news", response_model=NewsResponse)
async def search_news(query_data: QueryRequest):
    """
    Search for news articles related to the query
    """
    logger.info(f"News search request received: {query_data.query}")
    
    try:
        # Default to traditional query analyzer
        refined_query = query_analyzer.analyze(query_data.query)
        
        # Use LLM to refine the search query if enabled
        if query_data.use_llm:
            llm_refined_query = await llm_processor.refine_search_query(query_data.query)
            if llm_refined_query and llm_refined_query != query_data.query:
                refined_query = llm_refined_query
                logger.info(f"Using LLM refined query: {refined_query}")
            
        # Search for news
        news_results = await news_searcher.search(refined_query)
        
        # Process news with LLM if enabled
        formatted_response = None
        if query_data.use_llm:
            formatted_response = await llm_processor.process_news(query_data.query, news_results)
        
        return NewsResponse(
            results=news_results,
            query=query_data.query,
            tool="news",
            llm_response=formatted_response,
            refined_query=refined_query
        )
    except Exception as e:
        logger.error(f"Error in news search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")

@router.post("/query", response_model=Dict[str, Any])
async def analyze_query(query_data: QueryRequest):
    """
    Analyze a query and provide insights about it
    """
    logger.info(f"Query analysis request received: {query_data.query}")
    
    try:
        analysis = query_analyzer.get_detailed_analysis(query_data.query)
        return {
            "query": query_data.query,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error in query analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}") 