import re
import logging
from typing import Dict, List, Any
import nltk
from nltk.tokenize import word_tokenize
from utils.text_utils import TextProcessor

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """
    Service to analyze and understand user queries
    """
    
    def __init__(self):
        self.text_processor = TextProcessor()
        
        # Common query patterns for different query types
        self.patterns = {
            "factual": [
                r"what is", r"who is", r"where is", r"when was", r"how many", 
                r"define", r"meaning of", r"explain"
            ],
            "exploratory": [
                r"how to", r"how do", r"ways to", r"methods for", r"steps", 
                r"guide", r"tutorial", r"learn"
            ],
            "news": [
                r"latest", r"recent", r"news", r"update", r"current", r"today",
                r"this week", r"this month", r"developments"
            ],
            "comparison": [
                r"compare", r"difference between", r"vs", r"versus", r"better",
                r"pros and cons", r"advantages", r"disadvantages"
            ],
            "opinion": [
                r"best", r"worst", r"should I", r"recommend", r"review",
                r"opinion", r"thoughts on", r"top \d+"
            ]
        }
    
    def analyze(self, query: str) -> str:
        """
        Analyze the query and return an optimized version for search
        """
        if not query:
            return ""
            
        # Remove unnecessary fillers and improve search efficiency
        optimized_query = query.strip()
        
        # Remove generic phrases that don't add search value
        filler_phrases = [
            "please tell me", "i want to know", "can you tell me",
            "i'm looking for", "i'd like to know", "inform me about",
            "give me information about", "i need information on"
        ]
        
        for phrase in filler_phrases:
            optimized_query = re.sub(r"(?i)" + re.escape(phrase), "", optimized_query)
        
        # Simplify questions to keyword format for better search results
        optimized_query = re.sub(r"(?i)^(what is|who is|where is|when is|how to|why is|can you) ", "", optimized_query)
        
        # Clean up and return
        optimized_query = re.sub(r"\s+", " ", optimized_query).strip()
        
        logger.info(f"Query optimized: '{query}' -> '{optimized_query}'")
        return optimized_query
    
    def get_query_type(self, query: str) -> str:
        """
        Determine the type of query (factual, exploratory, news, etc.)
        """
        query_lower = query.lower()
        
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(r"(?i)" + pattern, query_lower):
                    return query_type
        
        # Default to factual if no pattern matches
        return "factual"
    
    def extract_entities(self, query: str) -> List[str]:
        """
        Extract key entities (nouns) from the query
        """
        try:
            # Tokenize
            words = word_tokenize(query)
            
            # POS tagging (requires nltk.download('averaged_perceptron_tagger'))
            try:
                nltk.download('averaged_perceptron_tagger', quiet=True)
                pos_tags = nltk.pos_tag(words)
                
                # Extract nouns (NN, NNS, NNP, NNPS)
                nouns = [word for word, pos in pos_tags if pos.startswith('NN')]
                return nouns
            except Exception:
                # Fallback to simple word extraction if POS tagging fails
                return [w for w in words if len(w) > 3]
                
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def get_detailed_analysis(self, query: str) -> Dict[str, Any]:
        """
        Provide a detailed analysis of the query
        """
        if not query:
            return {
                "query_type": "unknown",
                "entities": [],
                "suggested_search_terms": [],
                "complexity": 0
            }
        
        # Analyze the query
        query_type = self.get_query_type(query)
        entities = self.extract_entities(query)
        
        # Extract keywords
        keywords = self.text_processor.extract_keywords(query, 5)
        
        # Generate suggested search terms
        suggested_terms = []
        suggested_terms.append(self.analyze(query))  # Optimized query
        
        # Add entity-based searches
        for entity in entities:
            if len(entity) > 3 and entity not in suggested_terms:
                suggested_terms.append(entity)
        
        # Calculate query complexity based on length and structure
        words = query.split()
        complexity = min(10, len(words) / 3)  # Scale from 0-10
        
        return {
            "query_type": query_type,
            "entities": entities,
            "keywords": keywords,
            "suggested_search_terms": suggested_terms[:3],  # Top 3 suggestions
            "complexity": complexity
        } 