SCRIPTS
delete_low_relevance_articles.py
# Basic usage - delete articles with relevance below 0.1
python delete_low_relevance_articles.py

# Dry run first to see what would be deleted
python delete_low_relevance_articles.py --dry-run

# Use a different threshold
python delete_low_relevance_articles.py --threshold 0.2

# Only process articles from specific categories
python delete_low_relevance_articles.py --categories technology science

# Only process articles from the last 30 days
python delete_low_relevance_articles.py --days 30