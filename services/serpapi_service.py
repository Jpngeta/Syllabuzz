import os
import requests
import json
from datetime import datetime, timedelta
import logging
from cachetools import TTLCache
from dotenv import load_dotenv
from urllib.parse import urlencode
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv('SERPAPI_KEY')
BASE_URL = "https://serpapi.com/search"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration (TTL in seconds)
# Store up to 50 responses for 20 minutes
news_cache = TTLCache(maxsize=50, ttl=1200)

class SerpAPIError(Exception):
    """Custom exception for SerpAPI errors"""
    pass

def get_news_results(query=None, location="United States", time_period=None, page=1, category=None):
    """
    Fetch news results from SerpAPI
    
    Args:
        query (str, optional): Search query for specific news
        location (str): Location context for news (default: United States)
        time_period (str, optional): Time period filter (e.g., 'h' for hour, 'd' for day)
        page (int): Page number for pagination
        category (str, optional): News category (business, health, sci/tech, etc.)
        
    Returns:
        dict: Processed news results
    """
    # Convert our app's category to Google News categories
    google_category = None
    if category and category != "all":
        category_mapping = {
            "business": "business", 
            "entertainment": "entertainment",
            "technology": "sci/tech",
            "science": "sci/tech",
            "health": "health",
            "sports": "sports",
            "general": None
        }
        google_category = category_mapping.get(category.lower())

    # Create a unique cache key
    cache_params = {
        "q": query or "top news",
        "loc": location,
        "time": time_period or "",
        "page": page,
        "cat": google_category or ""
    }
    cache_key = urlencode(cache_params)
    
    # Check cache first
    if cache_key in news_cache:
        logger.info(f"Returning cached results for: {cache_key}")
        return news_cache[cache_key]
    
    try:
        # Build SerpAPI parameters
        params = {
            "engine": "google",
            "tbm": "nws",  # News search
            "api_key": API_KEY,
            "gl": "us",    # Country (US)
            "start": (page - 1) * 10  # SerpAPI pagination
        }
        
        # Add optional parameters
        if query:
            params["q"] = query
        else:
            params["q"] = "latest news"
            
        if google_category:
            params["q"] += f" {google_category}"
            
        if location:
            params["location"] = location
            
        if time_period:
            params["tbs"] = f"qdr:{time_period}"  # e.g., 'qdr:d' for past day
        
        logger.info(f"Making SerpAPI request with params: {params}")
        
        # Make API request
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        if "error" in data:
            raise SerpAPIError(f"SerpAPI error: {data['error']}")
        
        # Process news results into our standard format
        processed_results = process_news_results(data)
        
        # Cache the processed results
        news_cache[cache_key] = processed_results
        
        return processed_results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"SerpAPI request failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise SerpAPIError(f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing SerpAPI results: {str(e)}")
        logger.error(traceback.format_exc())
        raise SerpAPIError(f"Error: {str(e)}")

def process_news_results(serpapi_data):
    """
    Process SerpAPI news search results into our application's format
    
    Args:
        serpapi_data (dict): Raw SerpAPI response
        
    Returns:
        dict: Processed news data with standardized format
    """
    try:
        results = {
            "status": "ok",
            "total_results": 0,
            "articles": []
        }
        
        # Check if news results exist
        news_results = serpapi_data.get("news_results", [])
        if not news_results:
            logger.warning("No news results found in SerpAPI response")
            return results
        
        results["total_results"] = len(news_results)
        
        # Process each news item
        for item in news_results:
            # Extract data
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            source = item.get("source", "")
            published_date = item.get("date", "")
            thumbnail = item.get("thumbnail", "")
            
            # Extract category from source or link
            categories = extract_categories(title, link, source)
            
            # Parse date into datetime
            try:
                if published_date:
                    # Handle various date formats from SerpAPI
                    if 'ago' in published_date:
                        # Convert relative time to absolute
                        published_at = parse_relative_time(published_date)
                    else:
                        # Try common date formats
                        date_formats = [
                            '%b %d, %Y',  # 'May 10, 2023'
                            '%d %b %Y',   # '10 May 2023'
                            '%Y-%m-%d',   # '2023-05-10'
                        ]
                        published_at = None
                        for fmt in date_formats:
                            try:
                                published_at = datetime.strptime(published_date, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if not published_at:
                            # If parsing fails, use current time
                            published_at = datetime.now()
                else:
                    published_at = datetime.now()
            except Exception:
                # Default to current time if date parsing fails
                published_at = datetime.now()
            
            # Create article object in our standard format
            article = {
                "title": title,
                "description": snippet,
                "content": snippet,  # We'll need to fetch full content separately
                "url": link,
                "image_url": thumbnail,
                "source_name": source,
                "author": source,
                "published_at": published_at,
                "categories": categories
            }
            
            results["articles"].append(article)
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing news results: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e), "articles": []}

