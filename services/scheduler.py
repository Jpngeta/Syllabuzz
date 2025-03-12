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
    
    # Add this to your existing services/scheduler.py file

def start_enhanced_scheduler(content_service=None, recommendation_engine=None, embedding_service=None):
    """Start the enhanced scheduler with recommendation capabilities"""
    try:
        logger.info("Starting enhanced background scheduler")
        
        # Create a thread that runs both the original scheduler tasks
        # and the new recommendation tasks
        scheduler_thread = threading.Thread(target=lambda: run_enhanced_scheduler(
            content_service, recommendation_engine, embedding_service
        ))
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        logger.info("Enhanced background scheduler started")
        return True
    except Exception as e:
        logger.error(f"Error starting enhanced scheduler: {str(e)}")
        return False

def run_enhanced_scheduler(content_service=None, recommendation_engine=None, embedding_service=None):
    """Run the enhanced scheduled tasks"""
    # Setup the original schedules
    logger.info("Starting enhanced scheduler")
    
    # Original tasks
    schedule.every(4).hours.do(fetch_category_articles, category='business')
    schedule.every(4).hours.do(fetch_category_articles, category='technology')
    schedule.every(6).hours.do(fetch_category_articles, category='entertainment')
    schedule.every(6).hours.do(fetch_category_articles, category='health')
    schedule.every(8).hours.do(fetch_category_articles, category='science')
    schedule.every(8).hours.do(fetch_category_articles, category='sports')
    
    # Reset counters at midnight
    schedule.every().day.at("00:00").do(reset_api_counters)
    
    # Add new recommendation-related tasks if services are available
    if recommendation_engine and embedding_service:
        # Update article embeddings every 12 hours
        schedule.every(12).hours.do(
            lambda: update_article_embeddings(recommendation_engine)
        )
        
        # Update module relevance scores daily
        schedule.every().day.at("03:00").do(
            lambda: update_module_relevance(recommendation_engine, content_service)
        )
    
    # First run immediately
    for category in ['business', 'technology']:
        fetch_category_articles(category)
    
    # Run the scheduler in a loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def update_article_embeddings(recommendation_engine, batch_size=50):
    """Update embeddings for articles that don't have them"""
    try:
        logger.info("Updating article embeddings")
        
        # Find articles without embeddings
        from db import db
        articles = list(db.articles.find(
            {"vector_embedding": {"$exists": False}}
        ).limit(batch_size))
        
        if not articles:
            logger.info("No articles found needing embeddings")
            return
            
        count = 0
        for article in articles:
            try:
                # Generate embedding
                text = article.get('title', '') + ' ' + article.get('description', '') + ' ' + article.get('content', '')
                if not text.strip():
                    continue
                    
                embedding = recommendation_engine.embedding_service.generate_embedding(text)
                
                # Update article
                db.articles.update_one(
                    {"_id": article["_id"]},
                    {"$set": {"vector_embedding": embedding.tolist()}}
                )
                count += 1
            except Exception as e:
                logger.error(f"Error updating embedding for article {article.get('_id')}: {str(e)}")
                
        logger.info(f"Updated embeddings for {count} articles")
    except Exception as e:
        logger.error(f"Error in update_article_embeddings: {str(e)}")

def update_module_relevance(recommendation_engine, content_service=None):
    """Update relevance scores between modules and articles"""
    try:
        logger.info("Updating module-article relevance scores")
        
        # Get all modules
        from db import db
        modules = list(db.modules.find())
        
        for module in modules:
            try:
                # Get module embedding
                if 'vector_embedding' not in module and recommendation_engine.embedding_service:
                    text = module.get('name', '') + ' ' + module.get('description', '') + ' ' + ' '.join(module.get('keywords', []))
                    embedding = recommendation_engine.embedding_service.generate_embedding(text)
                    
                    # Update module
                    db.modules.update_one(
                        {"_id": module["_id"]},
                        {"$set": {"vector_embedding": embedding.tolist()}}
                    )
                    module['vector_embedding'] = embedding.tolist()
                
                # Get articles with embeddings
                articles = list(db.articles.find({"vector_embedding": {"$exists": True}}))
                
                # Calculate relevance
                for article in articles:
                    try:
                        # If both have embeddings, calculate similarity
                        if 'vector_embedding' in module and 'vector_embedding' in article:
                            similarity = recommendation_engine.embedding_service.calculate_similarity(
                                module['vector_embedding'], 
                                article['vector_embedding']
                            )
                            
                            # Store relevance
                            db.module_article_relevance.update_one(
                                {
                                    "module_id": module["_id"],
                                    "article_id": article["_id"]
                                },
                                {
                                    "$set": {
                                        "relevance_score": float(similarity),
                                        "updated_at": datetime.now()
                                    }
                                },
                                upsert=True
                            )
                    except Exception as inner_e:
                        logger.error(f"Error calculating relevance for article {article.get('_id')}: {str(inner_e)}")
                
                logger.info(f"Updated relevance scores for module: {module.get('name')}")
            except Exception as e:
                logger.error(f"Error updating relevance for module {module.get('name')}: {str(e)}")
                
        logger.info("Module-article relevance update complete")
    except Exception as e:
        logger.error(f"Error in update_module_relevance: {str(e)}")