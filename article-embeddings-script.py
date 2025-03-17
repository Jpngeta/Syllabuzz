#!/usr/bin/env python3
"""
Migration script to generate vector embeddings for all articles.

This script connects to the MongoDB database, retrieves all articles,
and uses the SentenceTransformer model to generate and store vector embeddings.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from tqdm import tqdm  # For progress bar (install with pip install tqdm)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('article_embedding_migration.log')
    ]
)
logger = logging.getLogger('article_migration')

# Make sure we can import from the application
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

try:
    # Import application components
    from sentence_transformers import SentenceTransformer
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    
    # Import configuration (modify if your config is located elsewhere)
    try:
        from config import MONGO_URI, MONGO_DB_NAME, SBERT_MODEL_NAME
    except ImportError:
        # Fallback configuration
        logger.warning("Could not import config, using default values")
        MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/cs_articles_recommender')
        MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'cs_articles_recommender')
        SBERT_MODEL_NAME = os.environ.get('SBERT_MODEL_NAME', 'all-MiniLM-L6-v2')
    
    class ArticleEmbeddingMigration:
        def __init__(self, mongo_uri=MONGO_URI, db_name=MONGO_DB_NAME, model_name=SBERT_MODEL_NAME, batch_size=50):
            """Initialize the migration with database connection and embedding model"""
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.articles_collection = self.db.articles
            self.batch_size = batch_size
            
            # Load the SBERT model
            logger.info(f"Loading SBERT model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("Model loaded successfully")
        
        def generate_article_embedding(self, article):
            """Generate embedding vector for an article based on title, description, and content"""
            try:
                # Combine title, description, and content
                text_parts = []
                
                if article.get("title"):
                    text_parts.append(article["title"])
                    
                if article.get("description"):
                    text_parts.append(article["description"])
                    
                if article.get("content"):
                    # Limit content to first 1000 characters to avoid exceeding model limits
                    text_parts.append(article["content"][:1000])
                    
                text = " ".join(text_parts)
                
                if not text:
                    logger.warning(f"Article {article.get('_id')} has no text content")
                    return None
                
                # Generate embedding
                embedding = self.model.encode(text)
                return embedding.tolist()  # Convert numpy array to list for MongoDB storage
            except Exception as e:
                logger.error(f"Error generating article embedding: {str(e)}")
                return None
        
        def count_articles(self, only_missing=True):
            """Count articles that need embeddings"""
            query = {"vector_embedding": None} if only_missing else {}
            return self.articles_collection.count_documents(query)
        
        def update_article_embeddings(self, only_missing=True, limit=None):
            """Update embeddings for all articles or only those without embeddings"""
            try:
                # Prepare query
                query = {"vector_embedding": None} if only_missing else {}
                
                # Get total count for progress tracking
                total_count = self.articles_collection.count_documents(query)
                if limit and limit < total_count:
                    total_count = limit
                    
                logger.info(f"Found {total_count} articles to process")
                
                if total_count == 0:
                    logger.info("No articles to process")
                    return 0
                
                # Process articles
                cursor = self.articles_collection.find(query)
                if limit:
                    cursor = cursor.limit(limit)
                
                success_count = 0
                error_count = 0
                
                # Process in batches to avoid memory issues with large datasets
                articles_batch = []
                embeddings_batch = []
                batch_ids = []
                
                # Use tqdm for progress bar
                with tqdm(total=total_count, desc="Generating embeddings") as pbar:
                    for article in cursor:
                        try:
                            # Generate embedding
                            embedding = self.generate_article_embedding(article)
                            
                            if embedding:
                                articles_batch.append(article)
                                embeddings_batch.append(embedding)
                                batch_ids.append(article["_id"])
                                
                                # Process batch when it reaches the specified size
                                if len(articles_batch) >= self.batch_size:
                                    self._update_batch(articles_batch, embeddings_batch)
                                    success_count += len(articles_batch)
                                    articles_batch = []
                                    embeddings_batch = []
                                    batch_ids = []
                            else:
                                error_count += 1
                                logger.warning(f"Failed to generate embedding for article: {article.get('_id')}")
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error processing article {article.get('_id')}: {str(e)}")
                        
                        pbar.update(1)
                
                # Process remaining articles
                if articles_batch:
                    self._update_batch(articles_batch, embeddings_batch)
                    success_count += len(articles_batch)
                
                logger.info(f"Migration completed: {success_count} successful, {error_count} failed")
                return success_count
            except Exception as e:
                logger.error(f"Error updating article embeddings: {str(e)}")
                return 0
        
        def _update_batch(self, articles, embeddings):
            """Update a batch of articles with their embeddings"""
            try:
                bulk_operations = []
                
                for article, embedding in zip(articles, embeddings):
                    # Create update operation
                    bulk_operations.append(
                        {
                            "updateOne": {
                                "filter": {"_id": article["_id"]},
                                "update": {
                                    "$set": {
                                        "vector_embedding": embedding,
                                        "updated_at": datetime.now()
                                    }
                                }
                            }
                        }
                    )
                
                # Execute bulk update
                if bulk_operations:
                    result = self.articles_collection.bulk_write(bulk_operations)
                    logger.debug(f"Batch update: {result.modified_count} articles updated")
            except Exception as e:
                logger.error(f"Error in batch update: {str(e)}")
        
        def close(self):
            """Close the database connection"""
            self.client.close()
            logger.info("Database connection closed")
    
    def parse_args():
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description="Generate embeddings for articles")
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all articles, not just those without embeddings'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of articles to process'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of articles to process in a single batch'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Count articles but do not generate embeddings'
        )
        
        return parser.parse_args()
    
    def main():
        """Main function to run the migration"""
        args = parse_args()
        logger.info("Starting article embeddings migration")
        
        # Initialize migration
        migration = ArticleEmbeddingMigration(batch_size=args.batch_size)
        
        try:
            # Count articles
            only_missing = not args.all
            article_count = migration.count_articles(only_missing=only_missing)
            
            logger.info(f"Found {article_count} articles to process")
            
            if args.dry_run:
                logger.info("Dry run completed, no embeddings generated")
                return
            
            # Process articles
            if article_count > 0:
                start_time = datetime.now()
                success_count = migration.update_article_embeddings(
                    only_missing=only_missing,
                    limit=args.limit
                )
                end_time = datetime.now()
                
                # Calculate duration
                duration = (end_time - start_time).total_seconds()
                per_article = duration / success_count if success_count > 0 else 0
                
                logger.info(f"Migration completed in {duration:.2f} seconds")
                logger.info(f"Average time per article: {per_article:.2f} seconds")
            else:
                logger.info("No articles to process")
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
        finally:
            migration.close()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error("Make sure you've installed all required packages: sentence-transformers, pymongo, tqdm")
    sys.exit(1)