# Database utilities
import pymongo
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
    
    print("Created database indexes")

def initialize_database():
    """Initialize the database with required data"""
    create_indexes()
    create_sample_cs_modules()
