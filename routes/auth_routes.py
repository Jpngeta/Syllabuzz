# Authentication routes for Syllabuzz
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from bson.objectid import ObjectId

# Import utils
from utils.db_utils import (
    modules_collection, users_collection, bookmarks_collection, tokens_collection, 
    find_user_by_email, find_user_by_username, find_user_by_id, create_user, 
    verify_user, update_user_password, create_token, find_token, mark_token_used,
    update_user_modules, update_user_preferences, bookmark_article, 
    remove_bookmark, get_user_bookmarks
)

from utils.auth_utils import (
    is_valid_email, is_valid_password, hash_password, verify_password,
    generate_verification_token, send_verification_email, send_password_reset_email,
    login_required
)

# Import configuration
from config import TOKEN_EXPIRY_HOURS, PASSWORD_RESET_EXPIRY_HOURS, SESSION_EXPIRY_DAYS

# Create Blueprint
auth = Blueprint('auth', __name__)

# Authentication Routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Find user by username or email
        user = find_user_by_username(username)
        if not user:
            user = find_user_by_email(username)
            
        if not user:
            error = "Invalid username or password"
        elif not user.get('is_verified', False):
            error = "Please verify your email address before logging in"
        elif not verify_password(password, user['password']):
            error = "Invalid username or password"
        else:
            # Set session variables
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['email'] = user['email']
            
            # Set session to permanent if remember me is checked
            if remember:
                session.permanent = True
                
            # Redirect to original page or home
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
    
    return render_template('login.html', error=error, success=success)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup route"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        terms_accepted = 'terms' in request.form
        
        # Validate inputs
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            error = "Username must be 3-20 characters (letters, numbers, underscores)"
        elif not is_valid_email(email):
            error = "Please enter a valid email address"
        elif not is_valid_password(password):
            error = "Password must be at least 8 characters with uppercase, lowercase, and number"
        elif password != confirm_password:
            error = "Passwords do not match"
        elif not terms_accepted:
            error = "You must accept the terms of service"
        else:
            # Check if username or email already exists
            if find_user_by_username(username):
                error = "Username already taken"
            elif find_user_by_email(email):
                error = "Email already registered"
            else:
                # Create the user
                hashed_password = hash_password(password)
                user_id = create_user(username, email, hashed_password)
                
                # Create and send verification token
                token = generate_verification_token()
                expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
                create_token(user_id, 'email_verification', token, expires_at)
                
                if send_verification_email(email, token):
                    success = "Account created! Please check your email to verify your account."
                else:
                    error = "Account created, but we couldn't send the verification email. Please try requesting a new one."
    
    return render_template('signup.html', error=error, success=success)

@auth.route('/verify/<token>')
def verify_email(token):
    """Email verification route"""
    error = None
    success = None
    expired = False
    
    # Find the token
    token_doc = find_token(token, 'email_verification')
    
    if not token_doc:
        error = "Invalid verification link"
    elif token_doc.get('used', False):
        error = "This verification link has already been used"
    elif token_doc['expires_at'] < datetime.now():
        expired = True
    else:
        # Mark the user as verified
        user_id = token_doc['user_id']
        if verify_user(user_id):
            # Mark the token as used
            mark_token_used(token_doc['_id'])
            success = "Your email has been verified successfully. You can now log in."
        else:
            error = "An error occurred while verifying your email. Please try again."
    
    return render_template('verify_email.html', error=error, success=success, expired=expired)

