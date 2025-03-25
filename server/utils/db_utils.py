# Database utilities with user authentication
import pymongo
from bson.objectid import ObjectId  # Add this import
from datetime import datetime
from config import MONGO_URI, MONGO_DB_NAME

# Create MongoDB connection
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Create collections
articles_collection = db.articles
modules_collection = db.modules
relevance_collection = db.module_article_relevance
users_collection = db.users
bookmarks_collection = db.bookmarks
interactions_collection = db.interactions
tokens_collection = db.tokens

def create_sample_cs_modules():
    """Create some sample CS modules if none exist"""
    if modules_collection.count_documents({}) == 0:
        print("Creating sample CS modules...")
        
        modules = [
            {
                "name": "Data Structures and Algorithms",
                "code": "COMP 210",
                "description": "A study of fundamental data structures and algorithms including lists, stacks, queues, trees, graphs, sorting and searching.",
                "keywords": ["algorithms", "data structures", "sorting", "searching", "complexity analysis", "trees", "graphs"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "vector_embedding": None  # Will be populated by embedding service
            },
            {
                "name": "Mobile Computing",
                "code": "COMP 340",
                "description": "Design and implementation of mobile applications, focusing on user interface, sensing, and system performance.",
                "keywords": ["mobile development", "android", "ios", "responsive design", "mobile ui", "app development"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "vector_embedding": None
            },
            {
                "name": "Distributed Systems",
                "code": "COMP 325",
                "description": "Key concepts in distributed systems including communication, coordination, consensus, replication, and fault tolerance.",
                "keywords": ["distributed computing", "cloud computing", "consensus algorithms", "fault tolerance", "replication", "distributed databases"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "vector_embedding": None
            },
            {
                "name": "Machine Learning",
                "code": "COMP 410",
                "description": "Fundamentals of machine learning including supervised and unsupervised learning, classification, regression, clustering, and neural networks.",
                "keywords": ["machine learning", "neural networks", "deep learning", "AI", "data mining", "classification", "clustering"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "vector_embedding": None
            },
            {
                "name": "Computer Networks",
                "code": "COMP 315",
                "description": "Concepts and technologies of computer networks, including network protocols, Internet architecture, socket programming, and network security.",
                "keywords": ["networking", "TCP/IP", "protocols", "Internet", "socket programming", "routing", "network security"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "vector_embedding": None
            }
        ]
        
        modules_collection.insert_many(modules)
        print(f"Created {len(modules)} sample modules")

def create_indexes():
    """Create necessary database indexes"""
    # Article indexes
    articles_collection.create_index([("url", pymongo.ASCENDING)], unique=True)
    articles_collection.create_index([("title", pymongo.TEXT), ("content", pymongo.TEXT), ("description", pymongo.TEXT)])
    articles_collection.create_index([("published_at", pymongo.DESCENDING)])
    articles_collection.create_index([("categories", pymongo.ASCENDING)])
    
    # Module indexes
    modules_collection.create_index([("code", pymongo.ASCENDING)], unique=True)
    
    # Relevance indexes
    relevance_collection.create_index([
        ("module_id", pymongo.ASCENDING), 
        ("article_id", pymongo.ASCENDING)
    ], unique=True)
    relevance_collection.create_index([("relevance_score", pymongo.DESCENDING)])
    
    # Interaction indexes
    interactions_collection.create_index([
        ("user_id", pymongo.ASCENDING),
        ("article_id", pymongo.ASCENDING),
        ("module_id", pymongo.ASCENDING)
    ])
    
    # User indexes
    users_collection.create_index([("email", pymongo.ASCENDING)], unique=True)
    users_collection.create_index([("username", pymongo.ASCENDING)], unique=True)
    
    # Token indexes
    tokens_collection.create_index([("token", pymongo.ASCENDING)], unique=True)
    tokens_collection.create_index([("expires_at", pymongo.ASCENDING)])
    tokens_collection.create_index([("user_id", pymongo.ASCENDING)])
    
    # Bookmark indexes
    bookmarks_collection.create_index([
        ("user_id", pymongo.ASCENDING),
        ("article_id", pymongo.ASCENDING)
    ], unique=True)
    
    print("Created database indexes")

def find_user_by_email(email):
    """Find a user by email"""
    return users_collection.find_one({"email": email})

def find_user_by_username(username):
    """Find a user by username"""
    return users_collection.find_one({"username": username})

def find_user_by_id(user_id):
    """Find a user by ID"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
    return users_collection.find_one({"_id": user_id})

def create_user(username, email, password_hash):
    """Create a new user"""
    user = {
        "username": username,
        "email": email,
        "password": password_hash,
        "is_verified": False,
        "modules": [],
        "preferences": {
            "newsletter": True,
            "email_notifications": True
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = users_collection.insert_one(user)
    return result.inserted_id

def verify_user(user_id):
    """Mark a user as verified"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "is_verified": True,
                "updated_at": datetime.now()
            }
        }
    )
    
    return result.modified_count > 0

def update_user_password(user_id, password_hash):
    """Update a user's password"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "password": password_hash,
                "updated_at": datetime.now()
            }
        }
    )
    
    return result.modified_count > 0

def create_token(user_id, token_type, token, expires_at):
    """Create a new token (verification, password reset, etc.)"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    token_doc = {
        "user_id": user_id,
        "token": token,
        "type": token_type,
        "created_at": datetime.now(),
        "expires_at": expires_at,
        "used": False
    }
    
    result = tokens_collection.insert_one(token_doc)
    return result.inserted_id

def find_token(token, token_type=None):
    """Find a token by its value and optionally type"""
    query = {"token": token}
    
    if token_type:
        query["type"] = token_type
        
    return tokens_collection.find_one(query)

def mark_token_used(token_id):
    """Mark a token as used"""
    if isinstance(token_id, str):
        token_id = ObjectId(token_id)  # Changed from pymongo.ObjectId to ObjectId
        
    result = tokens_collection.update_one(
        {"_id": token_id},
        {"$set": {"used": True}}
    )
    
    return result.modified_count > 0

def update_user_modules(user_id, modules):
    """Update a user's enrolled modules"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    # Convert module IDs to ObjectId if they're strings
    module_ids = []
    for module_id in modules:
        if isinstance(module_id, str):
            module_ids.append(ObjectId(module_id))  # Changed from pymongo.ObjectId to ObjectId
        else:
            module_ids.append(module_id)
    
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "modules": module_ids,
                "updated_at": datetime.now()
            }
        }
    )
    
    return result.modified_count > 0

def update_user_preferences(user_id, preferences):
    """Update a user's preferences"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "preferences": preferences,
                "updated_at": datetime.now()
            }
        }
    )
    
    return result.modified_count > 0

