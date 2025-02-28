from db import db
from bson import ObjectId
import json
from datetime import datetime

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def check_articles():
    """Check if articles exist in the database and print some information"""
    print("Checking articles in database...")
    
    # Count articles by category
    categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology', 'all']
    
    for category in categories:
        query = {}
        if category != 'all':
            query = {'categories': category}
            
        count = db.articles.count_documents(query)
        print(f"Category '{category}': {count} articles")
    
    # Sample a few articles
    print("\nSample articles:")
    sample_articles = list(db.articles.find().limit(3))
    
    for i, article in enumerate(sample_articles):
        print(f"\nArticle {i+1}:")
        print(f"  Title: {article.get('title')}")
        print(f"  Categories: {article.get('categories')}")
        print(f"  Source: {article.get('source_name')}")
        print(f"  Image URL available: {'Yes' if article.get('image_url') else 'No'}")
        print(f"  Description length: {len(article.get('description', '')) if article.get('description') else 0} chars")
    
    # Detailed dump of one article (for structure inspection)
    print("\nDetailed structure of first article:")
    if sample_articles:
        print(json.dumps(sample_articles[0], indent=2, cls=JSONEncoder))
    else:
        print("No articles found for detailed inspection")

if __name__ == "__main__":
    check_articles()