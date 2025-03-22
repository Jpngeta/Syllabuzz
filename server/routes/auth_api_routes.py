# Authentication API routes for Syllabuzz
import logging
from flask import Blueprint, request, jsonify, session
from bson.objectid import ObjectId

# Import utils
from utils.db_utils import (
    users_collection, bookmark_article, remove_bookmark, get_user_bookmarks
)

from utils.auth_utils import login_required

# Import services
from services.recommendation_service import RecommendationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_api = Blueprint('auth_api', __name__)

@auth_api.route('/api/recommendations')
@login_required
def get_user_recommendations():
    """Get personalized recommendations for the logged-in user"""
    try:
        user_id = session.get('user_id')
        limit = int(request.args.get('limit', 20))
        
        # This function requires the recommendation_service to be passed to the Blueprint
        # It will be attached when registering the blueprint in app.py
        recommendations = auth_api.recommendation_service.get_user_recommendations(user_id, limit=limit)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logger.error(f"Error getting user recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/api/interaction', methods=['POST'])
@login_required
def record_interaction():
    """Record user interaction with an article"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('article_id'):
            return jsonify({"error": "Missing required fields"}), 400
        
        user_id = session.get('user_id')    
        result = auth_api.recommendation_service.record_interaction(
            user_id=user_id,
            article_id=data.get('article_id'),
            module_id=data.get('module_id'),
            interaction_type=data.get('type', 'view')
        )
        
        return jsonify({"success": result})
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/api/bookmarks/add', methods=['POST'])
@login_required
def add_bookmark():
    """Add an article to user's bookmarks"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('article_id'):
            return jsonify({"error": "Missing required article_id"}), 400
            
        user_id = session.get('user_id')
        article_id = data.get('article_id')
        module_id = data.get('module_id')
        
        result = bookmark_article(user_id, article_id, module_id)
        
        if result:
            return jsonify({"success": True, "message": "Article bookmarked successfully"})
        else:
            return jsonify({"success": False, "message": "Article is already bookmarked"})
    except Exception as e:
        logger.error(f"Error adding bookmark: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/api/bookmarks/remove', methods=['POST'])
@login_required
def remove_bookmark_api():
    """Remove an article from user's bookmarks"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('article_id'):
            return jsonify({"error": "Missing required article_id"}), 400
            
        user_id = session.get('user_id')
        article_id = data.get('article_id')
        
        result = remove_bookmark(user_id, article_id)
        
        if result:
            return jsonify({"success": True, "message": "Bookmark removed successfully"})
        else:
            return jsonify({"success": False, "message": "Bookmark not found"})
    except Exception as e:
        logger.error(f"Error removing bookmark: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/api/bookmarks')
@login_required
def get_bookmarks_api():
    """Get user's bookmarked articles"""
    try:
        user_id = session.get('user_id')
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        
        bookmarks = get_user_bookmarks(user_id, limit=limit, skip=skip)
        return jsonify({"bookmarks": bookmarks})
    except Exception as e:
        logger.error(f"Error getting bookmarks: {str(e)}")
        return jsonify({"error": str(e)}), 500