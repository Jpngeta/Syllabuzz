# db_utils.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB 
# (You can import your existing db instance from db.py if you prefer)
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/syllabuzz'))
db = client.get_database()

def setup_recommendation_indexes():
    """Set up indexes for recommendation functionality"""
    # Text search index for articles (if not already created)
    if 'text_search' not in [idx.get('name') for idx in list(db.articles.list_indexes())]:
        db.articles.create_index([
            ('title', 'text'), 
            ('content', 'text'),
            ('description', 'text')
        ], 
        name='text_search',
        weights={
            'title': 10,
            'description': 5, 
            'content': 1
        })
    
    # Module keyword index
    db.modules.create_index('keywords')
    
    # User-module relationship index
    db.users.create_index('modules')
    
    # Interaction index for recommendation personalization
    db.interactions.create_index([('user_id', 1), ('created_at', -1)])
    db.interactions.create_index([('user_id', 1), ('article_id', 1)])
    db.interactions.create_index([('user_id', 1), ('module_id', 1)])
    
    # Set up vector index if using MongoDB Atlas
    # (Only needed if you're using MongoDB Atlas with Vector Search capability)
    try:
        db.command({
            "createIndexes": "articles",
            "indexes": [{
                "key": {"vector_embedding": "hnsw"},
                "name": "vector_index",
                "params": {
                    "dimensions": 384,  # Dimensions for Sentence-BERT embeddings
                    "metric": "cosine"
                }
            }]
        })
        print("Vector search index created successfully")
    except Exception as e:
        print(f"Note: Could not create vector index: {str(e)}")
        print("This is normal if you're not using MongoDB Atlas with vector search capability")
        print("The application will fall back to alternative similarity methods")

def get_module_articles(module_id, limit=10):
    """Get articles related to a specific module"""
    # Get the module to extract keywords
    module = db.modules.find_one({'_id': module_id})
    if not module or 'keywords' not in module:
        return []
    
    # Use text search with module keywords
    keyword_query = ' '.join(module['keywords'])
    articles = list(db.articles.find(
        {'$text': {'$search': keyword_query}},
        {'score': {'$meta': 'textScore'}}
    ).sort([('score', {'$meta': 'textScore'})]).limit(limit))
    
    return articles

def record_article_interaction(user_id, article_id, interaction_type, module_id=None, metadata=None):
    """Record user interaction with an article"""
    interaction = {
        'user_id': user_id,
        'article_id': article_id,
        'interaction_type': interaction_type,
        'created_at': datetime.now(),
        'metadata': metadata or {}
    }
    
    if module_id:
        interaction['module_id'] = module_id
        
    return db.interactions.insert_one(interaction).inserted_id