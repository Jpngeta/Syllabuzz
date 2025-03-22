# Updated scheduler_service.py with improved content fetching
import threading
import time
import logging
import schedule
from datetime import datetime
from config import SCHEDULER_INTERVAL_MINUTES, ARTICLE_CATEGORIES, GENERAL_CS_KEYWORDS, MODULE_CONTENT_FETCH_COUNT, ARXIV_CS_CATEGORIES
from services.article_service import ArticleService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, article_service, embedding_service, arxiv_service=None):
        """Initialize the scheduler service"""
        self.article_service = article_service
        self.embedding_service = embedding_service
        self.arxiv_service = arxiv_service 
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
            
            # Fetch regular articles every day
            schedule.every(24).hours.do(self.fetch_articles)
            
            # Fetch targeted content for modules every 12 hours
            schedule.every(12).hours.do(self.fetch_targeted_content_for_modules)
            
            # Fetch keyword-based content every 3 days for broader coverage
            schedule.every(3).days.do(self.fetch_general_keyword_content)
            
            # Update article embeddings every 15 minutes
            schedule.every(15).minutes.do(self.update_article_embeddings)
            
            # Update module embeddings daily
            schedule.every().day.do(self.update_module_embeddings)
            
            # Update relevance scores every hour
            schedule.every(1).hours.do(self.update_relevance_scores)
            
            # Run immediately on startup for initial data population
            self.fetch_articles()
            self.fetch_targeted_content_for_modules()
            self.fetch_general_keyword_content()
            self.update_article_embeddings()
            
            # Run the scheduler loop
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            self.is_running = False

    def fetch_articles(self):
        """Fetch new articles from all categories and arXiv with increased count"""
        try:
            logger.info("Running scheduled task: fetch_articles")
            
            # Fetch more news articles for each category
            for category in ARTICLE_CATEGORIES:
                try:
                    logger.info(f"Fetching articles for category: {category}")
                    # Fetch more articles per category
                    self.article_service.fetch_and_store_articles(category=category, count=20)
                except Exception as e:
                    logger.error(f"Error fetching articles for category {category}: {str(e)}")
            
            # Fetch arXiv papers if service is available
            if self.arxiv_service:
                try:
                    for category in ARXIV_CS_CATEGORIES:
                        logger.info(f"Fetching arXiv papers for category: {category}")
                        # Fetch more papers per category
                        self.arxiv_service.fetch_and_store_papers(search_query=category, max_results=15, years_limit=5)
                except Exception as e:
                    logger.error(f"Error fetching arXiv papers: {str(e)}")
                    
            logger.info(f"Completed fetching articles at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in fetch_articles task: {str(e)}")
            return False

    def fetch_targeted_content_for_modules(self):
        """Fetch targeted content (articles and papers) specifically for each module with increased counts"""
        try:
            logger.info("Running scheduled task: fetch_targeted_content_for_modules")
            
            # Get all modules
            from utils.db_utils import modules_collection
            modules = list(modules_collection.find({}))
            
            total_articles = 0
            total_papers = 0
            
            # For each module, fetch relevant content
            for module in modules:
                module_id = module["_id"]
                module_name = module.get("name", "Unknown")
                
                try:
                    logger.info(f"Fetching targeted content for module: {module_name}")
                    
                    # Fetch relevant news articles for this module
                    if self.article_service:
                        # Increased count from 10 to 25 for better coverage
                        article_count = self.article_service.fetch_module_specific_articles(
                            module_id=module_id, count=25
                        )
                        total_articles += article_count
                    
                    # Fetch relevant academic papers for this module
                    if self.arxiv_service:
                        # Increased count from 10 to 25
                        paper_count = self.arxiv_service.fetch_module_specific_papers(
                            module_id=module_id, 
                            max_results=25,
                            years_limit=5
                        )
                        total_papers += paper_count
                        
                    logger.info(f"Fetched {article_count} articles and {paper_count} papers for module: {module_name}")
                    
                except Exception as e:
                    logger.error(f"Error fetching content for module {module_name}: {str(e)}")
            
            # Update embeddings for the new content
            if total_articles > 0 or total_papers > 0:
                self.update_article_embeddings()
                self.update_relevance_scores()
                
            logger.info(f"Completed fetching targeted content: {total_articles} articles, {total_papers} papers")
            return True
        except Exception as e:
            logger.error(f"Error in fetch_targeted_content_for_modules task: {str(e)}")
            return False

    def fetch_general_keyword_content(self):
        """Fetch content for general CS keywords to ensure broad coverage"""
        try:
            logger.info("Running scheduled task: fetch_general_keyword_content")
            
            total_articles = 0
            total_papers = 0
            
            # First, fetch from the predefined general CS keywords
            for keyword in GENERAL_CS_KEYWORDS:
                try:
                    logger.info(f"Fetching content for keyword: {keyword}")
                    
                    # Fetch news articles
                    if self.article_service:
                        article_count = self.article_service.fetch_targeted_articles(
                            keywords=keyword, count=30
                        )
                        total_articles += article_count
                    
                    # Fetch arXiv papers
                    if self.arxiv_service:
                        paper_count = self.arxiv_service.fetch_targeted_papers(
                            keywords=keyword, 
                            max_results=30,
                            years_limit=5
                        )
                        total_papers += paper_count
                        
                    logger.info(f"Fetched {article_count} articles and {paper_count} papers for keyword: {keyword}")
                    
                except Exception as e:
                    logger.error(f"Error fetching content for keyword {keyword}: {str(e)}")
            
            # Now try to extract additional trending keywords from top articles
            try:
                from utils.db_utils import articles_collection
                import re
                from collections import Counter
                
                # Get recent articles with highest interaction counts
                from utils.db_utils import interactions_collection
                
                pipeline = [
                    {"$group": {"_id": "$article_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 50}
                ]
                
                top_articles = list(interactions_collection.aggregate(pipeline))
                article_ids = [doc["_id"] for doc in top_articles]
                
                if article_ids:
                    articles = list(articles_collection.find({"_id": {"$in": article_ids}}))
                    
                    # Extract potential keywords from titles and descriptions
                    text_content = ""
                    for article in articles:
                        if article.get("title"):
                            text_content += " " + article["title"]
                        if article.get("description"):
                            text_content += " " + article["description"]
                    
                    # Simple keyword extraction (could be improved with NLP)
                    words = re.findall(r'\b[A-Za-z][A-Za-z]{3,}\b', text_content)
                    word_counts = Counter(words)
                    
                    # Filter out common words
                    common_words = {"the", "and", "that", "with", "have", "this", "from", "they", "will", "what", "about"}
                    trending_keywords = [word for word, count in word_counts.most_common(10) 
                                        if word.lower() not in common_words]
                    
                    # Fetch content for these trending keywords
                    if trending_keywords:
                        logger.info(f"Extracted trending keywords: {trending_keywords}")
                        
                        if self.article_service:
                            article_count = self.article_service.fetch_targeted_articles(
                                keywords=trending_keywords[:5], count=25
                            )
                            total_articles += article_count
                        
                        if self.arxiv_service:
                            paper_count = self.arxiv_service.fetch_targeted_papers(
                                keywords=trending_keywords[:5], max_results=25
                            )
                            total_papers += paper_count
            
            except Exception as e:
                logger.error(f"Error extracting trending keywords: {str(e)}")
            
            # Update embeddings for the new content
            if total_articles > 0 or total_papers > 0:
                self.update_article_embeddings()
                self.update_relevance_scores()
                
            logger.info(f"Completed fetching keyword content: {total_articles} articles, {total_papers} papers")
            return True
        except Exception as e:
            logger.error(f"Error in fetch_general_keyword_content task: {str(e)}")
            return False

    def update_article_embeddings(self):
        """Update embeddings for recently added articles and papers with increased time range"""
        try:
            logger.info("Running scheduled task: update_article_embeddings")
            # Increase days from 1 to 7 to ensure older articles get embeddings too
            self.embedding_service.update_recent_article_embeddings(days=7)
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
        """Update relevance scores between modules and articles/papers with increased processing"""
        try:
            logger.info("Running scheduled task: update_relevance_scores")
            self.embedding_service.update_relevance_scores()
            logger.info(f"Completed updating relevance scores at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Error in update_relevance_scores task: {str(e)}")
            return False