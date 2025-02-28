import threading
import time
import logging
import schedule
from datetime import datetime
import os
import sys

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Then import your services
from services import article_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_category_articles(category):
    """Fetch articles for a category in the background"""
    try:
        logger.info(f"Background task: Fetching {category} articles")
        articles_data = article_service.get_articles(category=category, page=1)
        logger.info(f"Background task: Fetched {len(articles_data.get('articles', []))} {category} articles")
    except Exception as e:
        logger.error(f"Background task error fetching {category} articles: {str(e)}")

def reset_api_counters():
    """Reset API rate limiting counters"""
    logger.info("Resetting API request counters")
    news_api.reset_daily_count()

def run_scheduler():
    """Run the scheduled tasks"""
    # Setup schedules
    logger.info("Starting scheduler")
    
    # Fetch categories every few hours
    schedule.every(4).hours.do(fetch_category_articles, category='business')
    schedule.every(4).hours.do(fetch_category_articles, category='technology')
    schedule.every(6).hours.do(fetch_category_articles, category='entertainment')
    schedule.every(6).hours.do(fetch_category_articles, category='health')
    schedule.every(8).hours.do(fetch_category_articles, category='science')
    schedule.every(8).hours.do(fetch_category_articles, category='sports')
    
    # Reset counters at midnight
    schedule.every().day.at("00:00").do(reset_api_counters)
    
    # First run immediately
    for category in ['business', 'technology']:
        fetch_category_articles(category)
    
    # Run the scheduler in a loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def start_scheduler():
    """Start the scheduler in a background thread"""
    try:
        logger.info("Starting background scheduler thread")
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True  # Daemonize so it exits when main thread exits
        scheduler_thread.start()
        logger.info("Background scheduler started")
        return True
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return False