def extract_categories(title, link, source):
    """Extract likely categories based on title, link and source"""
    title_lower = title.lower()
    source_lower = source.lower()
    link_lower = link.lower()
    
    categories = []
    
    # Keywords for categories
    category_keywords = {
        "technology": ["tech", "software", "app", "digital", "computer", "ai", "robot", "smartphone", "gadget"],
        "business": ["business", "economy", "market", "stock", "finance", "company", "startup", "investment"],
        "science": ["science", "research", "study", "experiment", "discovery", "space", "physics", "chemistry"],
        "health": ["health", "medical", "doctor", "hospital", "disease", "treatment", "medicine", "covid", "vaccine"],
        "sports": ["sport", "game", "player", "team", "championship", "win", "match", "tournament", "league"],
        "entertainment": ["movie", "music", "celebrity", "actor", "film", "show", "star", "tv", "hollywood"],
        "politics": ["politic", "government", "president", "election", "vote", "democrat", "republican", "congress"]
    }
    
    # Check title and source against keywords
    for category, keywords in category_keywords.items():
        if any(keyword in title_lower for keyword in keywords):
            categories.append(category)
            continue
            
        if any(keyword in source_lower for keyword in keywords):
            categories.append(category)
            continue
            
        # Check URL parts that might indicate category
        if any(keyword in link_lower for keyword in keywords):
            categories.append(category)
            continue
    
    # Check for specific news sources that focus on certain categories
    tech_sources = ["techcrunch", "wired", "the verge", "engadget", "cnet"]
    business_sources = ["bloomberg", "forbes", "wsj", "financial times", "business insider"]
    
    if any(source in source_lower for source in tech_sources):
        categories.append("technology")
    
    if any(source in source_lower for source in business_sources):
        categories.append("business")
    
    # Add "general" category if no specific category was determined
    if not categories:
        categories.append("general")
    
    # Remove duplicates and return
    return list(set(categories))

def parse_relative_time(time_str):
    """Convert relative time strings like '3 hours ago' to datetime"""
    now = datetime.now()
    time_str = time_str.lower()
    
    try:
        if "min" in time_str:
            minutes = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(minutes=minutes)
        elif "hour" in time_str:
            hours = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(hours=hours)
        elif "day" in time_str:
            days = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(days=days)
        elif "week" in time_str:
            weeks = int(''.join(filter(str.isdigit, time_str)))
            return now - timedelta(weeks=weeks)
        elif "month" in time_str:
            months = int(''.join(filter(str.isdigit, time_str)))
            # Approximation: a month is about 30 days
            return now - timedelta(days=30*months)
        else:
            return now
    except:
        return now

def fetch_article_content(url):
    """
    Fetch full article content from URL using newspaper3k
    
    Args:
        url (str): Article URL
        
    Returns:
        str: Full article content if available, otherwise empty string
    """
    try:
        from newspaper import Article
        
        # Download and parse article
        article = Article(url)
        article.download()
        article.parse()
        
        return article.text
    except Exception as e:
        logger.error(f"Error fetching article content: {str(e)}")
        return ""

def clear_cache():
    """Clear all caches"""
    news_cache.clear()