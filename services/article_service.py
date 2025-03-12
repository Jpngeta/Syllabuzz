# Article fetching and processing
import logging
import requests
from datetime import datetime
from bson.objectid import ObjectId
from utils.db_utils import articles_collection
from config import NEWS_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleService:
    def __init__(self, news_api_key=NEWS_API_KEY):
        """Initialize the article service"""
        self.news_api_key = news_api_key
        logger.info("Initialized article service")

    def fetch_articles(self, category=None, count=20, page=1):
        """Fetch articles from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/top-headlines"
            
            # Prepare parameters
            params = {
                "apiKey": self.news_api_key,
                "pageSize": count,
                "page": page,
                "language": "en"
            }
            
            # Add category if specified
            if category:
                params["category"] = category
                
            # Make API request
            response = requests.get(url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return []
                
            # Parse response
            data = response.json()
            
            # Check if articles were returned
            if data.get("status") != "ok" or "articles" not in data:
                logger.error(f"Invalid response from NewsAPI: {data}")
                return []
                
            articles = data["articles"]
            logger.info(f"Fetched {len(articles)} articles from NewsAPI for category: {category}")
            return articles
        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            return []

    def fetch_and_store_articles(self, category=None, count=20):
        """Fetch articles from NewsAPI and store them in the database"""
        try:
            # Fetch articles
            articles = self.fetch_articles(category, count)
            
            # Store each article
            stored_count = 0
            for article in articles:
                # Store article
                result = self.store_article(article, category)
                if result:
                    stored_count += 1
                    
            logger.info(f"Stored {stored_count} articles for category: {category}")
            return stored_count
        except Exception as e:
            logger.error(f"Error fetching and storing articles: {str(e)}")
            return 0

    def store_article(self, article, category=None):
        """Store an article in the database"""
        try:
            # Extract source information
            source = article.get("source", {})
            source_name = source.get("name", "Unknown") if isinstance(source, dict) else str(source)
            
            # Extract published date
            published_at = article.get("publishedAt")
            if published_at:
                try:
                    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                except:
                    try:
                        published_at = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
                    except:
                        published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()
                
            # Prepare article document
            article_doc = {
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "url": article.get("url"),
                "image_url": article.get("urlToImage"),
                "source_name": source_name,
                "published_at": published_at,
                "updated_at": datetime.utcnow(),
                "vector_embedding": None  # Will be populated by embedding service
            }
            
            # Add category if provided
            if category:
                article_doc["categories"] = [category]
                
            # Check if article already exists (by URL)
            existing = articles_collection.find_one({"url": article_doc["url"]})
            
            if existing:
                # Update existing article
                articles_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": article_doc}
                )
                return existing["_id"]
            else:
                # Insert new article
                result = articles_collection.insert_one(article_doc)
                return result.inserted_id
        except Exception as e:
            logger.error(f"Error storing article: {str(e)}")
            return None

    def get_articles(self, category=None, limit=20, skip=0):
        """Get articles from database, optionally filtered by category"""
        try:
            # Build query
            query = {}
            if category:
                query["categories"] = category
                
            # Get articles
            articles = list(articles_collection.find(query)
                          .sort("published_at", -1)
                          .skip(skip)
                          .limit(limit))
                          
            # Convert ObjectId to string for JSON serialization
            for article in articles:
                article["_id"] = str(article["_id"])
                
            logger.info(f"Retrieved {len(articles)} articles from database for category: {category}")
            return articles
        except Exception as e:
            logger.error(f"Error getting articles: {str(e)}")
            return []

    def get_article_by_id(self, article_id):
        """Get a single article by ID"""
        try:
            # Ensure article_id is ObjectId
            if isinstance(article_id, str):
                article_id = ObjectId(article_id)
                
            # Get article
            article = articles_collection.find_one({"_id": article_id})
            
            if article:
                # Convert ObjectId to string
                article["_id"] = str(article["_id"])
                return article
                
            logger.error(f"Article not found: {article_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting article by ID: {str(e)}")
            return None

    def search_articles(self, query, limit=20, skip=0):
        """Search articles by text query"""
        try:
            # Build search query
            search_query = {
                "$text": {"$search": query}
            }
            
            # Perform search
            articles = list(articles_collection.find(search_query)
                           .sort("published_at", -1)
                           .skip(skip)
                           .limit(limit))
                           
            # Convert ObjectId to string
            for article in articles:
                article["_id"] = str(article["_id"])
                
            logger.info(f"Found {len(articles)} articles matching query: {query}")
            return articles
        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return []