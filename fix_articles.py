# Save this as fix_articles.py
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/syllabuzz')
client = MongoClient(mongo_uri)
db = client.get_database()

def fix_article_ids():
    """Fix any articles with missing IDs"""
    print("Looking for articles with missing IDs...")
    
    # Find articles with problematic IDs
    problematic_articles = list(db.articles.find({
        "$or": [
            {"_id": {"$exists": False}},
            {"_id": None},
            {"_id": "undefined"},
            {"_id": "null"}
        ]
    }))
    
    print(f"Found {len(problematic_articles)} problematic articles")
    
    # Fix these articles
    fixed_count = 0
    for article in problematic_articles:
        # Check if we can use URL as unique identifier
        if 'url' in article:
            # See if there's another article with same URL but proper ID
            duplicate = db.articles.find_one({
                "_id": {"$type": "objectId"},
                "url": article['url']
            })
            
            if duplicate:
                # Delete this problematic article
                db.articles.delete_one({"_id": article['_id']})
                print(f"Deleted duplicate article: {article.get('title', 'No title')}")
            else:
                # Create a new ID for this article
                old_id = article['_id']
                article['_id'] = ObjectId()
                
                # Delete old article and insert fixed one
                db.articles.delete_one({"_id": old_id})
                db.articles.insert_one(article)
                fixed_count += 1
                print(f"Fixed article: {article.get('title', 'No title')}")
                
    print(f"Fixed {fixed_count} articles")
    
    # Ensure all bookmarks point to valid articles
    print("Checking bookmarks...")
    invalid_bookmarks = []
    
    for bookmark in db.bookmarks.find():
        article_id = bookmark.get('article_id')
        if not article_id or not db.articles.find_one({"_id": article_id}):
            invalid_bookmarks.append(bookmark['_id'])
    
    print(f"Found {len(invalid_bookmarks)} invalid bookmarks")
    
    if invalid_bookmarks:
        db.bookmarks.delete_many({"_id": {"$in": invalid_bookmarks}})
        print(f"Deleted {len(invalid_bookmarks)} invalid bookmarks")

if __name__ == "__main__":
    fix_article_ids()
    print("Done!")