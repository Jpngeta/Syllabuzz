from datetime import datetime, timedelta
from bson.objectid import ObjectId
import hashlib
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from dotenv import load_dotenv
# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["Syllabuzz"]
users_collection = db["users"]
reset_tokens_collection = db["reset_tokens"]
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.ERROR)

"""
This file describes the MongoDB data models for the Tech News application.
While MongoDB is schemaless, this serves as a reference for the expected structure.
"""

"""
User Model Schema:
{
    "_id": ObjectId,
    "username": String,
    "email": String,
    "password": String (hashed),
    "profile_pic": String (URL),
    "bio": String,
    "created_at": DateTime,
    "last_login": DateTime,
    "topics": [String],
    "following": [ObjectId],
    "followers": [ObjectId],
    "settings": {
        "article_count": Integer,
        "theme": String,
        "email_notifications": Boolean,
        "notification_frequency": String,
        "content_filter": String
    },
    "subscription_tier": String,
    "subscription_expires": DateTime
}
"""

def create_user(username, email, password):
    """Create a new user with default settings"""
    try:
        if users_collection.find_one({"email": email}):
            return False
        
        hashed_password = generate_password_hash(password)
        
        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "profile_pic": None,
            "bio": "",
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "topics": [],
            "following": [],
            "followers": [],
            "settings": {
                "article_count": 20,
                "theme": "light",
                "email_notifications": False,
                "notification_frequency": "daily",
                "content_filter": "balanced"
            },
            "subscription_tier": "free",
            "subscription_expires": None
        }
        users_collection.insert_one(user)
        return True
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return False

def find_user_by_email(email):
    """Find a user by email"""
    try:
        user_data = users_collection.find_one({"email": email})
        return bool(user_data), user_data
    except Exception as e:
        logging.error(f"Error finding user: {e}")
        return False, None

def verify_password(user, password):
    """Verify user password."""
    if not user or 'password' not in user:
        return False
        
    # Make sure the stored password is in hash format
    stored_password = user['password']
    
    # Debug information
    print(f"Checking password for {user.get('email')}")
    
    try:
        # Check if the password is valid
        is_valid = check_password_hash(stored_password, password)
        print(f"Password verification result: {is_valid}")
        return is_valid
    except Exception as e:
        print(f"Error verifying password: {e}")
        # If there's an error in verification, default to not authenticated
        return False
    
