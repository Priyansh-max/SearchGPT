import re
import logging
import html2text
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter

logger = logging.getLogger(__name__)

# Download necessary NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {str(e)}")

class TextProcessor:
    """Utility class for text processing"""
    
    @staticmethod
    def html_to_text(html_content: str) -> str:
        """Convert HTML content to plain text"""
        try:
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            converter.ignore_images = True
            converter.ignore_tables = False
            converter.ignore_emphasis = True
            converter.body_width = 0  # No wrapping
            
            text = converter.handle(html_content)
            
            # Clean up some markdown artifacts
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove extra newlines
            text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1 (\2)', text)  # Convert links
            
            return text
        except Exception as e:
            logger.error(f"Error converting HTML to text: {str(e)}")
            return html_content  # Return original content in case of error
    
    @staticmethod
    def extract_main_content(text: str) -> str:
        """
        Attempt to extract the main content of a webpage by removing
        navigation, headers, footers, etc.
        """
        # Simple heuristic - Find the longest paragraph
        paragraphs = re.split(r'\n\s*\n', text)
        if not paragraphs:
            return text
            
        # Filter out very short paragraphs
        valid_paragraphs = [p for p in paragraphs if len(p.strip()) > 100]
        if not valid_paragraphs:
            return text
            
        # Find paragraph with highest content density (length / markup ratio)
        content_paragraph = max(valid_paragraphs, key=len)
        
        # If the chosen paragraph is too small, return the original text
        if len(content_paragraph) < 200:
            return text
            
        return content_paragraph
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
        """Extract key terms from text"""
        try:
            # Clean the text
            clean_text = TextProcessor.clean_text(text)
            
            # Tokenize
            words = word_tokenize(clean_text)
            
            # Remove stopwords
            stop_words = set(stopwords.words('english'))
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Lemmatize
            lemmatizer = WordNetLemmatizer()
            lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
            
            # Count word frequency
            word_counts = Counter(lemmatized_words)
            
            # Return the most common words
            return [word for word, _ in word_counts.most_common(num_keywords)]
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    @staticmethod
    def get_summary(text: str, num_sentences: int = 5) -> str:
        """Generate a simple extractive summary"""
        try:
            # Split into sentences
            sentences = sent_tokenize(text)
            
            if len(sentences) <= num_sentences:
                return text
                
            # Clean sentences
            clean_sentences = [sentence.strip() for sentence in sentences]
            clean_text = ' '.join(clean_sentences)
            
            # Extract keywords
            keywords = TextProcessor.extract_keywords(clean_text, 20)
            
            # Score sentences based on keyword presence
            sentence_scores = {}
            for i, sentence in enumerate(clean_sentences):
                sentence_scores[i] = 0
                sentence_lower = sentence.lower()
                
                # Boost score for first few sentences
                if i < 3:
                    sentence_scores[i] += 3 - i
                    
                # Score based on keywords
                for keyword in keywords:
                    if keyword.lower() in sentence_lower:
                        sentence_scores[i] += 1
                        
                # Length penalty for very short or very long sentences
                length = len(sentence.split())
                if length < 5:
                    sentence_scores[i] -= 2
                elif length > 40:
                    sentence_scores[i] -= 1
            
            # Get top sentences
            top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
            top_sentence_indices.sort()  # Preserve original order
            
            # Combine the top sentences
            summary = ' '.join([sentences[i] for i in top_sentence_indices])
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return text[:500] + "..."  # Fallback to truncation
    
    @staticmethod
    def get_readability_score(text: str) -> float:
        """Get a simple readability score (higher is more complex)"""
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text)
            
            if not sentences or not words:
                return 0
                
            avg_sentence_length = len(words) / len(sentences)
            
            # Simple readability measure
            return min(10, avg_sentence_length / 2)  # Scale to 0-10
        except Exception as e:
            logger.error(f"Error calculating readability: {str(e)}")
            return 5  # Default middle value

# Create a singleton instance
text_processor = TextProcessor() 