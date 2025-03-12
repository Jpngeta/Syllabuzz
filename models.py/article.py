# models/article.py
"""
Article-related database functions for the CS Articles Recommender system.
"""

from datetime import datetime
from bson.objectid import ObjectId

# Import db connection
from db import db

def get_article(article_id):
    """Get an article by ID"""
    if isinstance(article_id, str):
        try:
            article_id = ObjectId(article_id)
        except:
            # If not a valid ObjectId, try as a string ID
            return db.articles.find_one({"_id": article_id})
    
    return db.articles.find_one({"_id": article_id})

def get_articles_by_category(category, page=1, page_size=20):
    """Get articles by category with pagination"""
    skip = (page - 1) * page_size
    
    if category and category != 'all':
        query = {"categories": category}
    else:
        query = {}
    
    articles = list(db.articles.find(query)
                   .sort("published_at", -1)
                   .skip(skip)
                   .limit(page_size))
    
    total = db.articles.count_documents(query)
    
    return {
        "articles": articles,
        "total_results": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

def search_articles(query, page=1, page_size=20):
    """Search articles by keyword"""
    skip = (page - 1) * page_size
    
    search_results = list(db.articles.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})])
     .skip(skip)
     .limit(page_size))
    
    total = db.articles.count_documents({"$text": {"$search": query}})
    
    return {
        "articles": search_results,
        "total_results": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

def get_similar_articles(article_id, limit=5):
    """Get articles similar to the given article"""
    article = get_article(article_id)
    if not article:
        return []
        
    # If article has embedding, use vector similarity
    if "vector_embedding" in article:
        # Use vector search if available
        try:
            pipeline = [
                {
                    "$search": {
                        "knnBeta": {
                            "vector": article["vector_embedding"],
                            "path": "vector_embedding",
                            "k": limit + 1
                        }
                    }
                },
                {"$match": {"_id": {"$ne": article["_id"]}}},
                {"$limit": limit}
            ]
            
            similar = list(db.articles.aggregate(pipeline))
            if similar:
                return similar
        except Exception as e:
            print(f"Vector search failed: {str(e)}")
    
    # Fallback to text similarity
    if "categories" in article and article["categories"]:
        categories = article["categories"]
        return list(db.articles.find(
            {
                "_id": {"$ne": article["_id"]},
                "categories": {"$in": categories}
            }
        ).sort("published_at", -1).limit(limit))
    
    # Final fallback to recent articles
    return list(db.articles.find(
        {"_id": {"$ne": article["_id"]}}
    ).sort("published_at", -1).limit(limit))

def record_article_view(article_id, user_id=None):
    """Record a view for an article"""
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)
    
    # Update article view count
    db.articles.update_one(
        {"_id": article_id},
        {"$inc": {"view_count": 1}}
    )
    
    # Record in reading history if user is logged in
    if user_id:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        db.reading_history.insert_one({
            "user_id": user_id,
            "article_id": article_id,
            "read_at": datetime.utcnow()
        })
        
    return True

def get_trending_articles(days=7, limit=10):
    """Get trending articles based on views and interactions"""
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get articles with most views in timeframe
    pipeline = [
        {
            "$match": {
                "published_at": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$sort": {"view_count": -1}
        },
        {
            "$limit": limit
        }
    ]
    
    trending = list(db.articles.aggregate(pipeline))
    
    # If not enough results, get most recent popular articles
    if len(trending) < limit:
        more_articles = list(db.articles.find()
                           .sort([("view_count", -1), ("published_at", -1)])
                           .limit(limit - len(trending)))
        trending.extend(more_articles)
    
    return trending[:limit]

def get_articles_with_embeddings(limit=100):
    """Get articles that have embeddings for recommendation"""
    return list(db.articles.find(
        {"vector_embedding": {"$exists": True}}
    ).limit(limit))

def get_articles_without_embeddings(limit=100):
    """Get articles that don't have embeddings yet"""
    return list(db.articles.find(
        {"vector_embedding": {"$exists": False}}
    ).limit(limit))

def update_article_embedding(article_id, embedding):
    """Update an article's embedding vector"""
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)
        
    result = db.articles.update_one(
        {"_id": article_id},
        {"$set": {
            "vector_embedding": embedding.tolist(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return result.modified_count > 0