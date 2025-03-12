# models/user.py
"""
User-related database functions for the CS Articles Recommender system.
"""

from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# Import your existing db connection
from db import db

def get_user(user_id):
    """Get a user by ID"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.find_one({"_id": user_id})

def get_user_by_email(email):
    """Get a user by email"""
    return db.users.find_one({"email": email})

def update_user(user_id, updates):
    """Update user data"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    # Don't allow direct updates to password
    if "password" in updates:
        del updates["password"]
        
    # Add updated_at timestamp
    updates["updated_at"] = datetime.utcnow()
    
    result = db.users.update_one(
        {"_id": user_id},
        {"$set": updates}
    )
    
    return result.modified_count > 0

def update_user_password(user_id, new_password):
    """Update a user's password"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
        
    hashed_password = generate_password_hash(new_password)
    
    result = db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "password": hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return result.modified_count > 0

def get_user_modules(user_id):
    """Get a user's enrolled modules"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
        
    user = db.users.find_one({"_id": user_id}, {"modules": 1})
    if not user or "modules" not in user:
        return []
        
    # Get full module data
    module_ids = user["modules"]
    modules = list(db.modules.find({"_id": {"$in": module_ids}}))
    
    return modules

def enroll_module(user_id, module_id):
    """Enroll a user in a module"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    if isinstance(module_id, str):
        module_id = ObjectId(module_id)
        
    result = db.users.update_one(
        {"_id": user_id},
        {"$addToSet": {"modules": module_id}}
    )
    
    return result.modified_count > 0

def unenroll_module(user_id, module_id):
    """Unenroll a user from a module"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    if isinstance(module_id, str):
        module_id = ObjectId(module_id)
        
    result = db.users.update_one(
        {"_id": user_id},
        {"$pull": {"modules": module_id}}
    )
    
    return result.modified_count > 0

def get_user_reading_history(user_id, limit=20):
    """Get a user's reading history"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
        
    # Get reading history records
    history = list(db.reading_history.find(
        {"user_id": user_id}
    ).sort("read_at", -1).limit(limit))
    
    # Get article data for each history item
    article_ids = [h["article_id"] for h in history]
    articles = {
        str(a["_id"]): a for a in db.articles.find({"_id": {"$in": article_ids}})
    }
    
    # Add article data to history items
    for item in history:
        article_id = str(item["article_id"])
        if article_id in articles:
            item["article"] = articles[article_id]
            
    return history

def get_user_interactions(user_id, limit=50):
    """Get a user's interactions for recommendation purposes"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
        
    return list(db.interactions.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit))

def record_user_interaction(user_id, article_id, interaction_type, module_id=None, metadata=None):
    """Record a user's interaction with an article"""
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    if isinstance(article_id, str):
        article_id = ObjectId(article_id)
    if module_id and isinstance(module_id, str):
        module_id = ObjectId(module_id)
        
    interaction = {
        "user_id": user_id,
        "article_id": article_id,
        "interaction_type": interaction_type,
        "created_at": datetime.utcnow(),
        "metadata": metadata or {}
    }
    
    if module_id:
        interaction["module_id"] = module_id
        
    result = db.interactions.insert_one(interaction)
    return result.inserted_id