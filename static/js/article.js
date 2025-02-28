document.addEventListener('DOMContentLoaded', function() {
    const articleId = document.getElementById('article-container').dataset.id;
    let readingTime = 0;
    let readingInterval;
    
    // Start tracking reading time
    readingInterval = setInterval(() => {
        // Only increment if the page is visible
        if (!document.hidden) {
            readingTime += 1;
            
            // Update server every 10 seconds
            if (readingTime % 10 === 0) {
                updateReadingTime(articleId, readingTime);
            }
        }
    }, 1000);
    
    // Final update when leaving the page
    window.addEventListener('beforeunload', function() {
        updateReadingTime(articleId, readingTime);
        clearInterval(readingInterval);
    });
    
    // Toggle bookmark button
    const bookmarkButton = document.getElementById('bookmark-button');
    if (bookmarkButton) {
        bookmarkButton.addEventListener('click', function() {
            toggleBookmark(articleId, bookmarkButton);
        });
    }
});

function updateReadingTime(articleId, duration) {
    fetch('/update-reading-time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            article_id: articleId,
            duration: duration
        }),
    })
    .catch(error => console.error('Error updating reading time:', error));
}

function toggleBookmark(articleId, button) {
    fetch('/bookmark', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_id: articleId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            
            if (data.action === 'added') {
                icon.classList.remove('far');
                icon.classList.add('fas');
                showToast('Article bookmarked!');
            } else {
                icon.classList.remove('fas');
                icon.classList.add('far');
                showToast('Bookmark removed!');
            }
        }
    })
    .catch(error => {
        showToast('Error updating bookmark', true);
        console.error('Error:', error);
    });
}