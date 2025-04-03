# Main Flask application
import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime
from bson.objectid import ObjectId
import threading

# Option 1: Set specific allowed origins
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5174", "http://localhost:3000"]}})


# Import services
from services.news_service import NewsAPIClientService
from services.article_service import ArticleService
from services.embedding_service import EmbeddingService
from services.recommendation_service import RecommendationService
from services.scheduler_service import SchedulerService
from services.arXiv_service import ArxivService

# Import utils
from utils.db_utils import initialize_database, modules_collection, articles_collection, relevance_collection, users_collection

# Import blueprints
from routes.auth_api_routes import auth_api

# Import configuration
from config import NEWS_API_KEY, DEBUG, SECRET_KEY, SBERT_MODEL_NAME, SESSION_EXPIRY_DAYS, RELEVANCE_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app

app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Initialize services (do this before starting the scheduler)
news_service = NewsAPIClientService(api_key=NEWS_API_KEY)
article_service = ArticleService(news_api_key=NEWS_API_KEY)
embedding_service = EmbeddingService(model_name=SBERT_MODEL_NAME)
recommendation_service = RecommendationService(embedding_service=embedding_service)
arxiv_service = ArxivService()
scheduler_service = SchedulerService(article_service=article_service, embedding_service=embedding_service, arxiv_service=arxiv_service)


# Store scheduler thread reference
scheduler_thread = None

def start_scheduler_thread():
    """Start the scheduler in a separate thread"""
    global scheduler_thread
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("Scheduler thread is already running")
        return
    
    def run_scheduler():
        try:
            logger.info("Starting scheduler thread")
            scheduler_service.start()
        except Exception as e:
            logger.error(f"Error in scheduler thread: {str(e)}")
    
    # Create and start a daemon thread for the scheduler
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # This ensures the thread will exit when the main program exits
    scheduler_thread.start()
    
    logger.info("Scheduler thread started")

def setup():
    """Initialize database and start scheduler"""
    try:
        initialize_database()
        logger.info("Database initialized")
        
        # Start scheduler in a separate thread
        # start_scheduler_thread()
        
        logger.info("Application setup complete")
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")

# Register blueprints
app.register_blueprint(auth_api)

import routes.auth_api_routes as auth_routes
auth_routes.recommendation_service = recommendation_service

# Web Routes
@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Search page route"""
    query = request.args.get('q', '')
    return render_template('search.html', query=query)

@app.route('/module/<module_id>')
def module_detail(module_id):
    """Module detail page route"""
    try:
        # Validate module exists
        module = modules_collection.find_one({"_id": ObjectId(module_id)})
        if not module:
            return redirect(url_for('index'))
        return render_template('module.html', module_id=module_id)
    except Exception as e:
        logger.error(f"Error loading module page: {str(e)}")
        return redirect(url_for('index'))

@app.route('/articles/<category>')
def articles_by_category(category):
    """Articles by category page route"""
    return render_template('index.html', category=category)

@app.route('/trending')
def trending():
    """Trending articles page route"""
    return render_template('index.html', section='trending')

# API Routes
@app.route('/api/modules')
def get_modules():
    """Get all CS modules"""
    try:
        modules = list(modules_collection.find({}, {"vector_embedding": 0}))
        
        # Convert ObjectId to string for JSON serialization
        for module in modules:
            module["_id"] = str(module["_id"])
            
        return jsonify({"modules": modules})
    except Exception as e:
        logger.error(f"Error getting modules: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules/<module_id>')
def get_module(module_id):
    """Get a single module by ID"""
    try:
        module = modules_collection.find_one({"_id": ObjectId(module_id)}, {"vector_embedding": 0})
        
        if module:
            # Convert ObjectId to string
            module["_id"] = str(module["_id"])
            return jsonify({"module": module})
        else:
            return jsonify({"error": "Module not found"}), 404
    except Exception as e:
        logger.error(f"Error getting module: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules/<module_id>/recommendations')
def get_module_recommendations(module_id):
    """Get article recommendations for a specific module"""
    try:
        limit = int(request.args.get('limit', 10))
        recommendations = recommendation_service.get_module_recommendations(module_id, limit=limit)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logger.error(f"Error getting module recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles')
def get_articles():
    """Get articles and papers with optional category filter"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        
        articles = article_service.get_combined_articles(category, limit=limit, skip=skip)
        return jsonify({"articles": articles})
    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles/<article_id>')