@auth.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend verification email route"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not is_valid_email(email):
            error = "Please enter a valid email address"
        else:
            user = find_user_by_email(email)
            
            if not user:
                error = "No account found with this email address"
            elif user.get('is_verified', False):
                error = "This account is already verified"
            else:
                # Create and send new verification token
                token = generate_verification_token()
                expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
                create_token(user['_id'], 'email_verification', token, expires_at)
                
                if send_verification_email(email, token):
                    success = "Verification email sent! Please check your inbox."
                else:
                    error = "Failed to send verification email. Please try again later."
    
    return render_template('resend_verification.html', error=error, success=success)

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password route"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not is_valid_email(email):
            error = "Please enter a valid email address"
        else:
            user = find_user_by_email(email)
            
            if not user:
                # Don't reveal if the email exists or not for security
                success = "If an account exists with this email, a password reset link has been sent."
            else:
                # Create and send password reset token
                token = generate_verification_token()
                expires_at = datetime.now() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
                create_token(user['_id'], 'password_reset', token, expires_at)
                
                if send_password_reset_email(email, token):
                    success = "If an account exists with this email, a password reset link has been sent."
                else:
                    error = "Failed to send password reset email. Please try again later."
    
    return render_template('forgot_password.html', error=error, success=success)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password route"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    expired = False
    
    # Find the token
    token_doc = find_token(token, 'password_reset')
    
    if not token_doc:
        error = "Invalid password reset link"
        expired = True
    elif token_doc.get('used', False):
        error = "This password reset link has already been used"
        expired = True
    elif token_doc['expires_at'] < datetime.now():
        expired = True
    elif request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not is_valid_password(password):
            error = "Password must be at least 8 characters with uppercase, lowercase, and number"
        elif password != confirm_password:
            error = "Passwords do not match"
        else:
            # Update user's password
            user_id = token_doc['user_id']
            hashed_password = hash_password(password)
            
            if update_user_password(user_id, hashed_password):
                # Mark the token as used
                mark_token_used(token_doc['_id'])
                success = "Your password has been reset successfully. You can now log in with your new password."
            else:
                error = "An error occurred while resetting your password. Please try again."
    
    return render_template('reset_password.html', error=error, success=success, expired=expired, token=token)

@auth.route('/logout')
def logout():
    """User logout route"""
    # Clear session data
    session.clear()
    return redirect(url_for('index'))

# User Profile Routes
@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_id = session.get('user_id')
    user = find_user_by_id(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get modules for preferences
    all_modules = list(modules_collection.find({}))
    for module in all_modules:
        module['_id'] = str(module['_id'])
    
    # Get user modules as strings
    user_modules = [str(module_id) for module_id in user.get('modules', [])]
    
    # Get bookmarks
    bookmarks = get_user_bookmarks(user_id, limit=10)
    
    return render_template(
        'profile.html', 
        user=user, 
        all_modules=all_modules, 
        user_modules=user_modules,
        bookmarks=bookmarks,
        success=request.args.get('success'),
        error=request.args.get('error')
    )

@auth.route('/profile/info', methods=['POST'])
@login_required
def profile_info():
    """Update user profile information"""
    # Currently, this function doesn't allow changing username or email
    # Could be extended to allow other profile fields
    return redirect(url_for('auth.profile', success="Profile information updated"))

@auth.route('/profile/modules', methods=['POST'])
@login_required
def update_modules():
    """Update user module preferences"""
    user_id = session.get('user_id')
    modules = request.form.getlist('modules')
    
    if update_user_modules(user_id, modules):
        return redirect(url_for('auth.profile', success="Module preferences updated"))
    else:
        return redirect(url_for('auth.profile', error="Failed to update module preferences"))

@auth.route('/profile/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user notification preferences"""
    user_id = session.get('user_id')
    
    preferences = {
        'newsletter': 'newsletter' in request.form,
        'email_notifications': 'email_notifications' in request.form
    }
    
    if update_user_preferences(user_id, preferences):
        return redirect(url_for('auth.profile', success="Notification settings updated"))
    else:
        return redirect(url_for('auth.profile', error="Failed to update notification settings"))

@auth.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user_id = session.get('user_id')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    user = find_user_by_id(user_id)
    
    if not user:
        return redirect(url_for('auth.logout'))
    
    if not verify_password(current_password, user['password']):
        return redirect(url_for('auth.profile', error="Current password is incorrect"))
    
    if not is_valid_password(new_password):
        return redirect(url_for('auth.profile', error="New password must be at least 8 characters with uppercase, lowercase, and number"))
    
    if new_password != confirm_password:
        return redirect(url_for('auth.profile', error="New passwords do not match"))
    
    hashed_password = hash_password(new_password)
    
    if update_user_password(user_id, hashed_password):
        return redirect(url_for('auth.profile', success="Password changed successfully"))
    else:
        return redirect(url_for('auth.profile', error="Failed to change password"))