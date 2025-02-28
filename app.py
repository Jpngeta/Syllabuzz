from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, send_from_directory, current_app, g, has_app_context
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import secrets
import os
import threading
from services.scheduler import fetch_category_articles, start_scheduler
# from tasks import start_scheduler
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
import random
from functools import wraps
from tasks import start_scheduler
import json

from db import (
    create_user, find_user_by_email, update_user_password, verify_password,
    create_reset_token, find_reset_token, delete_reset_token, EmailService,mark_notification_read,
    store_article, update_article_metrics, record_reading_history, toggle_bookmark,
    update_bookmark, create_cluster, update_cluster_trending, add_comment, like_comment,
    create_notification, mark_all_notifications_read, record_search, record_search_click, db
)

# Add these imports
from services import article_service

# Add these imports at the top of your file
from services.news_service import NewsAPIClientService
import os
from dotenv import load_dotenv

# Add this near your imports at the top
from services.scheduler import start_scheduler

# Load environment variables from .env file
load_dotenv()

# Initialize the news API service
news_service = NewsAPIClientService(api_key=os.environ.get('NEWS_API_KEY'))

# Create Flask app first
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

csrf = CSRFProtect(app)
# csrf.exempt(toggle_bookmark)
# csrf.exempt(record_article_view)
# csrf.exempt(bookmark_note)
logging.basicConfig(level=logging.ERROR)
email_service = EmailService()

# Add this function near the top of your file after your imports
def get_json_data():
    """Safely get JSON data from request, even if content-type is not set"""
    try:
        # First try standard method
        if request.is_json:
            return request.get_json()
        
        # Fall back to manual parsing
        data = request.get_data(as_text=True)
        if data:
            return json.loads(data)
        return {}
    except Exception as e:
        app.logger.error(f"Error parsing JSON data: {str(e)}")
        return {}

# After initializing csrf with csrf = CSRFProtect(app)
@app.context_processor
def inject_csrf_token():
    """Make csrf_token available to all templates"""
    def get_csrf_token():
        return csrf._get_csrf_token()
    return dict(csrf_token=get_csrf_token)

# Configure upload folder for profile images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

# File extensions allowed for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update this decorator to handle AJAX requests properly
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Authentication required", "redirect": url_for('login')}), 401
            else:
                # IMPORTANT: Don't redirect to profile here
                flash('You need to be logged in to access this page.', 'error')
                return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter('route_exists')
def route_exists(route_name):
    """Check if a route exists in the Flask app"""
    try:
        return current_app.url_for(route_name, _external=False) is not None
    except:
        return False

@app.before_request
def check_session_expiry():
    # Avoid checking login routes to prevent redirect loops
    if request.endpoint in ['login', 'signup', 'static', 'forgot_password', 'reset_password']:
        return  # Skip checking for these routes
    
    if 'user_id' in session:
        # Check if session is valid
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        # Verify user still exists in database
        success, _ = find_user_by_email(user_email)
        if not success:
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for('login'))

# Add this function near the top of your file, after your app initialization
@app.before_request
def load_user():
    """Load user data before each request if user is logged in"""
    # Skip for login-related endpoints
    if request.endpoint in ['login', 'signup', 'static', 'forgot_password', 'reset_password']:
        g.user = None
        return
        
    if 'user_id' in session:
        try:
            user_id = session.get('user_id')
            user = db.users.find_one({'_id': ObjectId(user_id)})
            g.user = user
        except Exception as e:
            g.user = None
    else:
        g.user = None

# Add this context processor to make user data available in all templates
@app.context_processor
def inject_user():
    """Make user data available to all templates"""
    if hasattr(g, 'user'):
        return {'user': g.user}
    return {'user': None}

# Add this after app initialization but before your routes
with app.app_context():
    # Initialize anything that needs the application context
    pass

# Create a function to initialize your app
def init_app(app):
    """Initialize the Flask application with all required components"""
    # Start the scheduler when the app starts
    start_scheduler()

# Use the new pattern with app events
# @app.before_serving
# def before_serving():
#     """Run before the app starts serving requests"""
#     app.logger.info("Starting background tasks")
#     start_scheduler()

