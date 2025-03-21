#!/usr/bin/env python3
"""
Script to calculate and update module-article relevance scores in the database.

This script will:
1. Verify that modules and articles have embeddings
2. Calculate relevance scores between each module and article
3. Store the scores in the relevance_collection
4. Process ALL articles in the database, not just the most recent ones

Enhanced version to handle large numbers of articles efficiently.
"""

import os
import sys
import logging
import numpy as np
import argparse
from datetime import datetime
from tqdm import tqdm  # For progress bar (install with pip install tqdm)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update_relevance')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Update relevance scores for all articles')
    parser.add_argument('--batch-size', type=int, default=500, 
                      help='Number of articles to process in each batch (default: 500)')
    parser.add_argument('--clear-existing', action='store_true',
                      help='Clear existing relevance scores before processing')
    parser.add_argument('--threshold', type=float, default=None,
                      help='Override the relevance threshold from config')
    return parser.parse_args()

# Make sure we can import from the application
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

try:
    # Import application components
    from config import MONGO_URI, MONGO_DB_NAME, RELEVANCE_THRESHOLD
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    modules_collection = db.modules
    articles_collection = db.articles
    relevance_collection = db.module_article_relevance
    
    def calculate_similarity(embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
            
        try:
            # Convert to numpy arrays if they are lists
            if isinstance(embedding1, list):
                embedding1 = np.array(embedding1)
            
            if isinstance(embedding2, list):
                embedding2 = np.array(embedding2)
                
            # Calculate cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def validate_embeddings():
        """Check if modules and articles have embeddings"""
        modules_with_embeddings = modules_collection.count_documents({"vector_embedding": {"$ne": None}})
        total_modules = modules_collection.count_documents({})
        
        articles_with_embeddings = articles_collection.count_documents({"vector_embedding": {"$ne": None}})
        total_articles = articles_collection.count_documents({})
        
        logger.info(f"Modules with embeddings: {modules_with_embeddings}/{total_modules}")
        logger.info(f"Articles with embeddings: {articles_with_embeddings}/{total_articles}")
        
        if modules_with_embeddings == 0:
            logger.error("No modules have embeddings. Please run update_embeddings_cli.py --target modules first.")
            return False
            
        if articles_with_embeddings == 0:
            logger.error("No articles have embeddings. Please run update_embeddings_cli.py --target articles first.")
            return False
            
        return True
    
    def update_module_article_relevance(module, article, threshold=RELEVANCE_THRESHOLD):
        """Calculate and update relevance between a module and an article"""
        try:
            # Get embeddings
            module_embedding = module.get("vector_embedding")
            article_embedding = article.get("vector_embedding")
            
            if not module_embedding or not article_embedding:
                return None
                
            # Calculate similarity
            relevance_score = calculate_similarity(module_embedding, article_embedding)
            
            # Only store score if it meets threshold (optional optimization)
            # if relevance_score < threshold:
            #     return relevance_score
            
            # Update or insert relevance score
            relevance_collection.update_one(
                {"module_id": module["_id"], "article_id": article["_id"]},
                {
                    "$set": {
                        "relevance_score": relevance_score,
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            
            return relevance_score
        except Exception as e:
            logger.error(f"Error updating module-article relevance: {str(e)}")
            return None
    
    def update_all_relevance_scores(batch_size=500, clear_existing=False, custom_threshold=None):
        """Update relevance scores between all modules and articles with embeddings
        
        Args:
            batch_size: Number of articles to process in each batch
            clear_existing: Whether to clear existing relevance scores
            custom_threshold: Override the relevance threshold from config
        """
        try:
            # Use custom threshold if provided, otherwise use config
            threshold = custom_threshold if custom_threshold is not None else RELEVANCE_THRESHOLD
            
            # Get modules with embeddings
            modules = list(modules_collection.find({"vector_embedding": {"$ne": None}}))
            
            # Count total articles with embeddings
            total_articles = articles_collection.count_documents({"vector_embedding": {"$ne": None}})
            
            logger.info(f"Processing relevance scores for {len(modules)} modules and {total_articles} articles")
            logger.info(f"Using relevance threshold: {threshold}")
            
            # Optional: Clear existing relevance scores
            if clear_existing:
                relevance_collection.delete_many({})
                logger.info("Cleared existing relevance scores")
            
            # Variables to track progress
            total_processed = 0
            high_relevance_count = 0
            start_time = datetime.now()
            
            # Process in batches to handle large numbers of articles
            for skip in range(0, total_articles, batch_size):
                # Get batch of articles
                batch_size_adjusted = min(batch_size, total_articles - skip)
                articles = list(articles_collection.find(
                    {"vector_embedding": {"$ne": None}}
                ).sort("published_at", -1).skip(skip).limit(batch_size_adjusted))
                
                logger.info(f"Processing batch {skip//batch_size + 1}: {len(articles)} articles")
                
                batch_count = 0
                batch_high_relevance = 0
                
                # Use tqdm for progress bar
                total_pairs = len(modules) * len(articles)
                with tqdm(total=total_pairs, desc=f"Batch {skip//batch_size + 1}") as pbar:
                    for module in modules:
                        module_name = module.get("name", str(module["_id"]))
                        
                        for article in articles:
                            relevance_score = update_module_article_relevance(module, article, threshold)
                            
                            if relevance_score and relevance_score >= threshold:
                                batch_high_relevance += 1
                                
                            batch_count += 1
                            pbar.update(1)
                
                total_processed += batch_count
                high_relevance_count += batch_high_relevance
                
                # Calculate and display progress
                elapsed_time = (datetime.now() - start_time).total_seconds()
                progress_pct = (total_processed / (total_articles * len(modules))) * 100
                remaining_pairs = (total_articles * len(modules)) - total_processed
                
                if total_processed > 0 and elapsed_time > 0:
                    pairs_per_second = total_processed / elapsed_time
                    remaining_time = remaining_pairs / pairs_per_second if pairs_per_second > 0 else 0
                    
                    logger.info(f"Progress: {progress_pct:.1f}% | High relevance in batch: {batch_high_relevance}")
                    logger.info(f"Estimated time remaining: {remaining_time/60:.1f} minutes")
            
            logger.info(f"Updated {total_processed} relevance scores")
            logger.info(f"Found {high_relevance_count} high-relevance pairs (threshold: {threshold})")
            
            # Verify results
            relevance_count = relevance_collection.count_documents({})
            db_high_relevance_count = relevance_collection.count_documents({"relevance_score": {"$gte": threshold}})
            
            logger.info(f"Total relevance scores in database: {relevance_count}")
            logger.info(f"High relevance scores in database: {db_high_relevance_count}")
            
            return total_processed
        except Exception as e:
            logger.error(f"Error updating all relevance scores: {str(e)}")
            return 0
    
    def main():
        """Main function to run the script"""
        args = parse_args()
        logger.info("Starting module-article relevance update for ALL articles")
        logger.info(f"Using batch size: {args.batch_size}")
        
        # Check if embeddings exist
        if not validate_embeddings():
            logger.error("Embeddings validation failed")
            sys.exit(1)
        
        # Update relevance scores
        try:
            start_time = datetime.now()
            count = update_all_relevance_scores(
                batch_size=args.batch_size,
                clear_existing=args.clear_existing,
                custom_threshold=args.threshold
            )
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Relevance update completed: processed {count} pairs in {duration:.2f} seconds")
        except Exception as e:
            logger.error(f"Error during relevance update: {str(e)}")
        finally:
            client.close()
            logger.info("Database connection closed")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error("Make sure you're running this script from the project root or the correct Python environment")
    sys.exit(1)