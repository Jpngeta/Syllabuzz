# Authentication API Routes
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from bson.objectid import ObjectId
from datetime import datetime, timedelta
import jwt
import re
from utils.db_utils import (
    users_collection, 
    find_user_by_email, 
    find_user_by_id, 
    create_user, 
    update_user_password,
    bookmark_article,
    remove_bookmark,
    get_user_bookmarks,
    is_article_bookmarked
)
from config import SECRET_KEY, JWT_EXPIRY_HOURS

auth_api = Blueprint('auth_api', __name__)

# Property to store the recommendation service, set in app.py
recommendation_service = None

def generate_jwt_token(user_id, expiry_hours=JWT_EXPIRY_HOURS):
    """Generate a JWT token for a user"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def validate_jwt_token(token):
    """Validate a JWT token and return user_id if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
    
def get_current_user(token):
    """Get the current user from a JWT token"""
    if not token:
        return None
        
    user_id = validate_jwt_token(token)
    if not user_id:
        return None
        
    user = find_user_by_id(user_id)
    if not user:
        return None
        
    # Convert ObjectId to string for JSON serialization
    user['_id'] = str(user['_id'])
    
    # Remove sensitive information
    if 'password' in user:
        del user['password']
        
    return user

@auth_api.route('/api/auth/signup', methods=['POST'])
def signup():
    """Register a new user"""
    data = request.json
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    email = data.get('email').lower().strip()
    password = data.get('password')
    name = data.get('name').strip()
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'message': 'Invalid email format'}), 400
        
    # Check if user already exists
    if find_user_by_email(email):
        return jsonify({'message': 'Email already registered'}), 400
        
    # Create username from email if not provided
    username = data.get('username')
    if not username:
        username = email.split('@')[0]
        
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Create user
    try:
        user_id = create_user(username, email, password_hash)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(user_id)
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@auth_api.route('/api/auth/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    print(data)
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
        
    email = data.get('email').lower().strip()
    password = data.get('password')

    print(email, password)
    
    # Find user by email
    user = find_user_by_email(email)
    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401
        
    # Check password
    if not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid email or password'}), 401
        
    # Generate JWT token
    token = generate_jwt_token(user['_id'])
    
    # Prepare user data for response
    user_data = {
        'id': str(user['_id']),
        'name': user.get('username', ''),
        'email': user['email'],
        'modules': [str(module) for module in user.get('modules', [])]
    }
    
    return jsonify({
        'token': token,
        'user': user_data
    }), 200

@auth_api.route('/api/auth/me', methods=['GET'])
def me():
    """Get the current authenticated user"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user = get_current_user(token)
    
    if not user:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    return jsonify({'user': user}), 200

@auth_api.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset a user's password with a valid token"""
    data = request.json
    
    # Validate required fields
    if not data or not data.get('token') or not data.get('password'):
        return jsonify({'message': 'Token and new password are required'}), 400
        
    token = data.get('token')
    new_password = data.get('password')
    
    # Validate token
    user_id = validate_jwt_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    # Hash new password
    password_hash = generate_password_hash(new_password)
    
    # Update password
    if update_user_password(user_id, password_hash):
        return jsonify({'message': 'Password reset successfully'}), 200
    else:
        return jsonify({'message': 'Failed to reset password'}), 500

@auth_api.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send a password reset token to a user's email"""
    data = request.json
    
    # Validate required fields
    if not data or not data.get('email'):
        return jsonify({'message': 'Email is required'}), 400
        
    email = data.get('email').lower().strip()
    
    # Find user by email
    user = find_user_by_email(email)
    if not user:
        # Don't reveal if the email exists for security reasons
        return jsonify({'message': 'If your email is registered, you will receive a password reset link'}), 200
        
    # In a real application, you would send an email with the reset link
    # For this implementation, we'll just generate a token
    reset_token = generate_jwt_token(user['_id'], expiry_hours=1)
    
    # Note: In a real application, you would send this token via email
    # For simplicity, we'll just return it in the response (not secure for production)
    return jsonify({
        'message': 'Password reset instructions sent',
        'reset_token': reset_token  # Would be sent by email in production
    }), 200

@auth_api.route('/api/auth/verify-reset-token', methods=['GET'])
def verify_reset_token():
    """Verify if a reset token is valid"""
    token = request.args.get('token')
    
    if not token:
        return jsonify({'message': 'Token is required'}), 400
        
    user_id = validate_jwt_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    return jsonify({'message': 'Token is valid'}), 200

@auth_api.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout the current user (client should discard token)"""
    # JWT is stateless, so server-side we don't need to do anything
    # The client should discard the token
    return jsonify({'message': 'Logout successful'}), 200

# =========== Article Interaction Routes ===========

@auth_api.route('/api/auth/like', methods=['POST'])
def like_article():
    """Like an article"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_jwt_token(token)
    
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    data = request.json
    
    # Validate required fields
    if not data or not data.get('article_id'):
        return jsonify({'message': 'Article ID is required'}), 400
        
    article_id = data.get('article_id')
    module_id = data.get('module_id')
    
    # Record like interaction
    if recommendation_service:
        result = recommendation_service.record_interaction(
            user_id=user_id,
            article_id=article_id,
            module_id=module_id,
            interaction_type='like'
        )
        
        if result:
            return jsonify({'message': 'Article liked successfully'}), 200
        else:
            return jsonify({'message': 'Failed to like article'}), 500
    else:
        return jsonify({'message': 'Recommendation service not available'}), 500

@auth_api.route('/api/auth/bookmark', methods=['POST'])
def save_article():
    """Bookmark an article"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_jwt_token(token)
    
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    data = request.json
    
    # Validate required fields
    if not data or not data.get('article_id'):
        return jsonify({'message': 'Article ID is required'}), 400
        
    article_id = data.get('article_id')
    module_id = data.get('module_id')
    
    # Record bookmark interaction
    if recommendation_service:
        recommendation_service.record_interaction(
            user_id=user_id,
            article_id=article_id,
            module_id=module_id,
            interaction_type='bookmark'
        )
    
    # Save to bookmarks collection
    result = bookmark_article(user_id, article_id, module_id)
    
    if result is not None:
        return jsonify({'message': 'Article bookmarked successfully'}), 200
    else:
        return jsonify({'message': 'Article already bookmarked'}), 200

@auth_api.route('/api/auth/bookmarks', methods=['GET'])
def get_bookmarks():
    """Get user's bookmarked articles"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_jwt_token(token)
    
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
        
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Get bookmarks using the existing function
    raw_bookmarks = get_user_bookmarks(user_id, limit=limit, skip=skip)
    
    # Create a JSON serializable copy with all ObjectIds converted to strings
    bookmarks = []
    for bookmark in raw_bookmarks:
        # Create a serializable copy of the bookmark
        serializable_bookmark = {}
        
        # Handle nested article data
        if 'article' in bookmark:
            serializable_bookmark['article'] = {}
            for key, value in bookmark['article'].items():
                if isinstance(value, ObjectId):
                    serializable_bookmark['article'][key] = str(value)
                else:
                    serializable_bookmark['article'][key] = value
        
        # Handle other fields
        for key, value in bookmark.items():
            if key == 'article':
                continue  # Already handled
            elif isinstance(value, ObjectId):
                serializable_bookmark[key] = str(value)
            else:
                serializable_bookmark[key] = value
        
        bookmarks.append(serializable_bookmark)
    
    return jsonify({'bookmarks': bookmarks}), 200

@auth_api.route('/api/auth/bookmark/<article_id>', methods=['DELETE'])
def remove_saved_article(article_id):
    """Remove a bookmarked article"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_jwt_token(token)
    
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
    
    result = remove_bookmark(user_id, article_id)
    
    if result:
        return jsonify({'message': 'Bookmark removed successfully'}), 200
    else:
        return jsonify({'message': 'Bookmark not found'}), 404

@auth_api.route('/api/auth/bookmark/<article_id>/status', methods=['GET'])
def check_bookmark_status(article_id):
    """Check if an article is bookmarked by the current user"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authentication required'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_jwt_token(token)
    
    if not user_id:
        return jsonify({'message': 'Invalid or expired token'}), 401
    
    is_bookmarked = is_article_bookmarked(user_id, article_id)
    
    return jsonify({'isBookmarked': is_bookmarked}), 200