@app.route("/", methods=["GET", "POST"])
def login():
    form = FlaskForm()
    if 'user_id' in session:
        # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))
        
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Invalid form submission.", "error")
            return render_template("login.html", form=form)
            
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not all([email, password]):
            flash("Email and password are required.", "error")
            return render_template("login.html", form=form)
        
        print(f"Login attempt for email: {email}")
        success, user = find_user_by_email(email)
        
        if success:
            print(f"User found: {user.get('name')}")
            if verify_password(user, password):
                print("Password verified successfully")
                # Set session data
                session['user_id'] = str(user['_id'])
                session['user_email'] = user['email']
                session.permanent = True
                
                # Debug session
                print(f"Set session: user_id={session.get('user_id')}, user_email={session.get('user_email')}")
                
                # Check if there was a next parameter
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for("dashboard"))
            else:
                print("Password verification failed")
                flash("Invalid password. Please try again.", "error")
        else:
            print(f"User not found for email: {email}")
            flash("Email not found. Please check your email or sign up.", "error")
    
    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = FlaskForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Invalid form submission.", "error")
            return redirect(url_for("signup"))

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not all([name, email, password]):
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))
        
        if create_user(name, email, password):
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Email already registered.", "error")
    return render_template("signup.html", form=form)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = FlaskForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Invalid form submission.", "error")
            return redirect(url_for("forgot_password"))

        email = request.form.get("email")
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("forgot_password"))
        
        success, _ = find_user_by_email(email)
        if success:
            reset_token = secrets.token_urlsafe(16)
            create_reset_token(email, reset_token)
            
            reset_link = url_for("reset_password", token=reset_token, _external=True)
            if email_service.send_reset_email(email, reset_link):
                flash("Password reset link sent to your email.", "success")
            else:
                flash("Error sending reset email. Please try again.", "error")
            
            return redirect(url_for("login"))
        else:
            flash("Email not found.", "error")
    
    return render_template("forgot-password.html", form=form)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = FlaskForm()
    reset_token_data = find_reset_token(token)
    if not reset_token_data:
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Invalid form submission.", "error")
            return redirect(url_for("reset_password", token=token))

        new_password = request.form.get("new-password")
        confirm_password = request.form.get("confirm-password")
        
        if not all([new_password, confirm_password]):
            flash("All fields are required.", "error")
            return redirect(url_for("reset_password", token=token))
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            email = reset_token_data["email"]
            update_user_password(email, new_password)
            delete_reset_token(token)
            flash("Password reset successful! Please log in.", "success")
            return redirect(url_for("login"))
    
    return render_template("reset-password.html", token=token, form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Show dashboard with article categories"""
    try:
        # Get a smaller sample of articles from primary categories
        primary_categories = ['business', 'health']
        secondary_categories = ['technology', 'entertainment']
        
        # First load just 3 from each primary category
        primary_articles = {}
        for category in primary_categories:
            try:
                # Load with a smaller page size to avoid rate limits
                articles_data = article_service.get_articles(category=category, page=1, page_size=4)
                primary_articles[category] = articles_data.get('articles', [])[:4]
            except Exception as e:
                app.logger.error(f"Error loading {category} articles: {str(e)}")
                primary_articles[category] = []
        
        # For secondary categories, we'll load them via AJAX later
        
        # Get user's bookmarks
        bookmarked_articles = []
        if 'user_id' in session:
            user_id = session.get('user_id')
            bookmarks = list(db.bookmarks.find({"user_id": user_id}))
            bookmarked_articles = [str(b["article_id"]) for b in bookmarks]
        
        return render_template('dashboard.html',
                              primary_articles=primary_articles,
                              secondary_categories=secondary_categories,
                              bookmarked_articles=bookmarked_articles)
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('articles'))

@app.route('/api/user/settings', methods=['PUT'])
@login_required
def update_settings():
    user_id = session.get("user_id")
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    success = update_user_settings(user_id, data)
    
    if success:
        return jsonify({"message": "Settings updated successfully"})
    else:
        return jsonify({"error": "Failed to update settings"}), 500

# Add imports at the top
from services import article_service

@app.route('/articles')
def articles():
    try:
        category = request.args.get('category', 'all')
        search_query = request.args.get('q', None)
        page = int(request.args.get('page', 1))
        
        # Fetch articles
        try:
            articles_data = None
            if search_query:
                articles_data = article_service.search_articles(search_query, page=page)
                app.logger.info(f"Search query: {search_query}, Articles found: {len(articles_data.get('articles', []))}")
            else:
                articles_data = article_service.get_articles(category=category, page=page)
                app.logger.info(f"Category: {category}, Articles found: {len(articles_data.get('articles', []))}")
        except Exception as api_error:
            # Log the error but continue with empty results
            app.logger.error(f"Error fetching {category} articles: {str(api_error)}")
            articles_data = {"articles": [], "total_results": 0}
        
        # Get articles from database
        db_articles = articles_data.get("articles", [])
        
        # Get pagination info
        total_articles = articles_data.get("total_results", 0)
        articles_per_page = 12  # Articles per page
        total_pages = max(1, (total_articles + articles_per_page - 1) // articles_per_page)
        
        # Get user bookmarks
        bookmarked_articles = []
        if 'user_id' in session:
            user_id = session.get('user_id')
            bookmarks = list(db.bookmarks.find({"user_id": user_id}))
            bookmarked_articles = [str(b["article_id"]) for b in bookmarks]
        
        app.logger.info(f"Final count: {len(db_articles)} articles")
        
        if db_articles:
            app.logger.info(f"First article title: {db_articles[0]['title']}")
        
        return render_template('articles.html',
                          articles=db_articles,
                          category=category,
                          search_query=search_query,
                          current_page=page,
                          total_pages=total_pages,
                          total_articles=total_articles,
                          bookmarked_articles=bookmarked_articles)
    except Exception as e:
        app.logger.error(f"Error in articles route: {str(e)}")
        print(f"Error in articles route: {str(e)}")
        flash("Error loading articles. Please try again.", "error")
        return render_template('articles.html', 
                           articles=[], 
                           category='all',
                           current_page=1,
                           total_pages=1,
                           total_articles=0,
                           bookmarked_articles=[])

@app.route('/news')
def news_home():
    """Display the news home page with featured articles"""
    try:
        # Get articles from multiple categories
        categories = ['business', 'technology', 'health', 'entertainment']
        featured_articles = []
        
        # Get 3 articles from each category
        for category in categories:
            try:
                category_articles = article_service.get_articles(category=category, page=1)
                articles = category_articles.get('articles', [])[:3]
                featured_articles.extend(articles)
            except Exception as e:
                app.logger.error(f"Error fetching {category} articles: {str(e)}")
        
        # Shuffle the articles for variety
        import random
        random.shuffle(featured_articles)
        
        # Get trending articles (most read/bookmarked)
        trending_articles = []
        try:
            # Get articles with the most reading history entries in the last 7 days
            from datetime import datetime, timedelta
            pipeline = [
                {"$match": {"read_at": {"$gt": datetime.utcnow() - timedelta(days=7)}}},
                {"$group": {"_id": "$article_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            trending_ids = list(db.reading_history.aggregate(pipeline))
            
            # Get the full article data for each trending article
            for item in trending_ids:
                try:
                    article = article_service.get_article_by_id(item['_id'])
                    if article:
                        trending_articles.append(article)
                except:
                    continue
        except Exception as e:
            app.logger.error(f"Error fetching trending articles: {str(e)}")
        
        # If not enough trending articles, add some featured ones
        if len(trending_articles) < 5 and featured_articles:
            trending_articles.extend(featured_articles[:5-len(trending_articles)])
        
        # Get user bookmarks if logged in
        bookmarked_articles = []
        if 'user_id' in session:
            user_id = session.get('user_id')
            bookmarks = list(db.bookmarks.find({"user_id": user_id}))
            bookmarked_articles = [str(b["article_id"]) for b in bookmarks]
        
        return render_template('news_home.html', 
                              featured_articles=featured_articles[:8],
                              trending_articles=trending_articles[:5],
                              categories=categories,
                              bookmarked_articles=bookmarked_articles)
    
    except Exception as e:
        app.logger.error(f"Error loading news home: {str(e)}")
        flash('Error loading news page', 'error')
        return redirect(url_for('dashboard'))

@app.route('/article/<article_id>')
def article(article_id):
    """Display a single article."""
    try:
        app.logger.info(f"Accessing article with ID: {article_id}")
        
        # First attempt - look up by ObjectId
        article_obj = None
        try:
            article_obj_id = ObjectId(article_id)
            article_obj = db.articles.find_one({"_id": article_obj_id})
        except Exception as e:
            app.logger.warning(f"Could not find article with ObjectId {article_id}: {str(e)}")
        
        # If not found by ObjectId, try string ID
        if not article_obj:
            article_obj = db.articles.find_one({"_id": article_id})
            
        # If still not found, check for a URL match (sometimes URLs are shared as IDs)
        if not article_obj and '/' in article_id:
            article_obj = db.articles.find_one({"url": article_id})
        
        # If still not found, give up
        if not article_obj:
            app.logger.error(f"Article not found with any method: {article_id}")
            flash("Article not found", "error")
            return redirect(url_for("news_home"))
            
        # Convert article ID to string for the template
        article_obj["_id"] = str(article_obj["_id"])
        
        # Format the published date if needed
        if "published_at" in article_obj and not isinstance(article_obj["published_at"], str):
            try:
                article_obj["published_at"] = article_obj["published_at"].strftime("%Y-%m-%d %H:%M")
            except:
                article_obj["published_at"] = str(article_obj["published_at"])
        
        # Check for bookmarks if user is logged in
        is_bookmarked = False
        has_note = False
        
        if "user_id" in session:
            user_id = session.get("user_id")
            
            bookmark = db.bookmarks.find_one({
                "user_id": user_id,
                "article_id": ObjectId(str(article_obj["_id"]))
            })
            
            if not bookmark:
                # Try string comparison as fallback
                bookmark = db.bookmarks.find_one({
                    "user_id": user_id,
                    "article_id": str(article_obj["_id"])
                })
            
            is_bookmarked = bookmark is not None
            has_note = bookmark and "notes" in bookmark and bookmark["notes"].strip() != ""
        
        # Add debugging info
        app.logger.info(f"Returning article: {article_obj.get('title', 'No title')}")
        
        return render_template("article.html", 
                              article=article_obj, 
                              is_bookmarked=is_bookmarked,
                              has_note=has_note)
                              
    except Exception as e:
        app.logger.error(f"Error in article route: {str(e)}")
        flash("An error occurred while loading the article", "error")
        return redirect(url_for("news_home"))

@app.route('/article/')
def article_redirect():
    """Handle missing article ID case"""
    flash('Article ID is required', 'error')
    return redirect(url_for('news_home'))

@app.route('/admin/fetch-articles', methods=['GET', 'POST'])
@login_required
def admin_fetch_articles():
    """Admin page to fetch articles from News API"""
    # Check if user is admin
    user_email = session.get('user_email')
    success, user_data = find_user_by_email(user_email)
    
    if not success or not user_data.get('is_admin', False):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'fetch_headlines':
            category = request.form.get('category')
            country = request.form.get('country', 'us')
            
            # Use the updated article_service module
            result = article_service.fetch_and_store_articles(category=category)
            
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(f"Error: {result['message']}", 'error')
        
        elif action == 'search_articles':
            query = request.form.get('query')
            
            if not query or len(query) < 3:
                flash('Please enter a search query of at least 3 characters', 'error')
            else:
                # Use the article_service search method
                articles, count, pages = article_service.search_articles(query)
                if count > 0:
                    flash(f'Found {count} articles matching your search', 'success')
                else:
                    flash('No articles found for your search query', 'error')
    
    # Get statistics
    stats = {
        'total_articles': db.articles.count_documents({}),
        'technology': db.articles.count_documents({'categories': 'technology'}),
        'business': db.articles.count_documents({'categories': 'business'}),
        'health': db.articles.count_documents({'categories': 'health'}),
        'science': db.articles.count_documents({'categories': 'science'}),
        'sports': db.articles.count_documents({'categories': 'sports'}),
        'general': db.articles.count_documents({'categories': 'general'}),
    }
    
    return render_template('admin/fetch_articles.html', stats=stats, user=user_data)

@app.route('/admin/refresh-articles')
@login_required
def admin_refresh_articles():
    """Admin endpoint to manually refresh articles"""
    # Check if admin
    user_email = session.get('user_email')
    success, user = find_user_by_email(user_email) if user_email else (False, None)
    
    if not user_email or not success or not user.get('is_admin', False):
        flash('Unauthorized', 'error')
        return redirect(url_for('news_home'))
    
    # Fetch articles for key categories
    categories = ['business', 'technology', 'health', 'entertainment']
    results = {}
    
    for category in categories:
        try:
            result = article_service.fetch_and_store_articles(category=category, count=10)
            results[category] = result
        except Exception as e:
            app.logger.error(f"Error fetching {category} articles: {str(e)}")
            results[category] = {'success': False, 'message': str(e)}
    
    return render_template('admin_fetch_result.html', results=results)

# First implementation - rename to toggle_bookmark_simple
@app.route('/bookmark', methods=['POST'])
@login_required
def toggle_bookmark_simple():
    user_id = session.get("user_id")
    article_id = request.json.get('article_id')
    
    if not article_id:
        return jsonify({"success": False, "message": "No article specified"}), 400
    
    try:
        # Check if already bookmarked
        existing = db.bookmarks.find_one({
            "user_id": user_id,
            "article_id": article_id
        })
        
        if existing:
            # Remove bookmark
            db.bookmarks.delete_one({
                "user_id": user_id,
                "article_id": article_id
            })
            return jsonify({"success": True, "action": "removed"})
        else:
            # Add bookmark
            db.bookmarks.insert_one({
                "user_id": user_id,
                "article_id": article_id,
                "created_at": datetime.now(timezone.utc),
            })
            return jsonify({"success": True, "action": "added"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update-reading-time', methods=['POST'])
@login_required
def update_reading_time():
    user_id = session.get("user_id")
    article_id = request.json.get('article_id')
    duration = request.json.get('duration')  # in seconds
    
    if not article_id or not duration:
        return jsonify({"success": False}), 400
    
    try:
        db.reading_history.update_one(
            {
                "user_id": user_id,
                "article_id": article_id,
                "read_at": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            },
            {"$set": {"read_duration": duration}}
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    user_id = session.get("user_id")
    
    try:
        result = db.reading_history.delete_many({"user_id": user_id})
        return jsonify({"success": True, "count": result.deleted_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/bookmarks')
@login_required
def bookmarks():
    """Display user's bookmarked articles."""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    try:
        # Get all user's bookmarks trying multiple ways
        user_bookmarks = list(db.bookmarks.find({
            "$or": [
                {"user_id": user_id},
                {"user_email": user_email}
            ]
        }))
        
        bookmarked_articles = []
        for bookmark in user_bookmarks:
            article_id = None
            
            # Try getting the article_id in different ways
            if 'article_id' in bookmark:
                if isinstance(bookmark['article_id'], ObjectId):
                    article_id = bookmark['article_id']
                else:
                    try:
                        article_id = ObjectId(bookmark['article_id'])
                    except:
                        pass
            
            if not article_id and 'article_id_str' in bookmark:
                try:
                    article_id = ObjectId(bookmark['article_id_str'])
                except:
                    pass
                    
            if article_id:
                article = db.articles.find_one({"_id": article_id})
                if article:
                    # Add bookmark metadata to article
                    article['bookmarked_at'] = bookmark.get('created_at')
                    article['notes'] = bookmark.get('notes', '')
                    bookmarked_articles.append(article)
        
        return render_template('bookmarks.html', bookmarked_articles=bookmarked_articles)
    
    except Exception as e:
        print(f"Error loading bookmarks: {str(e)}")
        flash('Error loading bookmarks', 'error')
        return redirect(url_for('dashboard'))

# Second implementation - rename to toggle_bookmark_by_id
@app.route("/bookmark/<article_id>", methods=["POST"])
@login_required
def toggle_bookmark_by_id(article_id):
    user_id = session.get("user_id")
    
    try:
        # Check if already bookmarked
        existing_bookmark = db.bookmarks.find_one({
            "user_id": user_id,
            "article_id": article_id
        })
        
        if existing_bookmark:
            # Remove bookmark
            db.bookmarks.delete_one({"_id": existing_bookmark["_id"]})
            return jsonify({"status": "success", "action": "removed"})
        else:
            # Add bookmark
            article = db.articles.find_one({"_id": ObjectId(article_id)})
            if not article:
                return jsonify({"status": "error", "message": "Article not found"})
                
            db.bookmarks.insert_one({
                "user_id": user_id,
                "article_id": article_id,
                "title": article["title"],
                "created_at": datetime.utcnow(),
                "tags": [],
                "notes": ""
            })
            return jsonify({"status": "success", "action": "added"})
            
    except Exception as e:
        print(f"Error toggling bookmark: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/bookmark/<bookmark_id>/update", methods=["POST"])
@login_required
def update_bookmark_details(bookmark_id):
    user_id = session.get("user_id")
    
    try:
        data = request.json
        tags = data.get("tags", [])
        notes = data.get("notes", "")
        
        # Verify bookmark belongs to user
        bookmark = db.bookmarks.find_one({
            "_id": ObjectId(bookmark_id),
            "user_id": user_id
        })
        
        if not bookmark:
            return jsonify({"status": "error", "message": "Bookmark not found"})
        
        # Update bookmark
        db.bookmarks.update_one(
            {"_id": ObjectId(bookmark_id)},
            {"$set": {
                "tags": tags,
                "notes": notes
            }}
        )
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"Error updating bookmark: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/bookmark/toggle', methods=['POST'])
@login_required
def toggle_bookmark():
    """Toggle bookmark status for an article"""
    try:
        # Debug logging
        print("Bookmark toggle API called")
        
        # Try different ways to get the data
        data = None
        article_id = None
        
        # Method 1: Standard JSON
        if request.is_json:
            data = request.get_json()
            article_id = data.get('article_id')
            print(f"Got article_id from JSON: {article_id}")
            
        # Method 2: Form data
        if not article_id and request.form:
            article_id = request.form.get('article_id')
            print(f"Got article_id from form: {article_id}")
            
        # Method 3: Raw data
        if not article_id:
            try:
                raw_data = request.get_data(as_text=True)
                if raw_data:
                    data = json.loads(raw_data)
                    article_id = data.get('article_id')
                    print(f"Got article_id from raw data: {article_id}")
            except:
                pass
        
        if not article_id:
            print("No article_id found in request")
            return jsonify({"error": "Article ID is required"}), 400
            
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            print("No user_id in session")
            return jsonify({"error": "User not authenticated"}), 401
        
        print(f"Processing bookmark toggle for user {user_id} and article {article_id}")
            
        # Convert article_id to ObjectId
        try:
            article_obj_id = ObjectId(article_id)
        except Exception as e:
            print(f"Invalid ObjectId format: {article_id}, Error: {str(e)}")
            return jsonify({"error": f"Invalid article ID format: {str(e)}"}), 400
        
        # Check if bookmark exists - use both string and ObjectId comparison
        existing_bookmark = db.bookmarks.find_one({
            "user_id": user_id,
            "$or": [
                {"article_id": article_obj_id},
                {"article_id": article_id}
            ]
        })
        
        if existing_bookmark:
            # Remove bookmark
            print(f"Removing bookmark {existing_bookmark['_id']}")
            db.bookmarks.delete_one({"_id": existing_bookmark["_id"]})
            return jsonify({"is_bookmarked": False})
        else:
            # Add bookmark
            print(f"Adding new bookmark")
            result = db.bookmarks.insert_one({
                "user_id": user_id,
                "article_id": article_obj_id,
                "created_at": datetime.utcnow()
            })
            print(f"Inserted bookmark with ID: {result.inserted_id}")
            return jsonify({"is_bookmarked": True})
            
    except Exception as e:
        print(f"Error in toggle_bookmark: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get and save notes for a bookmark
@app.route('/api/bookmark/note', methods=['GET', 'POST'])
@login_required
def bookmark_note():
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    
    if request.method == 'GET':
        article_id_str = request.args.get("article_id")
        if not article_id_str:
            return jsonify({"error": "Article ID is required"}), 400
            
        try:
            # Try to convert to ObjectId
            article_id = ObjectId(article_id_str)
            
            # Look up bookmark by user_id first
            bookmark = db.bookmarks.find_one({
                "user_id": user_id,
                "article_id": article_id
            })
            
            # If not found, try by email
            if not bookmark and user_email:
                bookmark = db.bookmarks.find_one({
                    "user_email": user_email,
                    "article_id": article_id_str
                })
            
            if bookmark:
                return jsonify({"note": bookmark.get("notes", "")})
            else:
                return jsonify({"note": ""})
        except Exception as e:
            print(f"Error fetching note: {e}")
            return jsonify({"error": f"Failed to fetch note: {str(e)}"}), 500
    
    elif request.method == 'POST':
        data = request.get_json()
        article_id_str = data.get("article_id")
        note = data.get("note")
        
        if not article_id_str:
            return jsonify({"error": "Article ID is required"}), 400
        
        try:
            # Convert string ID to ObjectId
            article_id = ObjectId(article_id_str)
            
            # Try to find bookmark first
            bookmark = db.bookmarks.find_one({
                "user_id": user_id,
                "article_id": article_id
            })
            
            # If not found, try by email
            if not bookmark and user_email:
                bookmark = db.bookmarks.find_one({
                    "user_email": user_email,
                    "article_id": article_id_str
                })
                
            # If bookmark exists, update it
            if bookmark:
                result = db.bookmarks.update_one(
                    {"_id": bookmark["_id"]},
                    {"$set": {"notes": note}}
                )
            else:
                # Create new bookmark with note
                result = db.bookmarks.insert_one({
                    "user_id": user_id,
                    "user_email": user_email,
                    "article_id": article_id,
                    "article_id_str": article_id_str,
                    "created_at": datetime.now(),
                    "notes": note,
                    "tags": []
                })
            
            return jsonify({"message": "Note saved successfully"})
        except Exception as e:
            print(f"Error saving note: {e}")
            return jsonify({"error": f"Failed to save note: {str(e)}"}), 500

# Update tags for a bookmark
@app.route('/api/bookmark/tags', methods=['POST'])
@login_required
def update_bookmark_tags():
    user_id = session.get("user_id")
    data = request.get_json()
    article_id = data.get("article_id")
    tags = data.get("tags")
    
    if not article_id:
        return jsonify({"error": "Article ID is required"}), 400
    
    if not isinstance(tags, list):
        return jsonify({"error": "Tags must be an array"}), 400
    
    try:
        # Update the bookmark with the tags
        result = db.bookmarks.update_one(
            {"user_id": user_id, "article_id": ObjectId(article_id)},
            {"$set": {"tags": tags}},
            upsert=True
        )
        
        if result.modified_count > 0 or result.upserted_id:
            return jsonify({"message": "Tags updated successfully"})
        else:
            return jsonify({"message": "No changes made to tags"})
    except Exception as e:
        print(f"Error updating tags: {e}")
        return jsonify({"error": "Failed to update tags"}), 500

@app.route('/topic/<topic_name>')
@login_required
def topic(topic_name):
    try:
        articles = list(db.articles.find({"category": topic_name}).sort("published_at", -1).limit(20))
        return render_template('topic.html', topic=topic_name, articles=articles)
    except Exception as e:
        flash("Error loading topic", "error")
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    # flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """User profile page"""
    try:
        user_id = session.get('user_id')
        user = db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('dashboard'))
            
        # Get user's bookmarks
        bookmarks = list(db.bookmarks.find({
            "$or": [
                {"user_id": user_id},
                {"user_email": user.get('email')}
            ]
        }))
        
        # Make sure user preferences exist
        if 'preferences' not in user:
            user['preferences'] = []
            
        return render_template('profile.html', user=user, bookmarks=bookmarks)
        
    except Exception as e:
        app.logger.error(f"Error fetching profile: {str(e)}")
        print(f"Error fetching profile: {str(e)}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user_id = session.get("user_id")
    
    try:
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user_data:
            flash("User not found.", "error")
            return redirect(url_for("dashboard"))
        
        if request.method == "POST":
            # Get form data
            name = request.form.get("name")
            bio = request.form.get("bio")
            
            # Handle profile image upload
            profile_pic_url = user_data.get("profile_pic")
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    profile_pic_url = f'/static/uploads/{filename}'
            
            # Update user profile in database
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "name": name,
                    "bio": bio,
                    "profile_pic": profile_pic_url
                }}
            )
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))
        
        return render_template("edit_profile.html", user=user_data)
        
    except Exception as e:
        print(f"Error with profile edit: {e}")
        flash("Error updating profile.", "error")
        return redirect(url_for("profile"))