def update_user_password(email, new_password):
    """Update a user's password"""
    try:
        password_hash = generate_password_hash(new_password)
        result = users_collection.update_one(
            {"email": email},
            {"$set": {
                "password": password_hash,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    except Exception as e:
        logging.error(f"Error updating password: {e}")
        return False

def create_reset_token(email, token):
    """Create a password reset token"""
    try:
        reset_tokens_collection.delete_many({"email": email})
        reset_token = {
            "email": email,
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        reset_tokens_collection.insert_one(reset_token)
        return True
    except Exception as e:
        logging.error(f"Error creating reset token: {e}")
        return False

def find_reset_token(token):
    """Find a valid reset token"""
    try:
        return reset_tokens_collection.find_one({
            "token": token,
            "expires_at": {"$gt": datetime.utcnow()}
        })
    except Exception as e:
        logging.error(f"Error finding reset token: {e}")
        return None

def delete_reset_token(token):
    """Delete a reset token"""
    try:
        result = reset_tokens_collection.delete_one({"token": token})
        return result.deleted_count > 0
    except Exception as e:
        logging.error(f"Error deleting reset token: {e}")
        return False

def cleanup_expired_tokens():
    """Clean up expired reset tokens"""
    try:
        result = reset_tokens_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        return result.deleted_count
    except Exception as e:
        logging.error(f"Error cleaning up tokens: {e}")
        return 0

class EmailService:
    def __init__(self):
        self.sender_email = os.getenv("EMAIL_ADDRESS")
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = os.getenv("SMTP_PORT")

    def send_reset_email(self, recipient_email, reset_link):
        """
        Send password reset email with HTML content.
        Returns True if successful.
        """
        try:
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Password Reset Request - Tech News"

            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>Password Reset Request</h2>
                    <p>You requested a password reset. Click the button below to reset your password:</p>
                    <p style="margin: 25px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #fbbf24; 
                                  color: black; 
                                  padding: 10px 20px; 
                                  text-decoration: none; 
                                  border-radius: 5px;">
                            Reset Password
                        </a>
                    </p>
                    <p>If you did not request this reset, please ignore this email.</p>
                    <p>This link will expire in 1 hour.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        {reset_link}
                    </p>
                </body>
            </html>
            """
            
            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False

# Initialize email service
email_service = EmailService()

# Create indexes
users_collection.create_index("email", unique=True)
reset_tokens_collection.create_index("token", unique=True)
reset_tokens_collection.create_index("expires_at", expireAfterSeconds=3600)  # Auto-delete expired tokens

"""
Article Model Schema:
{
    "_id": ObjectId,
    "title": String,
    "content": String,
    "summary": String,
    "url": String,
    "source": String,
    "author": String,
    "published_date": DateTime,
    "image_url": String,
    "categories": [String],
    "keywords": [String],
    "cluster_id": ObjectId,
    "sentiment_score": Float,
    "created_at": DateTime,
    "read_count": Integer,
    "view_time_avg": Float,
    "save_count": Integer,
    "ai_tags": [String]
}
"""
def store_article(article_data):
    """Store a new article fetched from news API"""
    article = {
        "title": article_data.get("title"),
        "content": article_data.get("content"),
        "summary": article_data.get("summary"),
        "url": article_data.get("url"),
        "source": article_data.get("source", {}).get("name"),
        "author": article_data.get("author"),
        "published_date": article_data.get("publishedAt"),
        "image_url": article_data.get("urlToImage"),
        "categories": [],
        "keywords": [],
        "cluster_id": None,  # Will be updated after clustering
        "sentiment_score": None,  # Will be updated after analysis
        "created_at": datetime.now(),
        "read_count": 0,
        "view_time_avg": 0,
        "save_count": 0,
        "ai_tags": []
    }
    article_id = db.articles.insert_one(article).inserted_id
    return article_id

def update_article_metrics(article_id, increment_reads=True, read_time=None, increment_saves=False):
    """Update article metrics when read or saved"""
    updates = {}
    
    if increment_reads:
        updates["$inc"] = {"read_count": 1}
    
    if read_time:
        # Get current average and count
        article = db.articles.find_one({"_id": ObjectId(article_id)})
        if article:
            current_avg = article.get("view_time_avg", 0)
            current_count = article.get("read_count", 0)
            
            # Calculate new average
            if current_count > 0:
                new_avg = ((current_avg * current_count) + read_time) / (current_count + 1)
            else:
                new_avg = read_time
            
            updates["$set"] = {"view_time_avg": new_avg}
    
    if increment_saves:
        if "$inc" in updates:
            updates["$inc"]["save_count"] = 1
        else:
            updates["$inc"] = {"save_count": 1}
    
    if updates:
        db.articles.update_one(
            {"_id": ObjectId(article_id)},
            updates
        )
    
    return True

"""
Reading History Model Schema:
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "article_id": ObjectId,
    "read_at": DateTime,
    "read_duration": Integer (seconds),
    "completed": Boolean,
    "device": String,
    "reading_position": Float
}
"""
def record_reading_history(user_id, article_id, duration=None, completed=True, device=None, position=None):
    """Record when a user reads an article"""
    history_item = {
        "user_id": ObjectId(user_id),
        "article_id": ObjectId(article_id),
        "read_at": datetime.now(),
        "read_duration": duration,
        "completed": completed,
        "device": device,
        "reading_position": position
    }
    
    # Check if already exists
    existing = db.reading_history.find_one({
        "user_id": ObjectId(user_id),
        "article_id": ObjectId(article_id)
    })
    
    if existing:
        # Update existing record
        db.reading_history.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "read_at": history_item["read_at"],
                "read_duration": history_item["read_duration"],
                "completed": history_item["completed"],
                "device": history_item["device"],
                "reading_position": history_item["reading_position"]
            }}
        )
        history_id = existing["_id"]
    else:
        # Create new record
        history_id = db.reading_history.insert_one(history_item).inserted_id
    
    # Update article metrics
    update_article_metrics(article_id, increment_reads=not existing, read_time=duration)
    
    return history_id

"""
Bookmark Model Schema:
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "article_id": ObjectId,
    "created_at": DateTime,
    "tags": [String],
    "notes": String
}
"""
def toggle_bookmark(user_id, article_id, tags=None, notes=None):
    """Toggle bookmark status for an article"""
    existing = db.bookmarks.find_one({
        "user_id": ObjectId(user_id),
        "article_id": ObjectId(article_id)
    })
    
    if existing:
        # Remove bookmark
        db.bookmarks.delete_one({"_id": existing["_id"]})
        # Update article metrics
        update_article_metrics(article_id, increment_reads=False, increment_saves=-1)
        return False
    else:
        # Add bookmark
        bookmark = {
            "user_id": ObjectId(user_id),
            "article_id": ObjectId(article_id),
            "created_at": datetime.now(),
            "tags": tags or [],
            "notes": notes or ""
        }
        db.bookmarks.insert_one(bookmark)
        # Update article metrics
        update_article_metrics(article_id, increment_reads=False, increment_saves=True)
        return True

def update_user_settings(user_id, settings_data):
    """Update user settings"""
    try:
        # Make sure user_id is a string
        if isinstance(user_id, ObjectId):
            user_id = str(user_id)
            
        # Update settings in database
        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'preferences': settings_data}}
        )
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user settings: {e}")
        return False

def update_bookmark(bookmark_id, tags=None, notes=None):
    """Update bookmark tags and notes"""
    updates = {}
    
    if tags is not None:
        updates["tags"] = tags
    
    if notes is not None:
        updates["notes"] = notes
    
    if updates:
        try:
            result = db.bookmarks.update_one(
                {"_id": ObjectId(bookmark_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating bookmark: {e}")
            return False
    
    return True

"""
Cluster Model Schema:
{
    "_id": ObjectId,
    "name": String,
    "description": String,
    "keywords": [String],
    "article_count": Integer,
    "created_at": DateTime,
    "updated_at": DateTime,
    "trending_score": Float
}
"""
def create_cluster(name, keywords, description=""):
    """Create a new article cluster"""
    cluster = {
        "name": name,
        "description": description,
        "keywords": keywords,
        "article_count": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "trending_score": 0
    }
    cluster_id = db.clusters.insert_one(cluster).inserted_id
    return cluster_id

def update_cluster_trending():
    """Update trending scores for all clusters based on recent article activity"""
    # Get all clusters
    clusters = db.clusters.find({})
    
    for cluster in clusters:
        # Get recent articles in this cluster (last 24 hours)
        recent_time = datetime.now() - timedelta(days=1)
        recent_articles = db.articles.find({
            "cluster_id": cluster["_id"],
            "created_at": {"$gte": recent_time}
        })
        
        # Calculate trending score based on reads and saves
        total_reads = 0
        total_saves = 0
        
        for article in recent_articles:
            total_reads += article.get("read_count", 0)
            total_saves += article.get("save_count", 0)
        
        # Simple trending algorithm: (reads + saves*3) / article_count
        trending_score = 0
        if cluster["article_count"] > 0:
            trending_score = (total_reads + (total_saves * 3)) / cluster["article_count"]
        
        # Update cluster
        db.clusters.update_one(
            {"_id": cluster["_id"]},
            {"$set": {
                "trending_score": trending_score,
                "updated_at": datetime.now()
            }}
        )
    
    return True

"""
Comment Model Schema:
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "article_id": ObjectId,
    "parent_id": ObjectId or None,
    "content": String,
    "created_at": DateTime,
    "updated_at": DateTime,
    "likes": Integer,
    "liked_by": [ObjectId]
}
"""
def add_comment(user_id, article_id, content, parent_id=None):
    """Add a comment to an article or reply to another comment"""
    comment = {
        "user_id": ObjectId(user_id),
        "article_id": ObjectId(article_id),
        "parent_id": ObjectId(parent_id) if parent_id else None,
        "content": content,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "likes": 0,
        "liked_by": []
    }
    
    comment_id = db.comments.insert_one(comment).inserted_id
    return comment_id

def like_comment(user_id, comment_id):
    """Like or unlike a comment"""
    # Check if user already liked this comment
    comment = db.comments.find_one({"_id": ObjectId(comment_id)})
    
    if not comment:
        return False
    
    user_obj_id = ObjectId(user_id)
    already_liked = any(liked_id == user_obj_id for liked_id in comment.get("liked_by", []))
    
    if already_liked:
        # Unlike
        db.comments.update_one(
            {"_id": ObjectId(comment_id)},
            {
                "$pull": {"liked_by": user_obj_id},
                "$inc": {"likes": -1}
            }
        )
        return False
    else:
        # Like
        db.comments.update_one(
            {"_id": ObjectId(comment_id)},
            {
                "$addToSet": {"liked_by": user_obj_id},
                "$inc": {"likes": 1}
            }
        )
        return True

"""
Notification Model Schema:
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "type": String,
    "content": String,
    "related_id": ObjectId,
    "created_at": DateTime,
    "read": Boolean
}
"""
def create_notification(user_id, type, content, related_id=None):
    """Create a notification for a user"""
    notification = {
        "user_id": ObjectId(user_id),
        "type": type,
        "content": content,
        "related_id": ObjectId(related_id) if related_id else None,
        "created_at": datetime.now(),
        "read": False
    }
    
    notification_id = db.notifications.insert_one(notification).inserted_id
    return notification_id

def mark_notification_read(notification_id, is_read=True):
    """Mark a notification as read or unread"""
    db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": is_read}}
    )
    return True

def mark_all_notifications_read(user_id):
    """Mark all notifications for a user as read"""
    db.notifications.update_many(
        {"user_id": ObjectId(user_id), "read": False},
        {"$set": {"read": True}}
    )
    return True

"""
Search History Model Schema:
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "query": String,
    "filters": Object,
    "result_count": Integer,
    "created_at": DateTime,
    "clicked_results": [ObjectId]
}
"""
def record_search(user_id, query, filters=None, result_count=0):
    """Record a user's search query"""
    search_record = {
        "user_id": ObjectId(user_id) if user_id else None,
        "query": query,
        "filters": filters or {},
        "result_count": result_count,
        "created_at": datetime.now(),
        "clicked_results": []
    }
    search_id = db.search_history.insert_one(search_record).inserted_id
    return search_id

