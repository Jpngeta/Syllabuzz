# Configuration settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/cs_articles_recommender')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'cs_articles_recommender')

# News API configuration
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')

# SBERT model configuration
SBERT_MODEL_NAME = os.environ.get('SBERT_MODEL_NAME', 'all-MiniLM-L6-v2')

# Scheduler configuration
SCHEDULER_INTERVAL_MINUTES = int(os.environ.get('SCHEDULER_INTERVAL_MINUTES', 5))

# Relevance threshold for recommendations
RELEVANCE_THRESHOLD = float(os.environ.get('RELEVANCE_THRESHOLD', 0.2))

# Flask app configuration
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')

# Default categories for articles
ARTICLE_CATEGORIES = ['technology', 'science', 'education']

# Targeted content fetching settings
# CS categories for arXiv papers
ARXIV_CS_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.DS", "cs.SE", "cs.DB", "cs.CR", "cs.NE"]

# Number of articles/papers to fetch per module
MODULE_CONTENT_FETCH_COUNT = 10

# Keywords to add to general CS content fetching
GENERAL_CS_KEYWORDS = ["programming", "algorithm", "data structure", "artificial intelligence",
                      "machine learning", "computer science", "software engineering"]