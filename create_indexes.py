from db import db

def create_indexes():
    """Create necessary indexes for the application"""
    print("Creating database indexes...")
    
    # Text search index for articles
    db.articles.create_index([
        ("title", "text"), 
        ("description", "text"), 
        ("content", "text")
    ], 
    name="articles_text_search",
    weights={
        "title": 10,
        "description": 5,
        "content": 1
    })
    
    # Indexes for fast lookups
    db.articles.create_index("categories")
    db.articles.create_index("published_at")
    db.articles.create_index("url", unique=True)
    
    # Bookmark indexes
    db.bookmarks.create_index([("user_id", 1), ("article_id", 1)], unique=True)
    
    print("Database indexes created successfully!")

if __name__ == "__main__":
    create_indexes()