document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            
            // Save preference to localStorage
            if (document.documentElement.classList.contains('dark')) {
                localStorage.theme = 'dark';
            } else {
                localStorage.theme = 'light';
            }
        });
    }
    
    // Check for saved theme preference
    if (localStorage.theme === 'dark' || 
        (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    
    // Mobile navigation toggle
    const mobileNavToggle = document.getElementById('mobile-nav-toggle');
    if (mobileNavToggle) {
        mobileNavToggle.addEventListener('click', function() {
            const nav = document.querySelector('nav');
            nav.classList.toggle('hidden');
            
            // Add fullscreen overlay effect when nav is open
            if (!nav.classList.contains('hidden')) {
                nav.classList.add('fixed', 'inset-0', 'z-40');
            } else {
                nav.classList.remove('fixed', 'inset-0', 'z-40');
            }
        });
    }
    
    // Bookmark filtering
    const filterButtons = document.querySelectorAll('.filter-btn');
    const bookmarkCards = document.querySelectorAll('.bookmark-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button style
            filterButtons.forEach(btn => {
                btn.classList.remove('bg-blue-500', 'text-white');
                btn.classList.add('bg-gray-200', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-200');
            });
            
            this.classList.remove('bg-gray-200', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-200');
            this.classList.add('bg-blue-500', 'text-white');
            
            // Filter bookmarks
            bookmarkCards.forEach(card => {
                if (filter === 'all') {
                    card.classList.remove('hidden');
                } else {
                    const categories = card.getAttribute('data-categories').split(',');
                    if (categories.includes(filter)) {
                        card.classList.remove('hidden');
                    } else {
                        card.classList.add('hidden');
                    }
                }
            });
        });
    });
    
    // Handle bookmark toggling
    const bookmarkButtons = document.querySelectorAll('.bookmark-btn');
    bookmarkButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-id');
            toggleBookmark(articleId, this);
        });
    });
    
    // Handle bookmark removal from bookmark page
    const removeButtons = document.querySelectorAll('.remove-bookmark');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-id');
            if (confirm('Are you sure you want to remove this bookmark?')) {
                removeBookmark(articleId, this.closest('.bookmark-card'));
            }
        });
    });
    
    // Handle note adding
    const addNoteButtons = document.querySelectorAll('.add-note');
    const noteModal = document.getElementById('note-modal');
    const closeModalButton = document.getElementById('close-modal');
    const saveNoteButton = document.getElementById('save-note');
    const noteContent = document.getElementById('note-content');
    let currentArticleId = null;
    
    if (addNoteButtons.length > 0 && noteModal) {
        addNoteButtons.forEach(button => {
            button.addEventListener('click', function() {
                currentArticleId = this.getAttribute('data-id');
                noteContent.value = '';
                noteModal.classList.remove('hidden');
            });
        });
        
        closeModalButton.addEventListener('click', function() {
            noteModal.classList.add('hidden');
        });
        
        noteModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
        
        saveNoteButton.addEventListener('click', function() {
            if (currentArticleId) {
                saveNote(currentArticleId, noteContent.value);
            }
        });
    }
    
    // View notes functionality
    const viewNotesButtons = document.querySelectorAll('.view-notes');
    if (viewNotesButtons.length > 0 && noteModal) {
        viewNotesButtons.forEach(button => {
            button.addEventListener('click', function() {
                const articleId = this.getAttribute('data-id');
                viewNotes(articleId);
            });
        });
    }
    
    // Functions to interact with the server
    function toggleBookmark(articleId, buttonElement) {
        fetch('/api/bookmark/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ article_id: articleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert('Error toggling bookmark: ' + data.error);
                return;
            }
            
            // Update button appearance
            if (buttonElement) {
                if (data.is_bookmarked) {
                    buttonElement.classList.add('bookmarked');
                    buttonElement.innerHTML = '<i class="fas fa-bookmark"></i>';
                } else {
                    buttonElement.classList.remove('bookmarked');
                    buttonElement.innerHTML = '<i class="far fa-bookmark"></i>';
                }
            }
        })
        .catch(error => {
            console.error('Network error:', error);
            alert('Network error when toggling bookmark');
        });
    }
    
    function removeBookmark(articleId, cardElement) {
        fetch('/api/bookmark/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ article_id: articleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert('Error removing bookmark: ' + data.error);
                return;
            }
            
            if (!data.is_bookmarked && cardElement) {
                // Remove card with animation
                cardElement.style.opacity = '0';
                setTimeout(() => {
                    cardElement.remove();
                    
                    // Check if there are any bookmarks left
                    if (document.querySelectorAll('.bookmark-card').length === 0) {
                        location.reload(); // Reload to show empty state
                    }
                }, 300);
            }
        })
        .catch(error => {
            console.error('Network error:', error);
            alert('Network error when removing bookmark');
        });
    }
    
    function saveNote(articleId, note) {
        fetch('/api/bookmark/note', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ 
                article_id: articleId,
                note: note
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error saving note: ' + data.error);
                return;
            }
            
            noteModal.classList.add('hidden');
            alert('Note saved successfully!');
            
            // Reload the page to show updated notes
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving the note');
        });
    }
    
    function viewNotes(articleId) {
        fetch(`/api/bookmark/note?article_id=${articleId}`, {
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error retrieving notes: ' + data.error);
                return;
            }
            
            if (data.note) {
                // Open modal with existing notes
                currentArticleId = articleId;
                noteContent.value = data.note;
                noteModal.classList.remove('hidden');
            } else {
                alert('No notes found for this article.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while retrieving notes');
        });
    }
    
    // Helper function to get CSRF token
    function getCsrfToken() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
    }
});

