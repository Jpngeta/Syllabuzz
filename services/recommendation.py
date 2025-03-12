from bson.objectid import ObjectId
import numpy as np
from services.embedding_service import EmbeddingService

class RecommendationEngine:
    def __init__(self, db, embedding_service=None):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        
    def get_module_recommendations(self, module_id, limit=10):
        """Get article recommendations for a specific module"""
        # Get module
        module = self.db.modules.find_one({'_id': ObjectId(module_id)})
        if not module:
            return []
            
        # Generate module embedding if not already computed
        if 'vector_embedding' not in module:
            module_embedding = self.embedding_service.get_module_embedding(module)
            self.db.modules.update_one(
                {'_id': module['_id']},
                {'$set': {'vector_embedding': module_embedding.tolist()}}
            )
        else:
            module_embedding = np.array(module['vector_embedding'])
            
        # Find articles with similar embeddings
        pipeline = [
            {
                '$search': {
                    'index': 'vector_index',
                    'knnBeta': {
                        'vector': module_embedding.tolist(),
                        'path': 'vector_embedding',
                        'k': limit * 2  # Get more than needed to filter
                    }
                }
            },
            {
                '$project': {
                    'title': 1,
                    'summary': 1,
                    'url': 1,
                    'source': 1,
                    'image_url': 1,
                    'published_date': 1,
                    'categories': 1,
                    'score': {'$meta': 'searchScore'}
                }
            },
            {'$limit': limit}
        ]
        
        recommendations = list(self.db.articles.aggregate(pipeline))
        return recommendations
        
    def get_user_recommendations(self, user_id, limit=20):
        """Get personalized recommendations for a user based on their modules"""
        # Get user
        user = self.db.users.find_one({'_id': ObjectId(user_id)})
        if not user or 'modules' not in user:
            return []
            
        # Get recommendations for each module
        all_recommendations = []
        module_weights = {}
        
        # Get user's reading history for personalization
        history = list(self.db.interactions.find({
            'user_id': ObjectId(user_id),
            'interaction_type': 'view'
        }).sort('created_at', -1).limit(50))
        
        history_articles = set(str(h['article_id']) for h in history)
        
        # Calculate module weights based on user interaction
        for module_id in user['modules']:
            # Default weight
            module_weights[str(module_id)] = 1.0
            
            # Increase weight for modules with more interactions
            module_interactions = self.db.interactions.count_documents({
                'user_id': ObjectId(user_id),
                'module_id': ObjectId(module_id)
            })
            
            if module_interactions > 0:
                module_weights[str(module_id)] += min(module_interactions / 10, 1.0)
        
        # Get recommendations for each module
        for module_id in user['modules']:
            module_recs = self.get_module_recommendations(module_id, limit=limit//len(user['modules']))
            
            # Apply module weight to each recommendation
            for rec in module_recs:
                rec['module_id'] = module_id
                rec['weight'] = module_weights[str(module_id)]
                
                # Don't include already read articles
                if str(rec['_id']) not in history_articles:
                    all_recommendations.append(rec)
        
        # Sort by weighted score and take top limit
        all_recommendations.sort(key=lambda x: x['score'] * x['weight'], reverse=True)
        return all_recommendations[:limit]
        
    def update_article_embeddings(self, batch_size=100):
        """Update embeddings for articles that don't have them"""
        # Get articles without embeddings
        articles = list(self.db.articles.find(
            {'vector_embedding': {'$exists': False}}).limit(batch_size))
            
        if not articles:
            return 0
            
        # Prepare texts for batch processing
        texts = [article['title'] + '. ' + article.get('content', '') for article in articles]
        
        # Generate embeddings
        embeddings = self.embedding_service.generate_embeddings(texts)
        
        # Update articles with embeddings
        for i, article in enumerate(articles):
            self.db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {'vector_embedding': embeddings[i].tolist()}}
            )
            
        return len(articles)