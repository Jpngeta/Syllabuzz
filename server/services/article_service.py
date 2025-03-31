# Updated article_service.py with improved historical content fetch
import logging
import requests
from datetime import datetime, timedelta
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
            url = "https://newsapi.org/v2/everything"
            
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
                
            # Add keywords if available
            if article.get("keywords"):
                article_doc["keywords"] = article.get("keywords")
                
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
            results = list(articles_collection.find(search_query)
                           .sort("published_at", -1)
                           .skip(skip)
                           .limit(limit))
                           
            # Convert ObjectId to string and add type
            for item in results:
                item["_id"] = str(item["_id"])
                # Add a type field to distinguish between news and academic
                if item.get("source_name") == "arXiv":
                    item["type"] = "academic"
                else:
                    item["type"] = "news"
                    
            logger.info(f"Found {len(results)} combined items matching query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching combined content: {str(e)}")
            return []                 
        
    def get_combined_articles(self, category=None, limit=20, skip=0):
        """Get both news articles and academic papers, optionally filtered by category
        This method combines news articles and arXiv papers in a single list,
        sorted by published date"""
        try:
            # Build query
            query = {}
            
            # Add category filter if provided
            if category:
                # Handle special case "academic" to show only papers
                if category == "academic":
                    query["source_name"] = "arXiv"
                # For regular categories, try to match with either news categories or arXiv categories
                else:
                    query["$or"] = [
                        {"categories": category},  # Regular news article category
                        {"categories": {"$regex": category, "$options": "i"}}  # arXiv category (case insensitive)
                    ]
                    
            # Get articles from both sources
            combined_articles = list(articles_collection.find(query)
                            .sort("published_at", -1)
                            .skip(skip)
                            .limit(limit))
                            
            # Convert ObjectId to string for JSON serialization
            for article in combined_articles:
                article["_id"] = str(article["_id"])
                # Add a type field to distinguish between news and academic
                if article.get("source_name") == "arXiv":
                    article["type"] = "academic"
                else:
                    article["type"] = "news"
                    
            logger.info(f"Retrieved {len(combined_articles)} combined articles/papers from database for category: {category}")
            return combined_articles
        except Exception as e:
            logger.error(f"Error getting combined articles: {str(e)}")
            return []    

    def search_combined(self, query, limit=20, skip=0):
        """Enhanced search for both news articles and academic papers
        Uses text search and supports more complex queries"""
        try:
            # Build search query
            search_query = {
                "$text": {"$search": query}
            }
            
            # Perform search
            results = list(articles_collection.find(search_query)
                           .sort([
                               ("score", {"$meta": "textScore"}),  # Sort by relevance
                               ("published_at", -1)                # Then by date
                           ])
                           .skip(skip)
                           .limit(limit))
                           
            # Convert ObjectId to string and add type
            for item in results:
                item["_id"] = str(item["_id"])
                # Add a type field to distinguish between news and academic
                if item.get("source_name") == "arXiv":
                    item["type"] = "academic"
                else:
                    item["type"] = "news"
                    
            logger.info(f"Found {len(results)} combined items matching query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching combined content: {str(e)}")
            return []

    def fetch_targeted_articles(self, keywords, count=30, page=1):
        """
        Fetch articles that are targeted to specific keywords for better relevance
        
        Args:
            keywords (str or list): Keywords to search for, comma-separated or list
            count (int): Number of articles to fetch
            page (int): Page number for pagination
            
        Returns:
            int: Number of articles stored
        """
        try:
            # Use the "everything" endpoint instead of "top-headlines" for deeper search
            url = "https://newsapi.org/v2/everything"
            
            # Convert keywords list to proper query format
            if isinstance(keywords, list):
                query = " OR ".join([f'"{k}"' for k in keywords])
            else:
                query = keywords
                
            # Add CS/programming specific terms to improve relevance
            query = f"({query}) AND (programming OR software OR technology OR algorithm OR data OR computer)"
            
            # Prepare parameters for deeper search with extended date range
            # Get articles from last 30 days instead of default 7 for better historical coverage
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            params = {
                "apiKey": self.news_api_key,
                "q": query,
                "pageSize": count,
                "page": page,
                "language": "en",
                "from": from_date,
                "sortBy": "relevancy"  # Use relevancy instead of date
            }
            
            # Make API request
            response = requests.get(url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return 0
                
            # Parse response
            data = response.json()
            
            # Check if articles were returned
            if data.get("status") != "ok" or "articles" not in data:
                logger.error(f"Invalid response from NewsAPI: {data}")
                return 0
                
            articles = data["articles"]
            logger.info(f"Fetched {len(articles)} targeted articles for keywords: {keywords}")
            
            # Store each article
            stored_count = 0
            for article in articles:
                # Add keywords as categories
                if isinstance(keywords, list):
                    article["keywords"] = keywords
                else:
                    article["keywords"] = [k.strip() for k in keywords.split(",")]
                    
                # Store article
                result = self.store_article(article)
                if result:
                    stored_count += 1
                    
            logger.info(f"Stored {stored_count} targeted articles for keywords: {keywords}")
            return stored_count
        except Exception as e:
            logger.error(f"Error fetching targeted articles: {str(e)}")
            return 0

    def fetch_module_specific_articles(self, module_id, count=25):
        """
        Fetch articles specifically for a module based on its title and keywords
        with improvements for better relevance
        
        Args:
            module_id (str or ObjectId): ID of the module
            count (int): Number of articles to fetch
            
        Returns:
            int: Number of articles stored
        """
        try:
            # Get module details
            from utils.db_utils import modules_collection
            module = modules_collection.find_one({"_id": ObjectId(module_id) if isinstance(module_id, str) else module_id})
            
            if not module:
                logger.error(f"Module not found: {module_id}")
                return 0
                
            # Extract keywords from module title and description
            title = module.get("name", "")
            description = module.get("description", "")
            
            # Simple keyword extraction (you can use NLP libraries for better extraction)
            keywords = []
            
            # Add title keywords
            title_words = [w.lower() for w in title.split() if len(w) > 3]
            keywords.extend(title_words)
            
            # Extract keywords from description
            if description:
                # Remove common words
                common_words = {"the", "and", "that", "for", "with", "this", "are", "will", "what", "about"}
                desc_words = [w.lower() for w in description.split() if len(w) > 3 and w.lower() not in common_words]
                keywords.extend(desc_words)
            
            # Add specific module keywords if available
            if "keywords" in module and module["keywords"]:
                # Prioritize module keywords by adding them multiple times
                for kw in module["keywords"]:
                    keywords.extend([kw.lower()] * 3)  # Add each keyword 3 times for higher weight
                
            # Remove duplicates but maintain priority of keywords that appeared multiple times
            from collections import Counter
            keyword_count = Counter(keywords)
            
            # Get keywords ordered by frequency
            prioritized_keywords = [k for k, _ in keyword_count.most_common(10)]
            
            # Create different keyword combinations for better coverage
            keyword_groups = []
            
            # Group 1: Top 5 keywords
            if len(prioritized_keywords) >= 5:
                keyword_groups.append(prioritized_keywords[:5])
                
            # Group 2: Next 5 keywords
            if len(prioritized_keywords) >= 10:
                keyword_groups.append(prioritized_keywords[5:10])
                
            # Group 3: Mix of keywords with module name
            if title and len(prioritized_keywords) >= 3:
                keyword_groups.append([title] + prioritized_keywords[:3])
            
            # Fetch articles based on these keyword groups
            total_articles = 0
            
            # Calculate articles per group based on total count
            articles_per_group = count // (len(keyword_groups) or 1)
            
            for group in keyword_groups:
                # Fetch articles based on this keyword group
                article_count = self.fetch_targeted_articles(
                    keywords=group, 
                    count=articles_per_group
                )
                total_articles += article_count
                
            # If we didn't fetch enough articles, try with the full list as a backup
            if total_articles < count // 2 and prioritized_keywords:
                article_count = self.fetch_targeted_articles(
                    keywords=prioritized_keywords[:7],  # Use top 7 keywords
                    count=count - total_articles
                )
                total_articles += article_count
                
            return total_articles
        except Exception as e:
            logger.error(f"Error fetching module-specific articles: {str(e)}")
            return 0