@app.route('/update-account', methods=['POST'])
@login_required
def update_account():
    """Update user account information"""
    try:
        user_id = session.get('user_id')
        user = db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('profile'))
        
        # Get form data
        name = request.form.get('name')
        bio = request.form.get('bio', '')
        preferences = request.form.getlist('preferences')
        
        # Update user information
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'name': name,
                'bio': bio,
                'preferences': preferences
            }}
        )
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        app.logger.error(f"Error updating account: {str(e)}")
        flash('An error occurred while updating your profile', 'error')
        return redirect(url_for('profile'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        user_id = session.get('user_id')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not all([current_password, new_password, confirm_password]):
            flash('All password fields are required', 'error')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile'))
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(url_for('profile'))
        
        # Verify current password
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('profile'))
        
        if not check_password_hash(user.get('password', ''), current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('profile'))
        
        # Update to new password
        hashed_password = generate_password_hash(new_password)
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': hashed_password}}
        )
        
        flash('Password updated successfully', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        app.logger.error(f"Error changing password: {str(e)}")
        flash('An error occurred while changing your password', 'error')
        return redirect(url_for('profile'))

# Add this route near your other API routes
@app.route('/api/articles/recommended')
def recommended_articles():
    """Get recommended articles based on categories or article content"""
    article_id = request.args.get('article_id')
    categories_str = request.args.get('categories', '')
    
    try:
        # Parse categories
        categories = categories_str.split(',') if categories_str else []
        categories = [c.strip() for c in categories if c.strip()]
        
        # Default to general if no categories
        if not categories:
            categories = ['general']
            
        # Find articles with matching categories
        # Exclude the current article
        query = {
            "_id": {"$ne": ObjectId(article_id) if article_id else None},
            "$or": [{"categories": {"$in": categories}}]
        }
        
        # Get up to 6 recommended articles
        recommended = list(db.articles.find(query).sort("published_at", -1).limit(6))
        
        # Convert ObjectId to string for JSON serialization
        for article in recommended:
            article["_id"] = str(article["_id"])
        
        return jsonify({"articles": recommended})
        
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/article/view', methods=['POST'])
def record_article_view():
    """Record that an article was viewed"""
    try:
        # Get data using our helper function
        data = get_json_data()
        article_id = data.get('article_id')
        
        app.logger.info(f"Recording view for article: {article_id}")
        
        if not article_id or article_id == 'undefined' or article_id == 'null':
            app.logger.warning("Missing or invalid article ID in view request")
            return jsonify({"error": "Valid article ID is required"}), 400
        
        try:
            article_obj_id = ObjectId(article_id)
        except Exception as e:
            app.logger.error(f"Invalid ObjectId format: {article_id}: {str(e)}")
            return jsonify({"error": "Invalid article ID format"}), 400
            
        # Record the view
        user_id = session.get('user_id') if 'user_id' in session else None
        
        # Increment view count for the article regardless of login status
        db.articles.update_one(
            {"_id": article_obj_id},
            {"$inc": {"views": 1}}
        )
        
        if user_id:
            # Record in reading history for logged in users
            db.reading_history.insert_one({
                "user_id": user_id,
                "article_id": article_obj_id,
                "read_at": datetime.utcnow()
            })
        
        return jsonify({"success": True})
        
    except Exception as e:
        app.logger.error(f"Error recording article view: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles/category/<category>')
def get_category_articles(category):
    """API endpoint to get articles for a specific category"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('size', 4))
        
        # Get articles for the requested category
        articles_data = article_service.get_articles(category=category, page=page, page_size=page_size)
        articles = articles_data.get('articles', [])
        
        # Convert ObjectId to string for JSON serialization
        for article in articles:
            if '_id' in article:
                article['_id'] = str(article['_id'])
            if 'published_at' in article and not isinstance(article['published_at'], str):
                try:
                    article['published_at'] = article['published_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                except:
                    article['published_at'] = str(article['published_at'])
        
        return jsonify({
            'articles': articles,
            'total': articles_data.get('total_results', 0)
        })
    except Exception as e:
        app.logger.error(f"Error fetching category articles: {str(e)}")
        return jsonify({'error': 'Failed to load articles', 'articles': []}), 500

@app.route('/api/status')
def api_status():
    """Check API status and cache stats"""
    user_email = session.get('user_email')
    success, user = find_user_by_email(user_email) if user_email else (False, None)
    
    if not user_email or not success or not user.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from services.news_api import article_cache, daily_request_count, MAX_DAILY_REQUESTS
        
        # Get cache stats
        cache_size = len(article_cache)
        cache_keys = list(article_cache.keys())
        
        # Get API usage
        api_usage = {
            'daily_requests': daily_request_count,
            'max_daily': MAX_DAILY_REQUESTS,
            'usage_percentage': (daily_request_count / MAX_DAILY_REQUESTS) * 100 if MAX_DAILY_REQUESTS > 0 else 0
        }
        
        # Get database stats
        db_stats = {
            'articles_count': db.articles.count_documents({}),
            'categories': {
                category: db.articles.count_documents({'categories': category})
                for category in ['business', 'technology', 'entertainment', 'health', 'science', 'sports']
            }
        }
        
        return jsonify({
            'cache': {
                'size': cache_size,
                'keys': cache_keys[:10]  # Show first 10 keys only
            },
            'api': api_usage,
            'database': db_stats
        })
        
    except Exception as e:
        app.logger.error(f"Error getting API status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def preload_categories():
    """Preload categories to populate cache"""
    try:
        app.logger.info("Preloading article categories")
        categories = ['business', 'technology']
        for category in categories:
            try:
                app.logger.info(f"Preloading {category} articles")
                articles_data = article_service.get_articles(category=category, page=1)
                articles_count = len(articles_data.get('articles', []))
                app.logger.info(f"Preloaded {articles_count} {category} articles")
            except Exception as e:
                app.logger.error(f"Error preloading {category} articles: {str(e)}")
    except Exception as e:
        app.logger.error(f"Error in preload_categories: {str(e)}")

def start_app():
    """Start background processes and initialize app components"""
    try:
        app.logger.info("Starting application processes...")
        # Preload categories within app context
        with app.app_context():
            try:
                preload_categories()
            except Exception as e:
                app.logger.error(f"Error preloading categories: {str(e)}")
        
        # Start scheduler in a separate thread
        threading.Thread(target=start_scheduler, daemon=True).start()
        
        app.logger.info("Application initialization complete")
    except Exception as e:
        app.logger.error(f"Error during application startup: {str(e)}")

@app.route('/admin/articles')
def admin_articles():
    """Admin view of all articles for debugging"""
    # Check if admin
    user_email = session.get('user_email')
    success, user = find_user_by_email(user_email) if user_email else (False, None)
    
    if not user_email or not success or not user.get('is_admin', False):
        flash('Unauthorized', 'error')
        return redirect(url_for('news_home'))
    
    # Get all articles
    articles = list(db.articles.find().limit(100))
    
    # Process for display
    for article in articles:
        article['_id'] = str(article['_id'])
        if 'published_at' in article and not isinstance(article['published_at'], str):
            try:
                article['published_at'] = article['published_at'].strftime('%Y-%m-%d %H:%M:%S')
            except:
                article['published_at'] = str(article['published_at'])
    
    return render_template('admin_articles.html', articles=articles)

@app.route('/debug/articles')
def debug_articles():
    """Debug page to see all articles in database"""
    try:
        # Get articles from DB
        articles_cursor = db.articles.find().sort('published_at', -1).limit(100)
        articles = []
        
        for article in articles_cursor:
            # Convert ObjectId to string
            article['_id'] = str(article['_id'])
            
            # Format dates
            if 'published_at' in article and not isinstance(article['published_at'], str):
                article['published_at'] = article['published_at'].strftime('%Y-%m-%d %H:%M:%S')
                
            # Add to list
            articles.append(article)
            
        # Render template
        return render_template('debug_articles.html', articles=articles)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/run-seed')
def run_seed():
    """Run the database seeding process"""
    try:
        from seed_articles import seed_from_sample_data, seed_from_api
        
        # Try API seed first
        api_success = seed_from_api()
        
        # If that fails, use sample data
        if not api_success:
            count = seed_from_sample_data()
            return f"API seeding failed. Added {count} sample articles."
        
        return "Database seeding completed successfully."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/admin/create-sample-article')
@login_required
def create_sample_article():
    """Create a sample article for testing"""
    # Check if user is admin
    user_email = session.get('user_email')
    success, user_data = find_user_by_email(user_email)
    
    if not success or not user_data.get('is_admin', False):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('dashboard'))
    
    # Create a sample article
    sample_article = {
        "_id": ObjectId(),
        "title": "Sample Article: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        "description": "This is a sample article created for testing purposes.",
        "content": """<p>This is a sample article with some formatted content.</p>
        
        <p>It has multiple paragraphs.</p>
        
        <p>The purpose of this article is to test the article display functionality.</p>""",
        "image_url": "https://placehold.co/600x400?text=Sample+Article",
        "url": "https://example.com/sample",
        "source_name": "Syllabuzz Sample",
        "author": "Test User",
        "categories": ["test", "sample"],
        "published_at": datetime.utcnow()
    }
    
    # Insert the article
    article_id = db.articles.insert_one(sample_article).inserted_id
    
    # Redirect to the article page
    flash('Sample article created successfully', 'success')
    return redirect(url_for('article', article_id=str(article_id)))

csrf.exempt(toggle_bookmark)
csrf.exempt(record_article_view)
csrf.exempt(bookmark_note)

if __name__ == '__main__':
    # Start background processes before running the app
    start_app()
    
    # Run the Flask app
    app.run(debug=True, host="192.168.137.235")