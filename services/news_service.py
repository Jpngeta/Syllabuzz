import requests
import json
import os
import time
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from services.serpapi_service import get_news_results, SerpAPIError

load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPIService:
    def __init__(self, api_key=None, cache_duration=30):  # cache for 30 minutes by default
        """Initialize the News API service.
        
        Args:
            api_key: API key for the news service, defaults to environment variable
            cache_duration: How long to cache results in minutes
        """
        self.api_key = api_key or os.environ.get('NEWS_API_KEY')
        if not self.api_key:
            logger.warning("No News API key provided. API calls will fail.")
        
        self.base_url = "https://newsapi.org/v2"
        self.cache_file = "news_cache.json"
        self.cache_duration = cache_duration  # minutes
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cached API responses."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}
    
    def _save_cache(self):
        """Save API responses to cache."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _cache_key(self, endpoint, params):
        """Generate a cache key from the endpoint and params."""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"
    
    def _is_cache_valid(self, timestamp):
        """Check if the cache entry is still valid."""
        cache_time = datetime.fromtimestamp(timestamp)
        expiry_time = datetime.now() - timedelta(minutes=self.cache_duration)
        return cache_time > expiry_time
    
    def get(self, endpoint, params=None):
        """Make a GET request to the News API with caching."""
        if params is None:
            params = {}
        
        # Add API key to params
        params["apiKey"] = self.api_key
        
        # Check if we have a cached response
        cache_key = self._cache_key(endpoint, params)
        cached_data = self.cache.get(cache_key)
        
        if cached_data and self._is_cache_valid(cached_data["timestamp"]):
            logger.info(f"Using cached response for {endpoint}")
            return cached_data["data"]
        
        # Make the API request
        try:
            logger.info(f"Fetching fresh data from {endpoint}")
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            
            # Cache the successful response
            self.cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            self._save_cache()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            
            # If we have expired cache, use it as fallback
            if cached_data:
                logger.warning("Using expired cache as fallback")
                return cached_data["data"]
            
            # No cache available, raise the exception
            raise
    
    def get_top_headlines(self, category=None, country="us", page=1, page_size=20):
        """Get top headlines from the News API."""
        params = {
            "country": country,
            "page": page,
            "pageSize": page_size
        }
        
        if category and category != "all":
            params["category"] = category
        
        return self.get("top-headlines", params)
    
    def get_everything(self, query, language="en", sort_by="publishedAt", page=1, page_size=20):
        """Search for articles using the News API."""
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "page": page,
            "pageSize": page_size
        }
        
        return self.get("everything", params)
    
    def get_sources(self, category=None, language="en", country="us"):
        """Get available news sources from the News API."""
        params = {
            "language": language,
            "country": country
        }
        
        if category and category != "all":
            params["category"] = category
        
        return self.get("sources", params)


# Create a newsapi.org service (default)
class NewsAPIClientService(NewsAPIService):
    def format_articles(self, api_response):
        """Format articles from News API response to our app's format."""
        if not api_response or 'articles' not in api_response:
            return []
            
        articles = []
        for article in api_response['articles']:
            try:
                # Map NewsAPI fields to our app's fields
                formatted_article = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "image_url": article.get("urlToImage", ""),
                    "source_name": article.get("source", {}).get("name", "Unknown"),
                    "published_at": datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00")) if article.get("publishedAt") else datetime.now(),
                    "author": article.get("author", ""),
                    "categories": self._extract_categories(article)
                }
                articles.append(formatted_article)
            except Exception as e:
                logger.error(f"Error formatting article: {e}")
                continue
                
        return articles
    
    def _extract_categories(self, article):
        """Extract categories from article based on content."""
        # This is a simple implementation
        # In a real app, you might use NLP or the actual category from the API
        title = article.get("title", "").lower()
        keywords = {
            "technology": ["tech", "software", "app", "digital", "computer", "ai", "robot"],
            "business": ["business", "economy", "market", "stock", "finance", "company"],
            "science": ["science", "research", "study", "experiment", "discovery"],
            "health": ["health", "medical", "doctor", "hospital", "disease", "treatment"],
            "sports": ["sport", "game", "player", "team", "championship", "win", "match"],
            "entertainment": ["movie", "music", "celebrity", "actor", "film", "show", "star"]
        }
        
        categories = []
        for category, words in keywords.items():
            if any(word in title for word in words):
                categories.append(category)
        
        # Use source name as a fallback for categorization
        source = article.get("source", {}).get("name", "").lower()
        if "tech" in source or "digital" in source:
            categories.append("technology")
        elif "business" in source or "finance" in source:
            categories.append("business")
        elif "health" in source or "medical" in source:
            categories.append("health")
        elif "sport" in source:
            categories.append("sports")
        elif "science" in source:
            categories.append("science")
        elif "entertainment" in source:
            categories.append("entertainment")
        
        # Remove duplicates and ensure at least one category
        categories = list(set(categories))
        if not categories:
            categories = ["general"]
            
        return categories