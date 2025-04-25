import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

from utils.text_utils import TextProcessor
from config import settings

logger = logging.getLogger(__name__)

class InformationSynthesizer:
    """
    Service to synthesize information from multiple sources
    """
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    async def synthesize(self, query: str, scraped_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize information from multiple sources to answer the query
        """
        if not scraped_results:
            return {
                "summary": "No information found for the query.",
                "key_points": [],
                "sources": []
            }
            
        try:
            logger.info(f"Synthesizing information from {len(scraped_results)} sources")
            
            # Extract relevant information from each source
            all_text = []
            sources = []
            
            for result in scraped_results:
                # Extract and clean content
                content = result.get("content", "")
                if not content:
                    continue
                    
                # Add to the combined text
                all_text.append(content)
                
                # Track the source
                sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                })
            
            if not all_text:
                return {
                    "summary": "No usable content found for the query.",
                    "key_points": [],
                    "sources": []
                }
                
            # Combine all text
            combined_text = " ".join(all_text)
            
            # Generate summary
            summary = self.text_processor.get_summary(combined_text, 10)
            
            # Extract key points
            key_points = await self.extract_key_points(combined_text, query)
            
            return {
                "summary": summary,
                "key_points": key_points,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing information: {str(e)}")
            return {
                "summary": "An error occurred while synthesizing information.",
                "key_points": [],
                "sources": []
            }
    
    async def extract_key_points(self, text: str, query: str) -> List[str]:
        """
        Extract key points from text
        """
        try:
            # Extract sentences
            from nltk.tokenize import sent_tokenize
            sentences = sent_tokenize(text)
            
            # Check if we have enough sentences
            if len(sentences) <= 5:
                return sentences
                
            # Extract keywords from query
            query_keywords = self.text_processor.extract_keywords(query, 5)
            
            # Extract keywords from text
            text_keywords = self.text_processor.extract_keywords(text, 15)
            
            # Combine keywords, prioritizing query keywords
            all_keywords = query_keywords + [kw for kw in text_keywords if kw not in query_keywords]
            
            # Score sentences based on keyword presence
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                sentence_lower = sentence.lower()
                
                # Initialize score
                sentence_scores[i] = 0
                
                # Score based on keywords
                for j, keyword in enumerate(all_keywords):
                    # Give higher weight to query keywords and earlier keywords
                    weight = 1.0
                    if j < len(query_keywords):
                        weight = 2.0  # Query keywords are more important
                    elif j < 5:
                        weight = 1.5  # More important text keywords
                        
                    if keyword.lower() in sentence_lower:
                        sentence_scores[i] += weight
                
                # Penalize very short sentences
                if len(sentence.split()) < 5:
                    sentence_scores[i] -= 2
                    
                # Boost scores for sentences that appear to be definitions or explanations
                if re.search(r"(?i)(is|are|refers to|defined as|means)", sentence_lower):
                    sentence_scores[i] += 1
                    
                # Boost scores for sentences with statistics or numbers
                if re.search(r"\d+(\.\d+)?%|(\d+)", sentence):
                    sentence_scores[i] += 1
            
            # Get top scored sentences (up to 10)
            top_indices = sorted(sentence_scores.keys(), key=lambda i: sentence_scores[i], reverse=True)[:10]
            
            # Sort indices to maintain original order
            top_indices.sort()
            
            # Get top sentences
            key_points = [sentences[i] for i in top_indices]
            
            # Deduplicate and clean
            seen = set()
            clean_points = []
            for point in key_points:
                # Skip very similar points
                is_duplicate = False
                for seen_point in seen:
                    if self.is_similar(point, seen_point):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    clean_points.append(point)
                    seen.add(point)
            
            return clean_points
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return []
    
    def is_similar(self, s1: str, s2: str, threshold: float = 0.7) -> bool:
        """
        Check if two strings are similar using Jaccard similarity
        """
        # Convert to lowercase and tokenize
        tokens1 = set(s1.lower().split())
        tokens2 = set(s2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        if union == 0:
            return False
            
        similarity = intersection / union
        
        return similarity > threshold
    
    async def find_contradictions(self, key_points: List[str]) -> List[Dict[str, Any]]:
        """
        Find potential contradictions between key points
        """
        contradictions = []
        
        # Simple contradiction finding - sentences with opposite meaning
        contradictory_pairs = [
            ('increase', 'decrease'),
            ('higher', 'lower'),
            ('more', 'less'),
            ('positive', 'negative'),
            ('agree', 'disagree'),
            ('true', 'false'),
            ('support', 'oppose'),
            ('good', 'bad')
        ]
        
        for i, point1 in enumerate(key_points):
            for j, point2 in enumerate(key_points):
                if i >= j:
                    continue
                    
                # Check for contradictions
                for word1, word2 in contradictory_pairs:
                    if word1 in point1.lower() and word2 in point2.lower():
                        contradictions.append({
                            "point1": point1,
                            "point2": point2,
                            "contradictory_terms": [word1, word2]
                        })
                        break
                        
                    if word2 in point1.lower() and word1 in point2.lower():
                        contradictions.append({
                            "point1": point1,
                            "point2": point2,
                            "contradictory_terms": [word2, word1]
                        })
                        break
        
        return contradictions 