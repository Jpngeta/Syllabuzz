import os
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache
from dotenv import load_dotenv
from services.news_service import NewsAPIClientService
# Load environment variables
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv('NEWS_API_KEY')
BASE_URL = "https://newsapi.org/v2"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration (TTL in seconds)
article_cache = TTLCache(maxsize=100, ttl=3600)  # Store for 1 hour instead of 15 minutes

# Rate limiting configuration
last_request_time = datetime.now()
daily_request_count = 0
MAX_DAILY_REQUESTS = 100  # Adjust based on your NewsAPI plan
MIN_REQUEST_INTERVAL = 1.0  # Seconds between requests

def get_top_headlines(category=None, page=1, page_size=20, country='us'):
    """Get top headlines with rate limiting"""
    global last_request_time, daily_request_count
    
    # Create cache key
    cache_key = f"headlines_{country}_{category}_{page}_{page_size}"
    
    # Check if in cache
    if cache_key in article_cache:
        logger.info(f"Returning cached data for {cache_key}")
        return article_cache[cache_key]
    
    # Apply rate limiting
    current_time = datetime.now()
    time_since_last_request = (current_time - last_request_time).total_seconds()
    
    # Ensure minimum time between requests
    if time_since_last_request < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last_request
        logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    # Check if we've hit our daily limit
    if daily_request_count >= MAX_DAILY_REQUESTS:
        logger.warning(f"Daily request limit reached ({MAX_DAILY_REQUESTS}). Using expired cache")
        # Find any cached result for this category
        for key in article_cache.keys():
            if category and key.startswith(f"headlines_{country}_{category}_"):
                logger.info(f"Using similar cached result: {key}")
                return article_cache[key]
        
        # If no cache for this category, return empty result
        return {
            "status": "error",
            "message": "Daily request limit reached",
            "articles": [],
            "totalResults": 0
        }
    
    # Make the request
    logger.info("Fetching fresh data from top-headlines")
    
    params = {
        'country': country,
        'page': page,
        'pageSize': page_size
    }
    
    if category and category != 'all':
        params['category'] = category
        
    try:
        # Update rate limiting trackers before making the request
        last_request_time = datetime.now()
        daily_request_count += 1
        
        response = requests.get(f"{BASE_URL}/top-headlines", params=params, headers={'X-Api-Key': API_KEY})
        
        if response.status_code == 429:
            # We're rate limited - use cache as fallback
            logger.error(f"API request failed: {response.status_code} Rate limit exceeded")
            # Find any cached result for this category
            for key in article_cache.keys():
                if category and key.startswith(f"headlines_{country}_{category}_"):
                    logger.warning("Using expired cache as fallback")
                    return article_cache[key]
            
            # If no cache available, return empty result
            return {
                "status": "error",
                "message": "Rate limit exceeded",
                "articles": [],
                "totalResults": 0
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Cache the result
        article_cache[cache_key] = data
        
        return data
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        
        # Try to find similar cached results
        for key in article_cache.keys():
            if category and key.startswith(f"headlines_{country}_{category}_"):
                logger.warning("Using expired cache as fallback")
                return article_cache[key]
        
        # If no cache, return empty response
        return {
            "status": "error",
            "message": str(e),
            "articles": [],
            "totalResults": 0
        }

def search_articles(query, language='en', sort_by='publishedAt', page=1, page_size=20):
    """Search articles with rate limiting"""
    global last_request_time, daily_request_count
    
    # Create cache key
    cache_key = f"search_{query}_{language}_{sort_by}_{page}_{page_size}"
    
    # Check if in cache
    if cache_key in article_cache:
        logger.info(f"Returning cached data for {cache_key}")
        return article_cache[cache_key]
    
    # Apply rate limiting
    current_time = datetime.now()
    time_since_last_request = (current_time - last_request_time).total_seconds()
    
    # Ensure minimum time between requests
    if time_since_last_request < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last_request
        logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    # Check if we've hit our daily limit
    if daily_request_count >= MAX_DAILY_REQUESTS:
        logger.warning(f"Daily request limit reached ({MAX_DAILY_REQUESTS}). Using expired cache")
        # Try to find a similar search result
        for key in article_cache.keys():
            if key.startswith("search_"):
                logger.info(f"Using similar cached result: {key}")
                return article_cache[key]
        
        # If no cache, return empty result
        return {
            "status": "error",
            "message": "Daily request limit reached",
            "articles": [],
            "totalResults": 0
        }
    
    # Make the request
    logger.info(f"Fetching fresh data for search query: {query}")
    
    params = {
        'q': query,
        'language': language,
        'sortBy': sort_by,
        'page': page,
        'pageSize': page_size
    }
    
    try:
        # Update rate limiting trackers
        last_request_time = datetime.now()
        daily_request_count += 1
        
        response = requests.get(f"{BASE_URL}/everything", params=params, headers={'X-Api-Key': API_KEY})
        
        if response.status_code == 429:
            # We're rate limited - use cache as fallback
            logger.error(f"API request failed: {response.status_code} Rate limit exceeded")
            # Try to find a similar search result
            for key in article_cache.keys():
                if key.startswith("search_"):
                    logger.warning("Using expired cache as fallback")
                    return article_cache[key]
            
            # If no cache available, return empty result
            return {
                "status": "error",
                "message": "Rate limit exceeded",
                "articles": [],
                "totalResults": 0
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Cache the result
        article_cache[cache_key] = data
        
        return data
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        
        # Try to find a similar search result
        for key in article_cache.keys():
            if key.startswith("search_"):
                logger.warning("Using expired cache as fallback")
                return article_cache[key]
        
        # If no cache, return empty response
        return {
            "status": "error",
            "message": str(e),
            "articles": [],
            "totalResults": 0
        }

# Method to reset daily count (call this at midnight)
def reset_daily_count():
    global daily_request_count
    daily_request_count = 0

# Method to clear cache
def clear_cache():
    article_cache.clear()