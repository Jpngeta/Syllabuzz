# Recommendation engine
import logging
from datetime import datetime
from bson.objectid import ObjectId
from utils.db_utils import articles_collection, modules_collection, relevance_collection, interactions_collection
from config import RELEVANCE_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, embedding_service):
        """Initialize the recommendation service with the embedding service"""
        self.embedding_service = embedding_service
        logger.info("Initialized recommendation service")

    def get_module_recommendations(self, module_id, limit=20):
    #Get combined article and paper recommendations for a specific module
        try:
            # Ensure module_id is ObjectId
            if isinstance(module_id, str):
                module_id = ObjectId(module_id)
                    
            # Get module details
            module = modules_collection.find_one({"_id": module_id})
            if not module:
                logger.error(f"Module not found: {module_id}")
                return []
                    
            # Get articles/papers with high relevance scores for this module
            relevance_docs = relevance_collection.find({
                "module_id": module_id,
                "relevance_score": {"$gte": RELEVANCE_THRESHOLD}
            }).sort("relevance_score", -1).limit(limit * 2)  # Get more to ensure mix of types
                
            # Retrieve articles/papers with their relevance scores
            recommendations = []
            for rel in relevance_docs:
                article = articles_collection.find_one({"_id": rel["article_id"]})
                if article:
                    # Add relevance score to article
                    article["relevance_score"] = rel["relevance_score"]
                    # Add type field
                    if article.get("source_name") == "arXiv":
                        article["type"] = "academic"
                    else:
                        article["type"] = "news"
                    # Convert ObjectId to string for JSON serialization
                    article["_id"] = str(article["_id"])
                    recommendations.append(article)
            
            # Sort by relevance score and take top results           
            recommendations = sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
            logger.info(f"Found {len(recommendations)} combined recommendations for module: {module.get('name')}")
            return recommendations
        except Exception as e:
            logger.error(f"Error getting module recommendations: {str(e)}")
            return []

    def get_user_recommendations(self, user_id, limit=20):
        """Get personalized recommendations for a user based on enrolled modules"""
        try:
            # Get user details and enrolled modules
            from utils.db_utils import users_collection
            user = users_collection.find_one({"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id})
            
            if not user or not user.get("modules"):
                logger.error(f"User not found or has no enrolled modules: {user_id}")
                return []
                    
            # Get recommendations for each module the user is enrolled in
            all_recommendations = []
            for module_id in user.get("modules", []):
                module_recs = self.get_module_recommendations(module_id, limit=10)
                for rec in module_recs:
                    rec["module_id"] = str(module_id)  # Mark which module this recommendation is for
                    all_recommendations.append(rec)
                        
            # Deduplicate recommendations (an article may be relevant to multiple modules)
            seen_articles = set()
            unique_recommendations = []
            
            for article in all_recommendations:
                if article["_id"] not in seen_articles:
                    seen_articles.add(article["_id"])
                    unique_recommendations.append(article)
                        
            # Sort by relevance score
            sorted_recommendations = sorted(
                unique_recommendations, 
                key=lambda x: x.get("relevance_score", 0), 
                reverse=True
            )
            
            # Take top N recommendations
            top_recommendations = sorted_recommendations[:limit]
            
            logger.info(f"Found {len(top_recommendations)} personalized recommendations for user: {user_id}")
            return top_recommendations
        except Exception as e:
            logger.error(f"Error getting user recommendations: {str(e)}")
            return []


    def record_interaction(self, user_id, article_id, module_id=None, interaction_type="view"):
        """Record user interaction with an article"""
        try:
            # Ensure IDs are ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            if isinstance(article_id, str):
                article_id = ObjectId(article_id)
                
            if module_id and isinstance(module_id, str):
                module_id = ObjectId(module_id)
                
            # Create interaction document
            interaction = {
                "user_id": user_id,
                "article_id": article_id,
                "type": interaction_type,
                "created_at": datetime.now(),
                "metadata": {}
            }
            
            # Add module context if provided
            if module_id:
                interaction["module_id"] = module_id
                
            # Insert interaction record
            interactions_collection.insert_one(interaction)
            
            logger.info(f"Recorded {interaction_type} interaction for user {user_id}, article {article_id}")
            return True
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            return False

    def get_trending_articles(self, days=7, limit=10):
        """Get trending content (articles and papers) based on recent interactions"""
        try:
            # Calculate date threshold
            from datetime import datetime, timedelta
            threshold_date = datetime.now() - timedelta(days=days)
            
            # Get interaction counts for articles/papers
            pipeline = [
                {"$match": {"created_at": {"$gte": threshold_date}}},
                {"$group": {
                    "_id": "$article_id",
                    "interaction_count": {"$sum": 1}
                }},
                {"$sort": {"interaction_count": -1}},
                {"$limit": limit * 2}  # Get more to ensure mix of types
            ]
            
            trending_items = list(interactions_collection.aggregate(pipeline))
            
            # Get article details
            results = []
            for item in trending_items:
                article = articles_collection.find_one({"_id": item["_id"]})
                if article:
                    article["interaction_count"] = item["interaction_count"]
                    article["_id"] = str(article["_id"])  # Convert ObjectId to string
                    # Add type field
                    if article.get("source_name") == "arXiv":
                        article["type"] = "academic"
                    else:
                        article["type"] = "news"
                    results.append(article)
            
            # Sort by interaction count and limit results
            results = sorted(results, key=lambda x: x.get("interaction_count", 0), reverse=True)[:limit]
                        
            logger.info(f"Found {len(results)} trending items")
            return results
        except Exception as e:
            logger.error(f"Error getting trending items: {str(e)}")
            return []

    def get_recommendations_by_keyword(self, keyword, limit=10):
        """Get recommendations based on a keyword search"""
        try:
            # Search articles by keyword
            articles = articles_collection.find({
                "$text": {"$search": keyword}
            }).limit(limit)
            
            results = []
            for article in articles:
                article["_id"] = str(article["_id"])  # Convert ObjectId to string
                results.append(article)
                
            logger.info(f"Found {len(results)} articles matching keyword: {keyword}")
            return results
        except Exception as e:
            logger.error(f"Error getting recommendations by keyword: {str(e)}")
            return []