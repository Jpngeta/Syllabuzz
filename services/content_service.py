import requests
from datetime import datetime
import feedparser
import arxiv
from services.embedding_service import EmbeddingService
import logging
from services import article_service

class ContentService:
    def __init__(self, db, news_api_key, embedding_service=None):
        self.db = db
        self.news_api_key = news_api_key
        self.embedding_service = embedding_service or EmbeddingService()
        
    def fetch_news_articles(self, category=None, query=None, count=10):
        """Fetch articles from News API"""
        url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'apiKey': self.news_api_key,
            'language': 'en',
            'pageSize': count
        }
        
        if category:
            params['category'] = category
            
        if query:
            params['q'] = query
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []
            
        articles = response.json().get('articles', [])
        return self._process_news_articles(articles)
        
    def fetch_arxiv_articles(self, query, count=10):
        """Fetch articles from arXiv"""
        search = arxiv.Search(
            query=query,
            max_results=count,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = list(search.results())
        return self._process_arxiv_articles(results)
        
    def _process_news_articles(self, articles):
        """Process and store news API articles"""
        processed_articles = []
        
        for article in articles:
            # Check if article already exists
            existing = self.db.articles.find_one({'url': article['url']})
            if existing:
                processed_articles.append(existing)
                continue
                
            # Create article document
            article_doc = {
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'summary': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'author': article.get('author', ''),
                'published_date': article.get('publishedAt', datetime.now()),
                'image_url': article.get('urlToImage', ''),
                'categories': [article.get('category', 'general')],
                'created_at': datetime.now(),
                'view_count': 0,
                'bookmark_count': 0
            }
            
            # Generate embedding
            text = article_doc['title'] + '. ' + article_doc['content']
            embedding = self.embedding_service.generate_embedding(text)
            article_doc['vector_embedding'] = embedding.tolist()
            
            # Insert into database
            article_id = self.db.articles.insert_one(article_doc).inserted_id
            article_doc['_id'] = article_id
            processed_articles.append(article_doc)
            
        return processed_articles
        
    def _process_arxiv_articles(self, articles):
        """Process and store arXiv articles"""
        processed_articles = []
        
        for article in articles:
            # Check if article already exists
            existing = self.db.articles.find_one({'url': article.entry_id})
            if existing:
                processed_articles.append(existing)
                continue
                
            # Create article document
            article_doc = {
                'title': article.title,
                'content': article.summary,
                'summary': article.summary[:300] + '...' if len(article.summary) > 300 else article.summary,
                'url': article.entry_id,
                'source': 'arXiv',
                'author': ', '.join(author.name for author in article.authors),
                'published_date': article.published,
                'image_url': '',
                'categories': [category.replace('cs.', 'CS: ') for category in article.categories],
                'created_at': datetime.now(),
                'view_count': 0,
                'bookmark_count': 0
            }
            
            # Generate embedding
            text = article_doc['title'] + '. ' + article_doc['content']
            embedding = self.embedding_service.generate_embedding(text)
            article_doc['vector_embedding'] = embedding.tolist()
            
            # Insert into database
            article_id = self.db.articles.insert_one(article_doc).inserted_id
            article_doc['_id'] = article_id
            processed_articles.append(article_doc)
            
        return processed_articles
        
    def generate_module_articles_relevance(self, module_id):
        """Generate relevance scores between a module and articles"""
        # Get module
        module = self.db.modules.find_one({'_id': ObjectId(module_id)})
        if not module:
            return
            
        # Get module embedding
        if 'vector_embedding' not in module:
            module_embedding = self.embedding_service.get_module_embedding(module)
            self.db.modules.update_one(
                {'_id': module['_id']},
                {'$set': {'vector_embedding': module_embedding.tolist()}}
            )
        else:
            module_embedding = np.array(module['vector_embedding'])
            
        # Get articles with embeddings
        articles = list(self.db.articles.find({'vector_embedding': {'$exists': True}}))
        
        # Calculate relevance scores
        for article in articles:
            article_embedding = np.array(article['vector_embedding'])
            relevance = self.embedding_service.calculate_similarity(
                module_embedding, article_embedding)
                
            # Store relevance score
            self.db.module_article_relevance.update_one(
                {
                    'module_id': module['_id'],
                    'article_id': article['_id']
                },
                {
                    '$set': {
                        'relevance_score': float(relevance),
                        'created_at': datetime.now()
                    }
                },
                upsert=True
            )


logger = logging.getLogger(__name__)

def preload_categories():
    """Preload categories to populate cache"""
    try:
        logger.info("Preloading article categories")
        categories = ['business', 'technology']
        for category in categories:
            try:
                logger.info(f"Preloading {category} articles")
                articles_data = article_service.get_articles(category=category, page=1)
                articles_count = len(articles_data.get('articles', []))
                logger.info(f"Preloaded {articles_count} {category} articles")
            except Exception as e:
                logger.error(f"Error preloading {category} articles: {str(e)}")
    except Exception as e:
        logger.error(f"Error in preload_categories: {str(e)}")