def get_article(article_id):
    """Get a single article by ID"""
    try:
        article = article_service.get_article_by_id(article_id)
        if article:
            return jsonify({"article": article})
        else:
            return jsonify({"error": "Article not found"}), 404
    except Exception as e:
        logger.error(f"Error getting article: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/articles/relevant')
def get_relevant_articles():
    """Get articles prioritized by relevance across all modules and sorted by date"""
    try:
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        
        # Get articles with high relevance scores across all modules
        pipeline = [
            {"$match": {"relevance_score": {"$gte": RELEVANCE_THRESHOLD}}},
            {"$sort": {"relevance_score": -1}},
            {"$group": {
                "_id": "$article_id",
                "relevance_score": {"$max": "$relevance_score"}
            }},
            {"$lookup": {
                "from": "articles",
                "localField": "_id",
                "foreignField": "_id",
                "as": "article"
            }},
            {"$unwind": "$article"},
            {"$sort": {"article.published_at": -1}},  # Sort by date after filtering by relevance
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {
                "_id": "$article._id",
                "title": "$article.title",
                "description": "$article.description",
                "content": "$article.content",
                "url": "$article.url",
                "image_url": "$article.image_url",
                "source_name": "$article.source_name",
                "published_at": "$article.published_at",
                "updated_at": "$article.updated_at",
                "categories": "$article.categories",
                "authors": "$article.authors",
                "pdf_url": "$article.pdf_url",
                "arxiv_id": "$article.arxiv_id",
                "relevance_score": 1,
                "type": {"$cond": [{"$eq": ["$article.source_name", "arXiv"]}, "academic", "news"]}
            }}
        ]
        
        relevant_articles = list(relevance_collection.aggregate(pipeline))
        
        # Convert ObjectIds to strings
        for article in relevant_articles:
            article["_id"] = str(article["_id"])
        
        logger.info(f"Found {len(relevant_articles)} relevant articles across all modules")
        return jsonify({"articles": relevant_articles})
    except Exception as e:
        logger.error(f"Error getting relevant articles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def search_articles():
    """Search articles and papers by query"""
    try:
        query = request.args.get('q')
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
            
        articles = article_service.search_combined(query, limit=limit, skip=skip)
        return jsonify({"articles": articles})
    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trending')
def get_trending():
    """Get trending articles based on user interactions"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
        
        trending = recommendation_service.get_trending_articles(days=days, limit=limit)
        return jsonify({"trending": trending})
    except Exception as e:
        logger.error(f"Error getting trending articles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/<user_id>')
def get_user_recommendations(user_id):
    """Get personalized recommendations for a user"""
    try:
        limit = int(request.args.get('limit', 20))
        
        recommendations = recommendation_service.get_user_recommendations(user_id, limit=limit)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logger.error(f"Error getting user recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/interaction', methods=['POST'])
def record_interaction():
    """Record user interaction with an article"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('user_id') or not data.get('article_id'):
            return jsonify({"error": "Missing required fields"}), 400
            
        result = recommendation_service.record_interaction(
            user_id=data.get('user_id'),
            article_id=data.get('article_id'),
            module_id=data.get('module_id'),
            interaction_type=data.get('type', 'view')
        )
        
        return jsonify({"success": result})
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('email') or not data.get('name'):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Check if user exists
        existing_user = users_collection.find_one({"email": data.get('email')})
        if existing_user:
            return jsonify({"error": "User already exists"}), 400
            
        # Create user
        user = {
            "name": data.get('name'),
            "email": data.get('email'),
            "modules": data.get('modules', []),  # List of module IDs
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = users_collection.insert_one(user)
        
        return jsonify({
            "success": True,
            "user_id": str(result.inserted_id),
            "message": "User registered successfully"
        })
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<user_id>/modules', methods=['PUT'])
def update_user_modules(user_id):
    """Update user's enrolled modules"""
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('modules'):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Validate user exists
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Update user modules
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "modules": data.get('modules'),
                    "updated_at": datetime.now()
                }
            }
        )
        
        return jsonify({
            "success": True,
            "message": "User modules updated successfully"
        })
    except Exception as e:
        logger.error(f"Error updating user modules: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Admin Routes
@app.route('/api/admin/scheduler/status')
def scheduler_status():
    """Get the status of the scheduler"""
    try:
        is_running = False
        if scheduler_thread and scheduler_thread.is_alive():
            is_running = True
            
        return jsonify({
            "is_running": is_running,
            "scheduler_service_running": scheduler_service.is_running
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler if it's not already running"""
    try:
        start_scheduler_thread()
        return jsonify({
            "success": True,
            "message": "Scheduler started or already running"
        })
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/update-embeddings', methods=['POST'])
def update_embeddings():
    """Admin endpoint to trigger embedding updates"""
    try:
        data = request.json
        source = data.get('source', 'articles')
        
        if source == 'modules':
            embedding_service.update_all_module_embeddings()
            return jsonify({"message": "Module embeddings update initiated"})
        elif source == 'articles':
            days = int(data.get('days', 1))
            embedding_service.update_recent_article_embeddings(days=days)
            return jsonify({"message": f"Article embeddings update initiated for last {days} days"})
        elif source == 'relevance':
            embedding_service.update_relevance_scores()
            return jsonify({"message": "Relevance scores update initiated"})
        else:
            return jsonify({"error": "Invalid source. Use 'modules', 'articles', or 'relevance'"}), 400
    except Exception as e:
        logger.error(f"Error updating embeddings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fetch-articles', methods=['POST'])
def fetch_articles():
    """Admin endpoint to trigger article fetching"""
    try:
        data = request.json
        category = data.get('category')
        count = int(data.get('count', 20))
        
        result = article_service.fetch_and_store_articles(category=category, count=count)
        return jsonify({"message": f"Fetched and stored {result} articles"})
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/admin/fetch-papers', methods=['POST'])
def fetch_papers():
    """Admin endpoint to trigger paper fetching"""
    try:
        data = request.json
        query = data.get('query', 'cs.AI')
        count = int(data.get('count', 20))
        
        result = arxiv_service.fetch_and_store_papers(search_query=query, max_results=count)
        return jsonify({"message": f"Fetched and stored {result} papers"})
    except Exception as e:
        logger.error(f"Error fetching papers: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/admin/fetch-targeted-content', methods=['POST'])
def fetch_targeted_content():
    """Admin endpoint to trigger targeted content fetching for all modules"""
    try:
        result = scheduler_service.fetch_targeted_content_for_modules()
        return jsonify({"message": "Targeted content fetching completed", "success": result})
    except Exception as e:
        logger.error(f"Error fetching targeted content: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fetch-module-content/<module_id>', methods=['POST'])
def fetch_module_content(module_id):
    """Admin endpoint to trigger content fetching for a specific module"""
    try:
        # Get module details
        module = modules_collection.find_one({"_id": ObjectId(module_id)})
        if not module:
            return jsonify({"error": "Module not found"}), 404
            
        # Fetch news articles
        article_count = article_service.fetch_module_specific_articles(module_id, count=20)
        
        # Fetch arXiv papers
        paper_count = arxiv_service.fetch_module_specific_papers(module_id, max_results=20)
        
        # Update embeddings for the new content
        if article_count > 0 or paper_count > 0:
            embedding_service.update_recent_article_embeddings(days=1)
            embedding_service.update_relevance_scores()
        
        return jsonify({
            "message": f"Fetched {article_count} articles and {paper_count} papers for module",
            "module_name": module.get("name", "Unknown")
        })
    except Exception as e:
        logger.error(f"Error fetching module content: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fetch-keyword-content', methods=['POST'])
def fetch_keyword_content():
    """Admin endpoint to fetch content for specific keywords"""
    try:
        data = request.json
        
        if not data or not data.get('keywords'):
            return jsonify({"error": "Missing required field 'keywords'"}), 400
            
        keywords = data.get('keywords')
        count = int(data.get('count', 20))
        
        # Fetch news articles
        article_count = article_service.fetch_targeted_articles(keywords, count=count)
        
        # Fetch arXiv papers
        paper_count = arxiv_service.fetch_targeted_papers(keywords, max_results=count)
        
        # Update embeddings for the new content
        if article_count > 0 or paper_count > 0:
            embedding_service.update_recent_article_embeddings(days=1)
            embedding_service.update_relevance_scores()
        
        return jsonify({
            "message": f"Fetched {article_count} articles and {paper_count} papers for keywords: {keywords}"
        })
    except Exception as e:
        logger.error(f"Error fetching keyword content: {str(e)}")
        return jsonify({"error": str(e)}), 500

# @app.route('/api/admin/relevance-threshold', methods=['POST'])
# def update_relevance_threshold():
#     """Admin endpoint to adjust the relevance threshold"""
#     try:
#         data = request.json
        
#         if not data or not data.get('threshold'):
#             return jsonify({"error": "Missing required field 'threshold'"}), 400
            
#         # Get current threshold
#         from config import RELEVANCE_THRESHOLD
#         current_threshold = RELEVANCE_THRESHOLD
        
#         # Update threshold in config (this is temporary, restarts will reset it)
#         import sys
#         module = sys.modules['config']
#         setattr(module, 'RELEVANCE_THRESHOLD', float(data.get('threshold')))
        
#         # Recalculate relevance with new threshold
#         if data.get('recalculate', False):
#             embedding_service.update_relevance_scores()
        
#         return jsonify({
#             "message": f"Updated relevance threshold from {current_threshold} to {data.get('threshold')}",
#             "recalculated": data.get('recalculate', False)
#         })
#     except Exception as e:
#         logger.error(f"Error updating relevance threshold: {str(e)}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reset-database', methods=['POST'])
def reset_database():
    """Admin endpoint to reset the database (DANGEROUS: for development use only)"""
    try:
        # Check for authorization (in a real app, implement proper authentication)
        if app.config['DEBUG'] is not True:
            return jsonify({"error": "This operation is only allowed in debug mode"}), 403
            
        # Re-initialize database
        initialize_database()
        
        # Fetch initial articles
        for category in ["technology", "science", "education"]:
            article_service.fetch_and_store_articles(category=category, count=20)
            
        # Update embeddings
        embedding_service.update_all_module_embeddings()
        embedding_service.update_recent_article_embeddings(days=7)
        embedding_service.update_relevance_scores()
        
        return jsonify({"message": "Database reset and initialized with sample data"})
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500

# Custom filters
@app.template_filter('format_date')
def format_date(value, format='%B %d, %Y'):
    """Format a date"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        except:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except:
                return value
    return value.strftime(format)

if __name__ == '__main__':
    with app.app_context():
        # Call setup to initialize the database
        setup()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)