def record_search_click(search_id, article_id):
    """Record when a user clicks on a search result"""
    db.search_history.update_one(
        {"_id": ObjectId(search_id)},
        {"$addToSet": {"clicked_results": ObjectId(article_id)}}
    )
    return True

# Helper functions for MongoDB indexes setup
def setup_database_indexes():
    """Setup necessary indexes for better query performance"""
    # Users collection indexes
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)
    users_collection.create_index("topics")
    users_collection.create_index("subscription_tier")
    users_collection.create_index("following")
    users_collection.create_index("followers")
    
    # Articles collection indexes
    db.articles.create_index("title")
    db.articles.create_index("cluster_id")
    db.articles.create_index("published_date")
    db.articles.create_index("source")
    db.articles.create_index("categories")
    db.articles.create_index("keywords")
    db.articles.create_index("ai_tags")
    db.articles.create_index("read_count")
    db.articles.create_index("save_count")
    db.articles.create_index([("title", "text"), ("content", "text"), ("summary", "text")])
    
    # Reading history indexes
    db.reading_history.create_index([("user_id", 1), ("read_at", -1)])
    db.reading_history.create_index([("user_id", 1), ("article_id", 1)], unique=True)
    db.reading_history.create_index("device")
    
    # Bookmarks indexes
    db.bookmarks.create_index([("user_id", 1), ("article_id", 1)], unique=True)
    db.bookmarks.create_index([("user_id", 1), ("created_at", -1)])
    db.bookmarks.create_index("tags")
    
    # Cluster indexes
    db.clusters.create_index("name")
    db.clusters.create_index("keywords")
    db.clusters.create_index("trending_score")
    
    # Comments indexes
    db.comments.create_index("article_id")
    db.comments.create_index("user_id")
    db.comments.create_index("parent_id")
    db.comments.create_index("created_at")
    
    # Notifications indexes
    db.notifications.create_index([("user_id", 1), ("created_at", -1)])
    db.notifications.create_index([("user_id", 1), ("read", 1)])
    
    # Search history indexes
    db.search_history.create_index([("user_id", 1), ("created_at", -1)])
    db.search_history.create_index("query")