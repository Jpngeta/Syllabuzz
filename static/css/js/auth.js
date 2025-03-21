// Authentication related JavaScript functions

// Add Bookmark functionality
function bookmarkArticle(articleId, moduleId = null) {
    const data = {
        article_id: articleId
    };
    
    if (moduleId) {
        data.module_id = moduleId;
    }
    
    fetch('/api/bookmarks/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Article bookmarked successfully!', 'success');
            // Update bookmark button if exists
            const bookmarkBtn = document.querySelector(`.bookmark-btn[data-article-id="${articleId}"]`);
            if (bookmarkBtn) {
                bookmarkBtn.innerHTML = '<i class="fas fa-bookmark"></i>';
                bookmarkBtn.classList.remove('btn-outline-primary');
                bookmarkBtn.classList.add('btn-primary');
                bookmarkBtn.setAttribute('data-bookmarked', 'true');
            }
        } else {
            showToast(data.message || 'This article is already bookmarked', 'info');
        }
    })
    .catch(error => {
        console.error('Error bookmarking article:', error);
        showToast('Failed to bookmark article. Please try again.', 'error');
    });
}

// Remove Bookmark functionality
function removeBookmark(articleId) {
    fetch('/api/bookmarks/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            article_id: articleId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Bookmark removed successfully!', 'success');
            // Update bookmark button if exists
            const bookmarkBtn = document.querySelector(`.bookmark-btn[data-article-id="${articleId}"]`);
            if (bookmarkBtn) {
                bookmarkBtn.innerHTML = '<i class="far fa-bookmark"></i>';
                bookmarkBtn.classList.remove('btn-primary');
                bookmarkBtn.classList.add('btn-outline-primary');
                bookmarkBtn.setAttribute('data-bookmarked', 'false');
            }
        } else {
            showToast(data.message || 'Bookmark not found', 'info');
        }
    })
    .catch(error => {
        console.error('Error removing bookmark:', error);
        showToast('Failed to remove bookmark. Please try again.', 'error');
    });
}

// Toggle bookmark status
function toggleBookmark(articleId, moduleId = null) {
    const bookmarkBtn = document.querySelector(`.bookmark-btn[data-article-id="${articleId}"]`);
    const isBookmarked = bookmarkBtn && bookmarkBtn.getAttribute('data-bookmarked') === 'true';
    
    if (isBookmarked) {
        removeBookmark(articleId);
    } else {
        bookmarkArticle(articleId, moduleId);
    }
}

// Function to determine if user is logged in
function isLoggedIn() {
    // Check for user authentication status
    // This assumes there's a meta tag or some global variable that indicates login status
    return document.body.hasAttribute('data-user-authenticated') || 
           (typeof userAuthenticated !== 'undefined' && userAuthenticated);
}

// Function to prompt login if user is not authenticated
function requireLogin(callback, params = {}) {
    if (isLoggedIn()) {
        // User is logged in, proceed with action
        if (typeof callback === 'function') {
            callback(params);
        }
    } else {
        // User is not logged in, show login prompt
        const loginUrl = `/login?next=${encodeURIComponent(window.location.pathname)}`;
        
        // Using a confirmation dialog
        if (confirm('You need to be logged in to perform this action. Would you like to log in now?')) {
            window.location.href = loginUrl;
        }
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    // Handle bookmark button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('bookmark-btn') || e.target.closest('.bookmark-btn')) {
            e.preventDefault();
            const btn = e.target.classList.contains('bookmark-btn') ? e.target : e.target.closest('.bookmark-btn');
            const articleId = btn.getAttribute('data-article-id');
            const moduleId = btn.getAttribute('data-module-id');
            
            requireLogin(() => toggleBookmark(articleId, moduleId));
        }
    });
    
    // Add bookmark buttons to article cards if they don't exist
    document.querySelectorAll('.article-card').forEach(card => {
        const articleId = card.getAttribute('data-article-id');
        if (articleId && !card.querySelector('.bookmark-btn')) {
            const cardBody = card.querySelector('.card-body');
            const actionButtons = cardBody.querySelector('.card-footer') || cardBody.querySelector('button').parentNode;
            
            const bookmarkBtn = document.createElement('button');
            bookmarkBtn.className = 'btn btn-sm btn-outline-primary bookmark-btn ms-2';
            bookmarkBtn.setAttribute('data-article-id', articleId);
            bookmarkBtn.setAttribute('data-bookmarked', 'false');
            bookmarkBtn.innerHTML = '<i class="far fa-bookmark"></i>';
            
            actionButtons.appendChild(bookmarkBtn);
        }
    });
    
    // Password strength meter for signup form
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        const strengthMeter = document.createElement('div');
        strengthMeter.className = 'progress mt-2';
        strengthMeter.innerHTML = '<div class="progress-bar" role="progressbar" style="width: 0%"></div>';
        passwordInput.parentNode.appendChild(strengthMeter);
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            // Length check
            if (password.length >= 8) strength += 25;
            
            // Uppercase check
            if (/[A-Z]/.test(password)) strength += 25;
            
            // Lowercase check
            if (/[a-z]/.test(password)) strength += 25;
            
            // Number check
            if (/\d/.test(password)) strength += 25;
            
            // Update progress bar
            const progressBar = strengthMeter.querySelector('.progress-bar');
            progressBar.style.width = `${strength}%`;
            
            // Set color based on strength
            if (strength < 50) {
                progressBar.className = 'progress-bar bg-danger';
            } else if (strength < 100) {
                progressBar.className = 'progress-bar bg-warning';
            } else {
                progressBar.className = 'progress-bar bg-success';
            }
        });
    }
});