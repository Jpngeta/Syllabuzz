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
    
    // Reading trends chart
    const ctx = document.getElementById('readingChart');
    if (ctx) {
        // Fetch reading history data from API
        fetch('/api/reading/stats')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        datasets: [{
                            label: 'Articles Read',
                            data: data.values || [3, 1, 4, 2, 5, 2, 3],
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    display: true,
                                    color: 'rgba(0, 0, 0, 0.05)'
                                },
                                ticks: {
                                    precision: 0
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error fetching reading stats:', error);
                
                // Fallback to dummy data if API fails
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        datasets: [{
                            label: 'Articles Read',
                            data: [3, 1, 4, 2, 5, 2, 3],
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    display: true,
                                    color: 'rgba(0, 0, 0, 0.05)'
                                },
                                ticks: {
                                    precision: 0
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            });
    }
    
    // Bookmark toggle functionality in reading history list
    const bookmarkButtons = document.querySelectorAll('.bookmark-toggle');
    bookmarkButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const articleId = this.getAttribute('data-id');
            
            try {
                const response = await fetch('/api/bookmark/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ article_id: articleId })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Update the icon based on bookmark status
                    if (data.is_bookmarked) {
                        this.innerHTML = '<i class="fas fa-bookmark fa-lg"></i>';
                    } else {
                        this.innerHTML = '<i class="far fa-bookmark fa-lg"></i>';
                    }
                } else {
                    console.error('Failed to toggle bookmark');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
    
    // Clear reading history
    const clearHistoryButton = document.querySelector('button.bg-red-500');
    if (clearHistoryButton) {
        clearHistoryButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear your reading history?')) {
                fetch('/clear-history', {
                    method: 'POST',
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast('History cleared!');
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                })
                .catch(error => {
                    showToast('Error clearing history', true);
                    console.error('Error:', error);
                });
            }
        });
    }
    
    // Topic tags click handlers
    const topicTags = document.querySelectorAll('.flex-wrap .px-3.py-1');
    topicTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const topic = this.textContent.trim();
            window.location.href = `/topic/${topic}`;
        });
    });
});

// Toast notification function
function showToast(message, isError = false) {
    // Create toast element if it doesn't exist
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg text-white z-50 transition-opacity duration-300';
        document.body.appendChild(toast);
    }
    
    // Set toast style based on type
    if (isError) {
        toast.className = toast.className.replace(/bg-[^\s]+/, 'bg-red-500');
        if (!toast.className.includes('bg-red-500')) {
            toast.className += ' bg-red-500';
        }
    } else {
        toast.className = toast.className.replace(/bg-[^\s]+/, 'bg-green-500');
        if (!toast.className.includes('bg-green-500')) {
            toast.className += ' bg-green-500';
        }
    }
    
    // Set message and show
    toast.textContent = message;
    toast.style.opacity = '1';
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 3000);
}

// Replace with defensive code:
function createArticleCard(article) {
    const articleId = article._id || '';
    const isValidId = articleId && articleId !== 'undefined' && articleId !== 'null';
    
    const titleElement = isValidId ?
        `<a href="/article/${articleId}" class="hover:text-blue-500">
            ${article.title || 'Untitled Article'}
         </a>` :
        `<span class="text-gray-700 dark:text-gray-300">
            ${article.title || 'Untitled Article'} (ID missing)
         </span>`;
         
    // Rest of your card creation code...
}