# Updated configuration settings with improved content fetching parameters
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

# Relevance threshold for recommendations (lowered slightly to include more content)
RELEVANCE_THRESHOLD = float(os.environ.get('RELEVANCE_THRESHOLD', 0.3))

# Flask app configuration
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')

# Authentication settings
TOKEN_EXPIRY_HOURS = 48  # Email verification token expiry time
PASSWORD_RESET_EXPIRY_HOURS = 24  # Password reset token expiry time
SESSION_EXPIRY_DAYS = 30  # Remember me session expiry time

# JWT Authentication settings
JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', 24))  # JWT token expiry time
JWT_ALGORITHM = 'HS256'
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)  # Use same key as app or separate one
JWT_ACCESS_TOKEN_EXPIRES = JWT_EXPIRY_HOURS * 3600  # In seconds
JWT_REFRESH_TOKEN_EXPIRES = SESSION_EXPIRY_DAYS * 24 * 3600  # In seconds

# Email configuration
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@syllabuzz.com')
APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')


# Default categories for articles (expanded)
ARTICLE_CATEGORIES = ['technology', 'science', 'education', 'business']

# Targeted content fetching settings
# CS categories for arXiv papers (expanded with more categories)
ARXIV_CS_CATEGORIES = [
    # Core CS categories
    "cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.DS", "cs.SE", "cs.DB", "cs.CR", "cs.NE",
    # Additional categories
    "cs.DC", "cs.HC", "cs.IR", "cs.PL", "cs.NI", "cs.OS", "cs.RO", "cs.AR", "cs.CC","stat.ML"
]

# Number of articles/papers to fetch per module (increased)
MODULE_CONTENT_FETCH_COUNT = 15

# Keywords to add to general CS content fetching (expanded)
GENERAL_CS_KEYWORDS = [
    # Programming and software
    "programming", "algorithm", "data structure", "software engineering", "code",
    # AI and ML
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    # Computer science core
    "computer science", "computational", "computing", "information technology",
    # Web and mobile
    "web development", "mobile development", "app development", "responsive design",
    # Data and databases
    "database", "data science", "big data", "data analysis", "SQL", "NoSQL",
    # Security
    "cybersecurity", "encryption", "network security", "ethical hacking",
    # Systems
    "operating system", "distributed systems", "cloud computing", "microservices",
    # Modern tech
    "blockchain", "quantum computing", "augmented reality", "virtual reality"
]

# Historical content settings
# Number of days to look back for content (increased from default)
CONTENT_HISTORY_DAYS = 90

# Minimum number of articles per category to maintain
MIN_ARTICLES_PER_CATEGORY = 50

# Batch processing limits for embedding updates
EMBEDDING_BATCH_SIZE = 500

# API Paths
API_PREFIX = '/api'
AUTH_API_PREFIX = '/api/auth'

# Cookie settings for JWT
JWT_COOKIE_SECURE = os.environ.get('JWT_COOKIE_SECURE', 'False').lower() == 'true'  # Set to True in production with HTTPS
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = 'Lax'  # Prevents CSRF, adjust based on your needs

# CORS settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')