def bookmark_article(user_id, article_id, module_id=None):
    """Add an article to user's bookmarks"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)  # Changed from pymongo.ObjectId to ObjectId
        
    if module_id and isinstance(module_id, str):
        module_id = ObjectId(module_id)  # Changed from pymongo.ObjectId to ObjectId
    
    bookmark = {
        "user_id": user_id,
        "article_id": article_id,
        "created_at": datetime.now()
    }
    
    if module_id:
        bookmark["module_id"] = module_id
    
    try:
        result = bookmarks_collection.insert_one(bookmark)
        return result.inserted_id
    except pymongo.errors.DuplicateKeyError:
        # Already bookmarked
        return None

def remove_bookmark(user_id, article_id):
    """Remove an article from user's bookmarks"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)  # Changed from pymongo.ObjectId to ObjectId
    
    result = bookmarks_collection.delete_one({
        "user_id": user_id,
        "article_id": article_id
    })
    
    return result.deleted_count > 0

def get_user_bookmarks(user_id, limit=20, skip=0):
    """Get bookmarks for a user"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$lookup": {
            "from": "articles",
            "localField": "article_id",
            "foreignField": "_id",
            "as": "article"
        }},
        {"$unwind": "$article"},
        {"$project": {
            "bookmark_id": "$_id",
            "article": "$article",
            "created_at": 1
        }}
    ]
    
    bookmarks = list(bookmarks_collection.aggregate(pipeline))
    
    # Convert ObjectIds to strings for JSON serialization
    for bookmark in bookmarks:
        bookmark["article"]["_id"] = str(bookmark["article"]["_id"])
        bookmark["bookmark_id"] = str(bookmark["bookmark_id"])
    
    return bookmarks

def is_article_bookmarked(user_id, article_id):
    """Check if an article is bookmarked by a user"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)  # Changed from pymongo.ObjectId to ObjectId
        
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)  # Changed from pymongo.ObjectId to ObjectId
    
    bookmark = bookmarks_collection.find_one({
        "user_id": user_id,
        "article_id": article_id
    })
    
    return bookmark is not None

def initialize_database():
    """Initialize the database with required data"""
    create_indexes()
    create_sample_cs_modules()