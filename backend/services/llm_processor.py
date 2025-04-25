import logging
import os
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMProcessor:
    """
    Service to handle LLM operations for query refinement and results synthesis
    """
    
    def __init__(self):
        """Initialize the LLM processor with API key from environment variables"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY is required")
                
            # Configure the Gemini API
            genai.configure(api_key=api_key)
            
            # Get available models
            self.available_models = [m.name for m in genai.list_models() 
                                    if 'generateContent' in m.supported_generation_methods]
            
            # Select the appropriate model (preferring Gemini Flash if available)
            if 'models/gemini-2.0-flash' in self.available_models:
                self.model_name = 'models/gemini-2.0-flash'
            elif 'models/gemini-1.5-flash' in self.available_models:
                self.model_name = 'models/gemini-1.5-flash'
            elif 'models/gemini-1.0-pro' in self.available_models:
                self.model_name = 'models/gemini-1.0-pro'
            else:
                self.model_name = self.available_models[0] if self.available_models else None
                
            if not self.model_name:
                raise ValueError("No suitable Gemini models available")
                
            logger.info(f"Using LLM model: {self.model_name}")
            
            # Configure model with safe settings
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info("LLM processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM processor: {str(e)}")
            raise
    
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
            # Prepare content for the LLM prompt
            # Limit content length to avoid exceeding context window
            contents_text = ""
            for i, result in enumerate(scraped_results[:5]):  # Limit to first 5 results
                contents_text += f"Source {i+1}:\n"
                contents_text += f"Title: {result.get('title', 'No title')}\n"
                contents_text += f"URL: {result.get('url', 'No URL')}\n"
                
                # Truncate content to reasonable length
                content = result.get('content', 'No content available')
                if len(content) > 1500:
                    content = content[:1500] + "...(truncated)"
                    
                contents_text += f"Content: {content}\n\n"
            
            prompt = f"""
            You are an expert web scrapper agent who helps users find information online and across the web.
            
            User query: "{query}"
            
            Here is the content I scraped from relevant websites:
            
            {contents_text}
            
            Please synthesize this information into a comprehensive response to the user's query.
            Your response should:
            1. Directly output the scrapped content in a well-formatted manner
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
            
            # Prepare content for the LLM prompt
            contents_text = ""
            for i, result in enumerate(scraped_results[:5]):  # Limit to first 5 results
                contents_text += f"Source {i+1}:\n"
                contents_text += f"Title: {result.get('title', 'No title')}\n"
                contents_text += f"URL: {result.get('url', 'No URL')}\n"
                
                # Truncate content to reasonable length
                content = result.get('content', 'No content available')
                if len(content) > 1200:
                    content = content[:1200] + "...(truncated)"
                    
                contents_text += f"Content: {content}\n\n"
            
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
            
            response = await self._generate_content(prompt)
            
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
    
    async def _generate_content(self, prompt: str) -> str:
        """
        Helper method to generate content using the Gemini API
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
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
            date = article.get('published_date', 'Unknown date')
            formatted += f"{i + 1}. **{article.get('title', 'No title')}**\n"
            formatted += f"   *{article.get('source', 'Unknown source')}* | {date}\n"
            formatted += f"   {article.get('snippet', 'No snippet available')}\n"
            formatted += f"   [Read more]({article.get('url', '')})\n\n"
            
        return formatted

# Create a singleton instance
llm_processor = LLMProcessor() 