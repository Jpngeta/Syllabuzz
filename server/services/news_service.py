# NewsAPI integration
import requests
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPIClientService:
    def __init__(self, api_key):
        """Initialize the NewsAPI client"""
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        logger.info("Initialized NewsAPI client")

    def get_top_headlines(self, category=None, country="us", page=1, page_size=40):
        """Get top headlines from NewsAPI"""
        try:
            url = f"{self.base_url}/top-headlines"
            
            # Prepare parameters
            params = {
                "apiKey": self.api_key,
                "country": country,
                "page": page,
                "pageSize": page_size
            }
            
            # Add category if specified
            if category:
                params["category"] = category
                
            # Make API request
            response = requests.get(url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return {"status": "error", "articles": []}
                
            # Parse response
            data = response.json()
            logger.info(f"Fetched {len(data.get('articles', []))} headlines from NewsAPI")
            return data
        except Exception as e:
            logger.error(f"Error getting top headlines: {str(e)}")
            return {"status": "error", "articles": []}

    def search_everything(self, query, sort_by="relevancy", language="en", page=1, page_size=20):
        """Search all articles from NewsAPI"""
        try:
            url = f"{self.base_url}/everything"
            
            # Get articles from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # Prepare parameters
            params = {
                "apiKey": self.api_key,
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "from": from_date,
                "page": page,
                "pageSize": page_size
            }
            
            # Make API request
            response = requests.get(url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return {"status": "error", "articles": []}
                
            # Parse response
            data = response.json()
            logger.info(f"Fetched {len(data.get('articles', []))} articles matching query: {query}")
            return data
        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return {"status": "error", "articles": []}

    def get_sources(self, category=None, language="en", country=None):
        """Get news sources from NewsAPI"""
        try:
            url = f"{self.base_url}/sources"
            
            # Prepare parameters
            params = {
                "apiKey": self.api_key,
                "language": language
            }
            
            # Add optional parameters
            if category:
                params["category"] = category
                
            if country:
                params["country"] = country
                
            # Make API request
            response = requests.get(url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return {"status": "error", "sources": []}
                
            # Parse response
            data = response.json()
            logger.info(f"Fetched {len(data.get('sources', []))} sources from NewsAPI")
            return data
        except Exception as e:
            logger.error(f"Error getting sources: {str(e)}")
            return {"status": "error", "sources": []}