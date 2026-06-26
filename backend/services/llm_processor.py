import logging
import os
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

from config import settings
from services.llm_provider import build_provider_chain, generate_with_fallback

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMProcessor:
    """
    Service to handle LLM operations for query refinement and results synthesis
    """
    
    def __init__(self):
        """Store config only — no network/keys touched here. The Gemini model and the
        provider fallback chain are built lazily on first use so this module imports
        cleanly without a GEMINI_API_KEY (needed for offline tests and self-host setup)."""
        self.model = None
        self.model_name = None
        self._provider_chain = None
        self._embedder = None
        self._safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        # max_output_tokens raised 2048 -> settings.MAX_OUTPUT_TOKENS (8192) per Problem 2.
        self._generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": settings.MAX_OUTPUT_TOKENS,
        }

    def _ensure_model(self):
        """Lazily configure Gemini and build the model on first use. NEEDS KEYS at runtime."""
        if self.model is not None:
            return self.model

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models()
                     if 'generateContent' in m.supported_generation_methods]

        if 'models/gemini-2.0-flash' in available:
            self.model_name = 'models/gemini-2.0-flash'
        elif 'models/gemini-1.5-flash' in available:
            self.model_name = 'models/gemini-1.5-flash'
        elif 'models/gemini-1.0-pro' in available:
            self.model_name = 'models/gemini-1.0-pro'
        else:
            self.model_name = available[0] if available else None

        if not self.model_name:
            raise ValueError("No suitable Gemini models available")

        logger.info(f"Using LLM model: {self.model_name}")
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self._safety_settings,
            generation_config=self._generation_config,
        )
        return self.model

    def _ensure_providers(self):
        """Build the Gemini -> OpenAI fallback chain on first use (OpenAI only if a key is set)."""
        if self._provider_chain is None:
            self._provider_chain = build_provider_chain(
                gemini_model=self._ensure_model(),
                openai_model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY or None,
            )
        return self._provider_chain

    def _get_embedder(self):
        """Lazily build the embedder (falls back to the zero-dep hashing embedder)."""
        if self._embedder is None:
            from services.retrieval import get_embedder
            self._embedder = get_embedder(
                settings.EMBEDDING_MODE,
                openai_api_key=settings.OPENAI_API_KEY or None,
            )
        return self._embedder

    def _build_context(self, query: str, scraped_results: List[Dict[str, Any]]) -> str:
        """
        Select the most query-relevant passages across sources (RAG, Problem 2) instead of
        blindly truncating each source. Caps sources at MAX_SOURCES, retrieves passages within
        a token budget that fits the smallest model in the fallback chain.
        """
        from services.retrieval import retrieve_relevant_passages

        sources = (scraped_results or [])[: settings.MAX_SOURCES]
        passages = retrieve_relevant_passages(
            query,
            sources,
            self._get_embedder(),
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
            token_budget=settings.RETRIEVAL_TOKEN_BUDGET,
        )
        parts = []
        for i, p in enumerate(passages):
            label = p.source_title or p.source_url or f"Source {i + 1}"
            parts.append(f"Source {i + 1} — {label} ({p.source_url}):\n{p.text}")
        return "\n\n".join(parts)
    
    async def refine_search_query(self, original_query: str) -> str:
        """
        Use LLM to refine the original search query to be more search-friendly
        """
        if not original_query:
            return ""
            
        try:
            prompt = f"""
            Your task is to convert this user query into an optimal Google search query.
            Make it concise, use relevant keywords, and optimize for search engine understanding.
            Do not use special search operators unless absolutely necessary.
            
            Original query: "{original_query}"
            
            Return only the refined search query without any explanations or additional text.
            """
            
            response = await self._generate_content(prompt)
            
            # Clean up the response - ensure no quotes or prefix text
            refined_query = response.strip('\'"').strip()
            
            if not refined_query:
                logger.warning(f"LLM returned empty refined query for: {original_query}")
                return original_query
                
            logger.info(f"Query refined: '{original_query}' -> '{refined_query}'")
            return refined_query
            
        except Exception as e:
            logger.error(f"Error refining search query: {str(e)}")
            return original_query
    
    async def process_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Use LLM to process search results into a well-formatted response with references
        """
        if not search_results:
            return "No search results found to process."
            
        try:
            # Prepare search results for the LLM prompt
            results_text = ""
            for i, result in enumerate(search_results):
                results_text += f"Result {i+1}:\n"
                results_text += f"Title: {result.get('title', 'No title')}\n"
                results_text += f"URL: {result.get('url', 'No URL')}\n"
                results_text += f"Snippet: {result.get('snippet', 'No snippet available')}\n\n"
            
            prompt = f"""
            You are an expert web searcher who helps users find information online and across the web.
            
            User query: "{query}"
            
            Here are the search results I found for you on the web:
            
            {results_text}
            
            Please provide a the search results that you found on the web 
            Your response should:
            1. Mainly focused on providing as many web searched reference links as possible
            2. Directly answer the user's question
            3. Provide relevant context and information
            4. Cite sources for key information (use the format [1], [2], etc.)
            5. Include a "References" section at the end with numbered links
            
            Format your response in Markdown for readability.
            """
            
            response = await self._generate_content(prompt)
            
            if not response:
                logger.warning("LLM returned empty response when processing search results")
                # Fallback to a basic formatted response
                return self._format_basic_results(query, search_results)
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing search results: {str(e)}")
            # Fallback to basic formatting
            return self._format_basic_results(query, search_results)
    
    async def process_scraped_content(self, query: str, scraped_results: List[Dict[str, Any]]) -> str:
        """
        Use LLM to process scraped website content into a comprehensive response
        """
        if not scraped_results:
            return "No content was found to process."
            
        try:
            # RAG: select the most query-relevant passages across sources instead of
            # truncating each source to a fixed character budget (Problem 2).
            contents_text = self._build_context(query, scraped_results)

            prompt = f"""
            You are an expert web scrapper agent who helps users find information online and across the web.
            
            User query: "{query}"
            
            Here is the content I scraped from relevant websites:
            
            {contents_text}
            
            Please synthesize this information into a comprehensive response to the user's query.
            Your response should:
            1. Directly output the content in a way how a scrapper would output the content
            2. output what is asked by the user exactly as it is
            3. End with a "References" section at the end with numbered links to the scrapped content
            4. Do not add any additional text or explanations

            Format your response in Markdown for readability.
            """
            
            response = await self._generate_content(prompt)
            
            if not response:
                logger.warning("LLM returned empty response when processing scraped content")
                # Fallback to a basic formatted response
                return self._format_basic_scraped_content(query, scraped_results)
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing scraped content: {str(e)}")
            # Fallback to basic formatting
            return self._format_basic_scraped_content(query, scraped_results)
    
    async def synthesize_information(self, query: str, scraped_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use LLM to synthesize information from multiple sources (enhanced version of information_synthesizer)
        """
        if not scraped_results:
            return {
                "summary": "No information found for the query.",
                "key_points": [],
                "sources": []
            }
            
        try:
            # Extract sources for reference
            sources = []
            for result in scraped_results:
                sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                })
            
            # RAG: relevant-passage selection instead of fixed truncation (Problem 2).
            contents_text = self._build_context(query, scraped_results)

            prompt = f"""
            You are an expert content analyser who helps synthesize data from multiple sources combine them and create a comprehensive analysis.
            
            User query: "{query}"
            
            Here is content from relevant websites:
            
            {contents_text}
            
            Based on these sources, please provide:
            1. A concise summary (2-3 paragraphs) answering the query
            2. A list of 5-7 key points extracted from the sources
            
            Format your response as a JSON object with the following structure EXACTLY:
            {{
                "summary": "The concise summary text here",
                "key_points": ["Key point 1", "Key point 2", ...]
            }}
            
            Only return the JSON object, nothing else. Make sure your JSON is valid with proper quotes and formatting.
            """

            response = await self._generate_content(prompt, json_mode=True)

            try:
                # Parse JSON response
                # Clean the response to handle common formatting issues
                clean_response = response.strip()
                # Remove markdown code blocks if present
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                result = json.loads(clean_response)
                
                # Ensure required fields exist
                if "summary" not in result and "Analysis" in result:
                    result["summary"] = result["Analysis"]
                elif "summary" not in result:
                    result["summary"] = "Analysis could not be generated properly."
                
                if "key_points" not in result:
                    result["key_points"] = []
                    
                result["sources"] = sources
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"LLM did not return valid JSON: {e}, using fallback extraction")
                # Try to extract information using regex if JSON parsing fails
                import re
                
                # Extract summary - check both "summary" and "Analysis" fields
                summary_match = re.search(r'"summary":\s*"(.*?)"', response, re.DOTALL)
                if not summary_match:
                    summary_match = re.search(r'"Analysis":\s*"(.*?)"', response, re.DOTALL)
                    
                summary = summary_match.group(1) if summary_match else "Summary could not be extracted from the analysis."
                
                # Extract key points array
                key_points_match = re.search(r'"key_points":\s*\[(.*?)\]', response, re.DOTALL)
                if key_points_match:
                    points_text = key_points_match.group(1)
                    # Extract quoted strings within the array
                    key_points = re.findall(r'"(.*?)"', points_text)
                else:
                    # Try to extract bullet points if JSON parsing failed
                    bullet_points = re.findall(r'- (.*?)(?:\n|$)', response)
                    key_points = bullet_points if bullet_points else []
                
                return {
                    "summary": summary,
                    "key_points": key_points,
                    "sources": sources
                }
                
        except Exception as e:
            logger.error(f"Error synthesizing information: {str(e)}")
            # Create a basic summary from the content if possible
            try:
                combined_content = ""
                for result in scraped_results[:2]:  # Use first 2 sources for fallback
                    content = result.get('content', '')
                    if content:
                        combined_content += content[:300] + " "  # Take first 300 chars of each
                
                fallback_summary = combined_content[:500] + "..." if combined_content else "An error occurred while synthesizing information."
                
                return {
                    "summary": fallback_summary,
                    "key_points": ["Information could not be fully analyzed due to a processing error."],
                    "sources": sources if 'sources' in locals() else []
                }
            except:
                return {
                    "summary": "An error occurred while synthesizing information.",
                    "key_points": [],
                    "sources": sources if 'sources' in locals() else []
                }
    
    async def process_news(self, query: str, news_results: List[Dict[str, Any]]) -> str:
        """
        Use LLM to process news results into a well-formatted response with references
        """
        if not news_results:
            return "No news articles found to process."
            
        try:
            # Prepare news results for the LLM prompt
            news_text = ""
            for i, article in enumerate(news_results):
                news_text += f"Article {i+1}:\n"
                news_text += f"Title: {article.get('title', 'No title')}\n"
                news_text += f"Source: {article.get('source', 'Unknown source')}\n"
                news_text += f"Published: {article.get('published_date', 'Unknown date')}\n"
                news_text += f"URL: {article.get('url', 'No URL')}\n"
                news_text += f"Snippet: {article.get('snippet', 'No snippet available')}\n\n"
            
            prompt = f"""
            You are an expert news reporter who helps users reports news related to the user query.
            
            User query about news: "{query}"
            
            Here are the news articles I found as per your request:
            
            {news_text}
            
            Please provide a comprehensive overview of the news related to this query.
            Your response should:
            1. Summarize the key developments and trends
            2. Highlight important details from multiple sources
            3. Provide context and background if relevant
            4. Cite sources for key information (use the format [1], [2], etc.)
            5. Include a "References" section at the end with numbered links to articles
            6. For each reference, format it as: [Title] - [Source] ([Date]) with a "Read more" link to the URL
            
            Example reference format:
            1. Article Title - News Source (Publication Date) [Read more](URL)
            
            Format your response in Markdown for readability.
            """
            
            response = await self._generate_content(prompt)
            
            if not response:
                logger.warning("LLM returned empty response when processing news")
                # Fallback to a basic formatted response
                return self._format_basic_news(query, news_results)
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing news results: {str(e)}")
            # Fallback to basic formatting
            return self._format_basic_news(query, news_results)
    
    async def _generate_content(self, prompt: str, *, json_mode: bool = False) -> str:
        """
        Generate content through the provider fallback chain (Gemini async -> OpenAI).
        Fixes the old blocking synchronous call and adds rate-limit fallback.
        """
        try:
            providers = self._ensure_providers()
            result = await generate_with_fallback(prompt, providers, json_mode=json_mode)
            logger.info(f"LLM answered via: {result.provider}")
            return result.text
        except Exception as e:
            logger.error(f"Error generating content from LLM: {str(e)}")
            raise
    
    def _format_basic_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Fallback formatter for search results if LLM processing fails
        """
        formatted = f"Here are the search results for \"{query}\":\n\n"
        
        for i, result in enumerate(results):
            formatted += f"{i + 1}. **{result.get('title', 'No title')}**\n"
            formatted += f"   {result.get('snippet', 'No description available')}\n"
            formatted += f"   [Link]({result.get('url', '')})\n\n"
            
        return formatted
    
    def _format_basic_scraped_content(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Fallback formatter for scraped content if LLM processing fails
        """
        formatted = f"Here's the content I scraped for \"{query}\":\n\n"
        
        for i, result in enumerate(results):
            formatted += f"{i + 1}. **{result.get('title', 'No title')}**\n"
            formatted += f"   Source: {result.get('url', '')}\n\n"
            
            content = result.get('content', 'No content available')
            if len(content) > 500:
                content = content[:500] + "..."
                
            formatted += f"   {content}\n\n"
            
        return formatted
    
    def _format_basic_news(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Fallback formatter for news results if LLM processing fails
        """
        formatted = f"Here are the latest news articles for \"{query}\":\n\n"
        
        for i, article in enumerate(results):
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown source')
            date = article.get('published_date', 'Unknown date')
            url = article.get('url', '')
            
            formatted += f"{i + 1}. **{title}** - *{source}* ({date}) [Read more]({url})\n\n"
            formatted += f"   {article.get('snippet', 'No snippet available')}\n\n"
            
        return formatted

# Create a singleton instance
llm_processor = LLMProcessor() 