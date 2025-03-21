# Updated embedding_service.py with improved historical article processing
import numpy as np
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer
from bson.objectid import ObjectId
from utils.db_utils import articles_collection, modules_collection, relevance_collection
from config import SBERT_MODEL_NAME, RELEVANCE_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name=SBERT_MODEL_NAME):
        """Initialize the embedding service with the specified model"""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Initialized embedding service with model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading SBERT model: {str(e)}")
            raise

    def generate_embedding(self, text):
        """Generate embedding vector for a given text"""
        if not text or not isinstance(text, str):
            return None
            
        try:
            # Generate embedding vector
            embedding = self.model.encode(text)
            return embedding.tolist()  # Convert numpy array to list for MongoDB storage
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def generate_module_embedding(self, module_id):
        """Generate embedding vector for a module based on description and keywords"""
        try:
            # Get module details
            module = modules_collection.find_one({"_id": ObjectId(module_id) if isinstance(module_id, str) else module_id})
            if not module:
                logger.error(f"Module not found: {module_id}")
                return None
                
            # Combine description and keywords
            text = module.get("description", "")
            keywords = module.get("keywords", [])
            
            if keywords:
                text += " " + " ".join(keywords)
                
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Update module with embedding
            modules_collection.update_one(
                {"_id": module["_id"]},
                {"$set": {"vector_embedding": embedding, "updated_at": datetime.now()}}
            )
            
            logger.info(f"Generated embedding for module: {module.get('name')}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating module embedding: {str(e)}")
            return None

    def generate_article_embedding(self, article_id):
        """Generate embedding vector for an article based on title, description, and content"""
        try:
            # Get article details
            article = articles_collection.find_one({"_id": ObjectId(article_id) if isinstance(article_id, str) else article_id})
            if not article:
                logger.error(f"Article not found: {article_id}")
                return None
                
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
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Update article with embedding
            articles_collection.update_one(
                {"_id": article["_id"]},
                {"$set": {"vector_embedding": embedding, "updated_at": datetime.now()}}
            )
            
            logger.info(f"Generated embedding for article: {article.get('title')}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating article embedding: {str(e)}")
            return None

    def calculate_similarity(self, embedding1, embedding2):
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

    def update_module_article_relevance(self, module_id, article_id):
        """Calculate and update relevance between a module and an article"""
        try:
            # Get module and article
            module = modules_collection.find_one({"_id": ObjectId(module_id) if isinstance(module_id, str) else module_id})
            article = articles_collection.find_one({"_id": ObjectId(article_id) if isinstance(article_id, str) else article_id})
            
            if not module or not article:
                logger.error(f"Module or article not found: {module_id}, {article_id}")
                return None
                
            # Get embeddings
            module_embedding = module.get("vector_embedding")
            article_embedding = article.get("vector_embedding")
            
            # Generate embeddings if not available
            if not module_embedding:
                module_embedding = self.generate_module_embedding(module_id)
                
            if not article_embedding:
                article_embedding = self.generate_article_embedding(article_id)
                
            if not module_embedding or not article_embedding:
                logger.warning(f"Could not generate embeddings for module-article: {module_id}, {article_id}")
                return None
                
            # Calculate similarity
            relevance_score = self.calculate_similarity(module_embedding, article_embedding)
            
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
            
            logger.info(f"Updated relevance for module-article: {module.get('name')}, {article.get('title')}, score: {relevance_score:.4f}")
            return relevance_score
        except Exception as e:
            logger.error(f"Error updating module-article relevance: {str(e)}")
            return None

    def update_all_module_embeddings(self):
        """Update embeddings for all modules"""
        try:
            modules = modules_collection.find({})
            for module in modules:
                self.generate_module_embedding(module["_id"])
            logger.info("Updated all module embeddings")
        except Exception as e:
            logger.error(f"Error updating all module embeddings: {str(e)}")

    def update_recent_article_embeddings(self, days=7):
        """Update embeddings for articles from the last X days and articles without embeddings"""
        try:
            # Find articles that need embeddings: either recent or missing embeddings
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = {
                "$or": [
                    {"vector_embedding": None},  # Articles missing embeddings
                    {"updated_at": {"$lt": cutoff_date}}  # Articles with old embeddings
                ]
            }
            
            # Increase limit from 100 to 500 to process more at once
            articles = articles_collection.find(query).limit(500)
            
            count = 0
            for article in articles:
                self.generate_article_embedding(article["_id"])
                count += 1
                
            logger.info(f"Updated embeddings for {count} articles")
        except Exception as e:
            logger.error(f"Error updating article embeddings: {str(e)}")

    def update_relevance_scores(self):
        """Update relevance scores for module-article pairs with improved historical coverage"""
        try:
            # Get all modules with embeddings
            modules = list(modules_collection.find({"vector_embedding": {"$ne": None}}))
            
            # Increase from 100 to 500 articles, and include any that don't have relevance scores yet
            # Sort oldest first to ensure historical articles get processed
            recent_articles_pipeline = [
                {"$match": {"vector_embedding": {"$ne": None}}},
                {"$sort": {"published_at": 1}},  # Process oldest first 
                {"$limit": 250}
            ]
            
            recent_articles = list(articles_collection.aggregate(recent_articles_pipeline))
            
            # Also get articles that have no relevance scores at all
            missing_relevance_pipeline = [
                {"$match": {"vector_embedding": {"$ne": None}}},
                {"$lookup": {
                    "from": "module_article_relevance",
                    "localField": "_id",
                    "foreignField": "article_id",
                    "as": "relevance"
                }},
                {"$match": {"relevance": {"$size": 0}}},
                {"$limit": 250}
            ]
            
            missing_relevance_articles = list(articles_collection.aggregate(missing_relevance_pipeline))
            
            # Combine both sets of articles, removing duplicates
            processed_ids = set()
            combined_articles = []
            
            for article in recent_articles + missing_relevance_articles:
                if str(article["_id"]) not in processed_ids:
                    combined_articles.append(article)
                    processed_ids.add(str(article["_id"]))
            
            count = 0
            for module in modules:
                for article in combined_articles:
                    self.update_module_article_relevance(module["_id"], article["_id"])
                    count += 1
                    
            logger.info(f"Updated {count} module-article relevance scores")
        except Exception as e:
            logger.error(f"Error updating relevance scores: {str(e)}")

    def get_module_recommendations(self, module_id, limit=10):
        """Get article recommendations for a specific module"""
        try:
            # Validate module exists
            module = modules_collection.find_one({"_id": ObjectId(module_id) if isinstance(module_id, str) else module_id})
            if not module:
                logger.error(f"Module not found: {module_id}")
                return []
                
            # Get articles with high relevance to this module, increasing limit to get more quality content
            relevance_docs = relevance_collection.find({
                "module_id": module["_id"],
                "relevance_score": {"$gte": RELEVANCE_THRESHOLD}
            }).sort("relevance_score", -1).limit(limit * 2)  # Get more for filtering
            
            # Get article details
            recommendations = []
            for rel in relevance_docs:
                article = articles_collection.find_one({"_id": rel["article_id"]})
                if article:
                    # Add relevance score to article
                    article["relevance_score"] = rel["relevance_score"]
                    recommendations.append(article)
            
            # Sort by relevance score and take top results
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            logger.info(f"Found {len(recommendations[:limit])} recommendations for module: {module.get('name')}")
            return recommendations[:limit]
        except Exception as e:
            logger.error(f"Error getting module recommendations: {str(e)}")
            return []