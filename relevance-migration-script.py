#!/usr/bin/env python3
"""
Script to calculate and update module-article relevance scores in the database.

This script will:
1. Verify that modules and articles have embeddings
2. Calculate relevance scores between each module and article
3. Store the scores in the relevance_collection
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime
from tqdm import tqdm  # For progress bar (install with pip install tqdm)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update_relevance')

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
    
    def update_module_article_relevance(module, article):
        """Calculate and update relevance between a module and an article"""
        try:
            # Get embeddings
            module_embedding = module.get("vector_embedding")
            article_embedding = article.get("vector_embedding")
            
            if not module_embedding or not article_embedding:
                return None
                
            # Calculate similarity
            relevance_score = calculate_similarity(module_embedding, article_embedding)
            
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
    
    def update_all_relevance_scores():
        """Update relevance scores between all modules and articles with embeddings"""
        try:
            # Get modules and articles with embeddings
            modules = list(modules_collection.find({"vector_embedding": {"$ne": None}}))
            
            # Limit articles to most recent ones to avoid processing too many
            articles = list(articles_collection.find(
                {"vector_embedding": {"$ne": None}}
            ).sort("published_at", -1).limit(500))
            
            logger.info(f"Processing relevance scores for {len(modules)} modules and {len(articles)} articles")
            
            # Optional: Clear existing relevance scores
            # relevance_collection.delete_many({})
            # logger.info("Cleared existing relevance scores")
            
            total_pairs = len(modules) * len(articles)
            count = 0
            high_relevance = 0
            
            # Use tqdm for progress bar
            with tqdm(total=total_pairs, desc="Calculating relevance") as pbar:
                for module in modules:
                    module_name = module.get("name", str(module["_id"]))
                    
                    for article in articles:
                        relevance_score = update_module_article_relevance(module, article)
                        
                        if relevance_score and relevance_score >= RELEVANCE_THRESHOLD:
                            high_relevance += 1
                            
                        count += 1
                        pbar.update(1)
            
            logger.info(f"Updated {count} relevance scores")
            logger.info(f"Found {high_relevance} high-relevance pairs (threshold: {RELEVANCE_THRESHOLD})")
            
            # Verify results
            relevance_count = relevance_collection.count_documents({})
            high_relevance_count = relevance_collection.count_documents({"relevance_score": {"$gte": RELEVANCE_THRESHOLD}})
            
            logger.info(f"Total relevance scores in database: {relevance_count}")
            logger.info(f"High relevance scores in database: {high_relevance_count}")
            
            return count
        except Exception as e:
            logger.error(f"Error updating all relevance scores: {str(e)}")
            return 0
    
    def main():
        """Main function to run the script"""
        logger.info("Starting module-article relevance update")
        
        # Check if embeddings exist
        if not validate_embeddings():
            logger.error("Embeddings validation failed")
            sys.exit(1)
        
        # Update relevance scores
        try:
            start_time = datetime.now()
            count = update_all_relevance_scores()
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
