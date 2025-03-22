# Script to delete articles with relevance scores below threshold

import logging
import argparse
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Delete articles with low relevance scores')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='Minimum relevance score threshold (default: 0.1)')
    parser.add_argument('--mongo-uri', type=str, default='mongodb://localhost:27017/cs_articles_recommender',
                        help='MongoDB connection URI')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without making changes to identify what would be deleted')
    parser.add_argument('--categories', type=str, nargs='+',
                        help='Optional list of categories to filter by')
    parser.add_argument('--days', type=int, default=None,
                        help='Optional: Only process articles from the last N days')
    return parser.parse_args()

def get_database_connection(mongo_uri):
    """Connect to MongoDB and return db object"""
    try:
        client = MongoClient(mongo_uri)
        # Extract DB name from the MongoDB URI
        db_name = mongo_uri.split('/')[-1]
        db = client[db_name]
        logger.info(f"Connected to database: {db_name}")
        return db
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise

def delete_low_relevance_articles(db, threshold, dry_run=False, categories=None, days=None):
    """Delete articles with relevance scores below the threshold"""
    try:
        # Get collections
        articles_collection = db.articles
        relevance_collection = db.module_article_relevance
        
        # Build query for articles
        articles_query = {}
        if categories:
            articles_query["categories"] = {"$in": categories}
        
        if days:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            articles_query["published_at"] = {"$gte": cutoff_date}
        
        # Get all article IDs
        article_ids = [doc["_id"] for doc in articles_collection.find(articles_query, {"_id": 1})]
        logger.info(f"Found {len(article_ids)} articles matching the criteria")
        
        if not article_ids:
            logger.info("No articles found matching the criteria")
            return 0
        
        # Find articles to delete (those where ALL relevance scores are below threshold)
        articles_to_delete = []
        
        for article_id in article_ids:
            # Get all relevance scores for this article
            relevance_docs = list(relevance_collection.find({"article_id": article_id}))
            
            if not relevance_docs:
                # No relevance scores found - add to delete list
                articles_to_delete.append(article_id)
                continue
            
            # Check if ALL relevance scores are below threshold
            all_below_threshold = all(doc["relevance_score"] < threshold for doc in relevance_docs)
            
            if all_below_threshold:
                articles_to_delete.append(article_id)
        
        logger.info(f"Found {len(articles_to_delete)} articles with all relevance scores below {threshold}")
        
        # Delete relevance docs and articles
        if not dry_run and articles_to_delete:
            # Delete relevance documents first
            for article_id in articles_to_delete:
                relevance_collection.delete_many({"article_id": article_id})
            
            # Then delete the articles
            result = articles_collection.delete_many({"_id": {"$in": articles_to_delete}})
            logger.info(f"Deleted {result.deleted_count} articles with relevance below {threshold}")
            return result.deleted_count
        elif dry_run:
            # List articles that would be deleted in dry run mode
            logger.info("DRY RUN - No articles were deleted")
            for i, article_id in enumerate(articles_to_delete[:10]):  # Show first 10
                article = articles_collection.find_one({"_id": article_id})
                if article:
                    logger.info(f"Would delete: {i+1}. {article.get('title')} (ID: {article_id})")
            
            if len(articles_to_delete) > 10:
                logger.info(f"... and {len(articles_to_delete) - 10} more articles")
            
            return len(articles_to_delete)
        
        return 0
    except Exception as e:
        logger.error(f"Error deleting low relevance articles: {str(e)}")
        return 0

def main():
    """Main function"""
    args = parse_arguments()
    
    logger.info(f"Starting deletion of articles with relevance below {args.threshold}")
    if args.dry_run:
        logger.info("DRY RUN mode - no changes will be made")
    
    try:
        # Connect to the database
        db = get_database_connection(args.mongo_uri)
        
        # Delete low relevance articles
        count = delete_low_relevance_articles(
            db, 
            args.threshold, 
            args.dry_run, 
            args.categories, 
            args.days
        )
        
        if args.dry_run:
            logger.info(f"DRY RUN: Would delete {count} articles with relevance below {args.threshold}")
        else:
            logger.info(f"Successfully deleted {count} articles with relevance below {args.threshold}")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())