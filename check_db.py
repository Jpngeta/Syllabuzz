import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Get MongoDB connection string from environment or use default
mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/syllabuzz')
client = MongoClient(mongo_uri)
db = client.get_database()

def check_database():
    """Check the database collections and contents"""
    
    # Check articles collection
    article_count = db.articles.count_documents({})
    print(f"Articles in database: {article_count}")
    
    # Show some article samples if available
    if article_count > 0:
        print("\nSample Articles:")
        for article in db.articles.find().limit(3):
            print(f"  ID: {article.get('_id')}")
            print(f"  Title: {article.get('title')}")
            print(f"  Source: {article.get('source_name')}")
            print(f"  URL: {article.get('url')}")
            print(f"  Categories: {article.get('categories', [])}")
            print("  ---")
    
    # Check users collection
    user_count = db.users.count_documents({})
    print(f"\nUsers in database: {user_count}")
    
    # Check bookmarks collection
    bookmark_count = db.bookmarks.count_documents({})
    print(f"\nBookmarks in database: {bookmark_count}")

if __name__ == "__main__":
    print("Checking database collections...\n")
    check_database()
    print("\nDone.")