# Background task scheduler
import threading
import time
import logging
import schedule
from datetime import datetime
from config import SCHEDULER_INTERVAL_MINUTES, ARTICLE_CATEGORIES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, article_service, embedding_service):
        """Initialize the scheduler service"""
        self.article_service = article_service
        self.embedding_service = embedding_service
        self.is_running = False
        logger.info("Initialized scheduler service")

    def start(self):
        """Start the background scheduler thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        # Start in a new thread
        thread = threading.Thread(target=self.run_scheduler)
        thread.daemon = True  # Allow the thread to exit when the main program exits
        thread.start()
        
        self.is_running = True
        logger.info("Started scheduler service")

    def run_scheduler(self):
        """Run the scheduler with periodic tasks"""
        try:
            # Schedule tasks
            
            # Fetch articles every 5 minutes
            schedule.every(SCHEDULER_INTERVAL_MINUTES).minutes.do(self.fetch_articles)
            
            # Update article embeddings every 15 minutes
            schedule.every(10).minutes.do(self.update_article_embeddings)
            
            # Update module embeddings daily
            schedule.every().day.do(self.update_module_embeddings)
            
            # Update relevance scores every hour
            schedule.every(15).minutes.do(self.update_relevance_scores)
            
            # Run immediately on startup
            self.fetch_articles()
            self.update_article_embeddings()
            
            # Run the scheduler loop
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            self.is_running = False

    def fetch_articles(self):
        """Fetch new articles from all categories"""
        try:
            logger.info("Running scheduled task: fetch_articles")
            
            # Fetch articles for each category
            for category in ARTICLE_CATEGORIES:
                try:
                    logger.info(f"Fetching articles for category: {category}")
                    self.article_service.fetch_and_store_articles(category=category, count=20)
                except Exception as e:
                    logger.error(f"Error fetching articles for category {category}: {str(e)}")
                    
            logger.info(f"Completed fetching articles at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in fetch_articles task: {str(e)}")
            return False

    def update_article_embeddings(self):
        """Update embeddings for recently added articles"""
        try:
            logger.info("Running scheduled task: update_article_embeddings")
            self.embedding_service.update_recent_article_embeddings(days=1)
            logger.info(f"Completed updating article embeddings at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in update_article_embeddings task: {str(e)}")
            return False

    def update_module_embeddings(self):
        """Update embeddings for all modules"""
        try:
            logger.info("Running scheduled task: update_module_embeddings")
            self.embedding_service.update_all_module_embeddings()
            logger.info(f"Completed updating module embeddings at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in update_module_embeddings task: {str(e)}")
            return False

    def update_relevance_scores(self):
        """Update relevance scores between modules and articles"""
        try:
            logger.info("Running scheduled task: update_relevance_scores")
            self.embedding_service.update_relevance_scores()
            logger.info(f"Completed updating relevance scores at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in update_relevance_scores task: {str(e)}")
            return False