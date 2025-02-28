from services.news_service import NewsAPIClientService
from db import db
import os
from dotenv import load_dotenv
import time
import threading
from datetime import datetime, timedelta
import schedule

# Load environment variables from .env file
load_dotenv()

# Initialize news service
news_service = NewsAPIClientService(api_key=os.environ.get('NEWS_API_KEY'))

def fetch_and_store_articles():
    """Fetch articles from News API and store them in the database."""
    print(f"[{datetime.now()}] Fetching articles...")
    
    categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    
    for category in categories:
        try:
            # Fetch articles from API
            response = news_service.get_top_headlines(category=category, page_size=20)
            articles = news_service.format_articles(response)
            
            for article in articles:
                # Check if article already exists
                existing = db.articles.find_one({'url': article['url']})
                if not existing:
                    db.articles.insert_one(article)
            
            print(f"[{datetime.now()}] Fetched {len(articles)} {category} articles")
        except Exception as e:
            print(f"[{datetime.now()}] Error fetching {category} articles: {e}")
    
    # Cleanup old articles (keep last 30 days)
    cutoff_date = datetime.now() - timedelta(days=30)
    db.articles.delete_many({'published_at': {'$lt': cutoff_date}})
    
    print(f"[{datetime.now()}] Article fetch complete")

def run_scheduler():
    """Run the scheduled tasks."""
    # Fetch articles immediately on startup
    fetch_and_store_articles()
    
    # Schedule to run every 3 hours
    schedule.every(3).hours.do(fetch_and_store_articles)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute between checks

def start_scheduler():
    """Start the scheduler in a background thread."""
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Thread will exit when main program exits
    scheduler_thread.start()

if __name__ == "__main__":
    run_scheduler()