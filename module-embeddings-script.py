#!/usr/bin/env python3
"""
Script to add vector embeddings to modules using the application's EmbeddingService.

This script leverages the existing application's EmbeddingService to generate
and update vector embeddings for all CS modules in the database.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('add_embeddings')

# Add project root to Python path (adjust if needed)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

try:
    # Import application components
    from services.embedding_service import EmbeddingService
    from config import SBERT_MODEL_NAME
    from utils.db_utils import modules_collection
    
    def update_module_embeddings():
        """Update embeddings for all modules using the application's EmbeddingService"""
        try:
            # Initialize the embedding service
            logger.info(f"Initializing embedding service with model: {SBERT_MODEL_NAME}")
            embedding_service = EmbeddingService(model_name=SBERT_MODEL_NAME)
            
            # Get all modules without embeddings (or all modules if you want to refresh all)
            # modules = list(modules_collection.find({"vector_embedding": None}))
            modules = list(modules_collection.find({}))
            
            logger.info(f"Found {len(modules)} modules to process")
            
            # Update embeddings for each module
            for i, module in enumerate(modules):
                module_name = module.get('name', f"ID: {module['_id']}")
                
                try:
                    logger.info(f"[{i+1}/{len(modules)}] Generating embedding for {module_name}")
                    embedding = embedding_service.generate_module_embedding(module['_id'])
                    
                    if embedding:
                        logger.info(f"Successfully generated embedding for {module_name}")
                    else:
                        logger.warning(f"Failed to generate embedding for {module_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing module {module_name}: {str(e)}")
            
            # Verify results
            modules_with_embeddings = modules_collection.count_documents({"vector_embedding": {"$ne": None}})
            modules_without_embeddings = modules_collection.count_documents({"vector_embedding": None})
            
            logger.info(f"Migration completed:")
            logger.info(f"Modules with embeddings: {modules_with_embeddings}")
            logger.info(f"Modules without embeddings: {modules_without_embeddings}")
            
            return modules_with_embeddings
        
        except Exception as e:
            logger.error(f"Error updating module embeddings: {str(e)}")
            return 0
    
    if __name__ == "__main__":
        logger.info("Starting module embeddings update")
        count = update_module_embeddings()
        logger.info(f"Process completed. Updated {count} modules.")
        
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error("Make sure you're running this script from the project root or the correct Python environment")
    sys.exit(1)
