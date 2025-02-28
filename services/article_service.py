import os
import logging
import requests
import time
import json
from datetime import datetime, timedelta
from cachetools import TTLCache
from bson.objectid import ObjectId
from db import db
from services import news_api
from services.serpapi_service import get_news_results
from dotenv import load_dotenv
# Add this import for NewsAPIClientService
from services.news_service import NewsAPIClientService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # This line was missing

# Load environment variables
load_dotenv()

# Initialize the news API service
news_service = NewsAPIClientService(api_key=os.environ.get('NEWS_API_KEY'))

# Collection references
articles_collection = db.articles
bookmarks_collection = db.bookmarks

# Cache for articles
article_cache = TTLCache(maxsize=100, ttl=900)  # 15 minutes cache

def get_articles(category=None, page=1, page_size=12):
    """
    Get articles from the database or API, and ensure proper ID handling
    """
    try:
        # Get articles from NewsAPI
        logger.info(f"Fetching articles for category: {category}, page: {page}")
        
        if category and category != 'all':
            articles_data = news_service.get_top_headlines(category=category, page=page, page_size=page_size)
        else:
            articles_data = news_service.get_top_headlines(page=page, page_size=page_size)
        
        # Process and store articles to ensure they have proper IDs
        processed_articles = []
        for article in articles_data.get('articles', []):
            # Store the article in the database to ensure it has an ID
            stored_article = store_article(article, categories=[category] if category and category != 'all' else None)
            if stored_article:
                # Make sure ID is properly converted to string
                stored_article['_id'] = str(stored_article['_id'])
                processed_articles.append(stored_article)
        
        # Return processed articles with guaranteed IDs
        return {
            'articles': processed_articles,
            'total_results': articles_data.get('totalResults', len(processed_articles))
        }
    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        
        # Try to get articles from the database instead
        try:
            logger.info("Falling back to database articles")
            query = {}
            if category and category != 'all':
                query['categories'] = category
                
            # Calculate skip and limit for pagination
            skip = (page - 1) * page_size
            
            # Get articles from database
            articles = list(articles_collection.find(query)
                           .sort('published_at', -1)
                           .skip(skip)
                           .limit(page_size))
                           
            # Convert ObjectId to string
            for article in articles:
                article['_id'] = str(article['_id'])
                
                # Ensure published_at is properly formatted
                if 'published_at' in article and not isinstance(article['published_at'], str):
                    try:
                        article['published_at'] = article['published_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                    except:
                        article['published_at'] = str(article['published_at'])
            
            # Get total count for pagination
            total_results = articles_collection.count_documents(query)
            
            return {
                'articles': articles,
                'total_results': total_results
            }
            
        except Exception as db_error:
            logger.error(f"Database fallback error: {str(db_error)}")
            # Return empty result on error
            return {'articles': [], 'total_results': 0}

def fetch_articles_by_category(category, page=1, page_size=12):
    """
    Fetch articles from API by category
    
    Args:
        category (str): Article category
        page (int): Page number
        page_size (int): Number of articles per page
        
    Returns:
        dict: Articles data with pagination info
    """
    try:
        # Try NewsAPI first
        try:
            data = news_api.get_top_headlines(
                category=category,
                page=page,
                page_size=page_size
            )
            
            # Store articles in database
            for article in data.get('articles', []):
                store_article(article, [category])
                
            return data
            
        except Exception as news_api_error:
            logger.error(f"NewsAPI error: {str(news_api_error)}")
            
            # Fall back to SerpAPI
            logger.info(f"Falling back to SerpAPI for category: {category}")
            serp_data = get_news_results(category=category, page=page)
            
            # Process and store articles
            processed_articles = []
            for article in serp_data.get('articles', []):
                processed = store_article(article, [category])
                processed_articles.append(processed)
                
            return {
                'articles': processed_articles,
                'total_results': serp_data.get('total_results', 0)
            }
            
    except Exception as e:
        logger.error(f"Error fetching articles for category {category}: {str(e)}")
        return {
            'articles': [],
            'total_results': 0
        }

def search_articles(query, page=1, page_size=12):
    """
    Search for articles by query
    
    Args:
        query (str): Search query
        page (int): Page number
        page_size (int): Number of articles per page
        
    Returns:
        dict: Search results with pagination info
    """
    try:
        logger.info(f"Searching articles for query: {query}")
        
        # First try searching via NewsAPI
        try:
            articles_data = news_service.search_everything(query=query, page=page, page_size=page_size)
            
            # Process and store articles
            processed_articles = []
            for article in articles_data.get('articles', []):
                stored_article = store_article(article)
                if stored_article:
                    stored_article['_id'] = str(stored_article['_id'])
                    processed_articles.append(stored_article)
            
            return {
                'articles': processed_articles,
                'total_results': articles_data.get('totalResults', len(processed_articles))
            }
        except Exception as api_error:
            logger.error(f"NewsAPI search error: {str(api_error)}")
            
            # Fall back to database search
            logger.info("Falling back to database search")
            
            # Build search query - search in title, description and content
            search_query = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Calculate skip and limit for pagination
            skip = (page - 1) * page_size
            
            # Get articles from database
            articles = list(articles_collection.find(search_query)
                          .sort('published_at', -1)
                          .skip(skip)
                          .limit(page_size))
                          
            # Convert ObjectId to string
            for article in articles:
                article['_id'] = str(article['_id'])
                
                # Ensure published_at is properly formatted
                if 'published_at' in article and not isinstance(article['published_at'], str):
                    try:
                        article['published_at'] = article['published_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                    except:
                        article['published_at'] = str(article['published_at'])
            
            # Get total count for pagination
            total_results = articles_collection.count_documents(search_query)
            
            return {
                'articles': articles,
                'total_results': total_results
            }
            
    except Exception as e:
        logger.error(f"Error searching articles for query {query}: {str(e)}")
        return {
            'articles': [],
            'total_results': 0
        }

def get_article_by_id(article_id):
    """
    Get an article by its ID
    
    Args:
        article_id: String or ObjectId of the article
        
    Returns:
        dict: Article data or None if not found
    """
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(article_id, str):
            try:
                article_id = ObjectId(article_id)
            except:
                logger.error(f"Invalid article ID format: {article_id}")
                return None
        
        # Try to find the article by ID
        article = articles_collection.find_one({"_id": article_id})
        
        if article:
            # Convert ObjectId to string for JSON serialization
            article["_id"] = str(article["_id"])
            # Ensure published_at is serializable
            if 'published_at' in article and not isinstance(article['published_at'], str):
                try:
                    article['published_at'] = article['published_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                except:
                    article['published_at'] = str(article['published_at'])
            
            return article
        
        logger.error(f"Article not found for ID: {article_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting article by ID: {str(e)}")
        return None

def fetch_and_store_articles(category=None, count=20, page=1):
    """
    Fetch articles from NewsAPI and store them in the database
    
    Args:
        category (str): Category to fetch articles for
        count (int): Number of articles to fetch
        page (int): Page number
        
    Returns:
        dict: Result of operation
    """
    try:
        logger.info(f"Fetching and storing articles for category: {category}")
        
        # Fetch articles using our existing function
        articles_data = news_service.get_top_headlines(category=category, page=page, page_size=count)
        
        # Get the articles from the response
        articles = articles_data.get('articles', [])
        
        if not articles:
            logger.warning(f"No articles found for category: {category}")
            return {
                'success': False,
                'message': f"No articles found for category: {category}"
            }
        
        # Store each article
        stored_count = 0
        for article in articles:
            # Add category to article
            if not article.get('categories'):
                article['categories'] = [category] if category else ['general']
            
            # Store or update the article
            processed_article = store_article(article)
            if processed_article:
                stored_count += 1
        
        return {
            'success': True,
            'message': f"Successfully stored {stored_count} articles for category: {category}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching and storing articles: {str(e)}")
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def store_article(article, categories=None):
    """Store or update an article in the database"""
    try:
        # Extract fields or set defaults
        source = article.get('source', {})
        
        # Handle different source formats
        if isinstance(source, dict):
            source_name = source.get('name', 'Unknown')
            source_id = source.get('id')
        else:
            source_name = str(source) if source else 'Unknown'
            source_id = None
        
        # Make sure we have an image URL
        image_url = article.get('urlToImage') or article.get('image_url')
        
        # Get or sanitize the publish date
        published_at = article.get('publishedAt')
        if not published_at:
            published_at = datetime.utcnow()
        elif isinstance(published_at, str):
            try:
                published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            except:
                try:
                    published_at = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
                except:
                    published_at = datetime.utcnow()
        
        processed_article = {
            "title": article.get('title'),
            "description": article.get('description'),
            "content": article.get('content'),
            "url": article.get('url'),
            "image_url": image_url,
            "source_name": source_name,
            "source_id": source_id,
            "published_at": published_at,
            "updated_at": datetime.utcnow()
        }
        
        # Add categories if provided
        if categories:
            processed_article["categories"] = categories
        elif "categories" in article:
            processed_article["categories"] = article["categories"]
        
        # Check if article already exists by URL
        existing = articles_collection.find_one({"url": processed_article["url"]})
        
        if existing:
            # Update existing article
            articles_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": processed_article}
            )
            processed_article["_id"] = existing["_id"]
        else:
            # Insert new article
            result = articles_collection.insert_one(processed_article)
            processed_article["_id"] = result.inserted_id
        
        return processed_article
        
    except Exception as e:
        logger.error(f"Error storing article: {str(e)}")
        return None

def get_bookmarked_articles(user_id):
    """
    Get all articles bookmarked by a user
    
    Args:
        user_id (str): User ID
        
    Returns:
        list: Bookmarked articles
    """
    try:
        bookmarks = list(bookmarks_collection.find({"user_id": user_id}))
        article_ids = [bookmark["article_id"] for bookmark in bookmarks]
        
        # Get the full articles
        bookmarked_articles = []
        for article_id in article_ids:
            article = get_article_by_id(article_id)
            if article:
                # Add bookmark metadata
                bookmark = next((b for b in bookmarks if str(b["article_id"]) == str(article_id)), None)
                if bookmark and "notes" in bookmark:
                    article["notes"] = bookmark["notes"]
                bookmarked_articles.append(article)
        
        return bookmarked_articles
        
    except Exception as e:
        logger.error(f"Error fetching bookmarks for user {user_id}: {str(e)}")
        return []

def get_cached_articles_by_category(category, fallback_count=5):
    """Get cached articles by category as fallback when API fails"""
    try:
        # Try to get from database
        query = {"categories": category} if category != "all" else {}
        articles = list(articles_collection.find(query).sort("published_at", -1).limit(fallback_count))
        
        if articles and len(articles) > 0:
            logger.info(f"Found {len(articles)} cached articles for category {category} in database")
            return {
                "articles": articles,
                "total_results": len(articles),
                "status": "ok"
            }
        
        # If no articles in database, create sample ones
        logger.info(f"No cached articles found for {category}, generating samples")
        return generate_sample_articles(category)
    except Exception as e:
        logger.error(f"Error getting fallback articles: {str(e)}")
        return generate_sample_articles(category)

def generate_sample_articles(category):
    """Generate sample articles when no cache or API is available"""
    samples = []
    category_titles = {
        "business": ["Market Update", "Business Trends", "Economic Outlook"],
        "technology": ["Tech Innovations", "Digital Transformation", "New Gadget Review"],
        "entertainment": ["Celebrity News", "Movie Reviews", "Music Festival Highlights"],
        "health": ["Health Tips", "Medical Breakthrough", "Wellness Guide"],
        "science": ["Scientific Discovery", "Space Exploration", "Research Update"],
        "sports": ["Game Highlights", "Sports Analysis", "Athlete Profile"]
    }
    
    titles = category_titles.get(category, ["Latest News", "Breaking Story", "Featured Article"])
    
    for i in range(5):
        sample = {
            "_id": ObjectId(),
            "title": f"{titles[i % len(titles)]} #{i+1}",
            "description": f"Sample article description for {category} category.",
            "content": "This is a placeholder article when API data is not available.",
            "url": "#",
            "image_url": None,
            "source_name": "Syllabuzz",
            "categories": [category],
            "published_at": datetime.utcnow() - timedelta(days=i)
        }
        samples.append(sample)
    
    return {
        "articles": samples,
        "total_results": len(samples),
        "status": "ok"
    }