// Add this script to your base.html or articles.html template
document.addEventListener('DOMContentLoaded', function() {
    // Fix bookmark toggle buttons
    document.querySelectorAll('.bookmark-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const articleId = this.getAttribute('data-id');
            
            // Check if we have a valid article ID
            if (!articleId || articleId === 'undefined' || articleId === 'null') {
                console.error('Invalid article ID for bookmark');
                
                // Show feedback to user
                const notification = document.createElement('div');
                notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50';
                notification.textContent = 'Error: Cannot bookmark article with missing ID';
                document.body.appendChild(notification);
                
                // Remove notification after 3 seconds
                setTimeout(() => {
                    notification.remove();
                }, 3000);
                
                return;
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            // Toggle bookmark
            fetch('/api/bookmark/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || ''
                },
                body: JSON.stringify({ article_id: articleId })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Bookmark operation failed');
                }
                return response.json();
            })
            .then(data => {
                // Update button appearance based on bookmark status
                if (data.is_bookmarked) {
                    this.innerHTML = '<i class="fas fa-bookmark text-blue-500"></i>';
                    this.classList.add('bookmarked');
                } else {
                    this.innerHTML = '<i class="far fa-bookmark"></i>';
                    this.classList.remove('bookmarked');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update bookmark');
            });
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Handle bookmark button clicks
    document.querySelectorAll('.bookmark-btn, #bookmark-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-id');
            
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            console.log('Toggling bookmark for article:', articleId);
            
            // Send request to toggle bookmark
            fetch('/api/bookmark/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || ''
                },
                body: JSON.stringify({ article_id: articleId })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || 'Failed to update bookmark');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Bookmark updated:', data);
                
                // Update button appearance
                if (data.is_bookmarked) {
                    this.innerHTML = '<i class="fas fa-bookmark text-blue-500"></i>';
                    this.classList.add('bookmarked');
                    
                    // Show success message
                    showNotification('Article bookmarked', 'success');
                } else {
                    this.innerHTML = '<i class="far fa-bookmark"></i>';
                    this.classList.remove('bookmarked');
                    
                    // Show success message
                    showNotification('Bookmark removed', 'info');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error: ' + error.message, 'error');
            });
        });
    });
    
    // Helper function to show notifications
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-4 py-2 rounded shadow-lg z-50 ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});
</script>