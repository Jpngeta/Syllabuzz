# arXiv API integration
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bson.objectid import ObjectId
from utils.db_utils import articles_collection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArxivService:
    def __init__(self):
        """Initialize the arXiv service"""
        self.base_url = "http://export.arxiv.org/api/query"
        logger.info("Initialized arXiv service")

    def fetch_papers(self, search_query="cs", max_results=20, start=0, sort_by="submittedDate"):
        """Fetch papers from arXiv API
        
        Args:
            search_query: Search query string (can include categories like 'cs.AI')
            max_results: Maximum number of results to return
            start: Start index for results
            sort_by: Sort order ('submittedDate', 'relevance', 'lastUpdatedDate')
            
        Returns:
            List of paper dictionaries
        """
        try:
            # Prepare parameters
            params = {
                "search_query": search_query,
                "start": start,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": "descending"
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params)
            
            # Check for successful response
            if response.status_code != 200:
                logger.error(f"arXiv API error: {response.status_code}, {response.text}")
                return []
                
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract papers from response
            papers = []
            namespace = {"atom": "http://www.w3.org/2005/Atom", 
                         "arxiv": "http://arxiv.org/schemas/atom"}
            
            for entry in root.findall("atom:entry", namespace):
                # Extract basic paper information
                title = entry.find("atom:title", namespace).text.strip()
                summary = entry.find("atom:summary", namespace).text.strip()
                
                # Extract authors
                authors = []
                for author in entry.findall("atom:author", namespace):
                    author_name = author.find("atom:name", namespace).text
                    authors.append(author_name)
                
                # Extract arXiv ID and URLs
                paper_id = entry.find("atom:id", namespace).text
                arxiv_id = paper_id.split("/abs/")[-1]
                
                # Get PDF URL
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                abstract_url = f"https://arxiv.org/abs/{arxiv_id}"
                
                # Extract categories
                categories = []
                primary_category = entry.find("arxiv:primary_category", namespace)
                if primary_category is not None:
                    categories.append(primary_category.attrib.get("term"))
                
                for category in entry.findall("atom:category", namespace):
                    cat_term = category.attrib.get("term")
                    if cat_term and cat_term not in categories:
                        categories.append(cat_term)
                
                # Extract publication date
                published = entry.find("atom:published", namespace).text
                published_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                
                # Convert to our standard format
                paper = {
                    "title": title,
                    "description": summary[:300] + "..." if len(summary) > 300 else summary,
                    "content": summary,
                    "url": abstract_url,
                    "pdf_url": pdf_url,
                    "arxiv_id": arxiv_id,
                    "source_name": "arXiv",
                    "authors": authors,
                    "categories": categories,
                    "published_at": published_date,
                    "source_type": "academic"
                }
                
                papers.append(paper)
            
            logger.info(f"Fetched {len(papers)} papers from arXiv for query: {search_query}")
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {str(e)}")
            return []

    def fetch_and_store_papers(self, search_query="cs", max_results=20):
        """Fetch papers from arXiv and store them in the database"""
        try:
            # Fetch papers
            papers = self.fetch_papers(search_query=search_query, max_results=max_results)
            print(papers)
            
            # Store each paper
            stored_count = 0
            for paper in papers:
                # Store paper
                result = self.store_paper(paper)
                if result:
                    stored_count += 1
                    
            logger.info(f"Stored {stored_count} papers for query: {search_query}")
            return stored_count
        except Exception as e:
            logger.error(f"Error fetching and storing papers: {str(e)}")
            return 0

    def store_paper(self, paper):
        """Store a paper in the database"""
        try:
            # Prepare paper document
            paper_doc = {
                "title": paper.get("title"),
                "description": paper.get("description"),
                "content": paper.get("content"),
                "url": paper.get("url"),
                "pdf_url": paper.get("pdf_url"),
                "arxiv_id": paper.get("arxiv_id"),
                "source_name": "arXiv",
                "authors": paper.get("authors", []),
                "categories": paper.get("categories", []),
                "published_at": paper.get("published_at"),
                "updated_at": datetime.utcnow(),
                "source_type": "academic",
                "vector_embedding": None  # Will be populated by embedding service
            }
            
            # Check if paper already exists (by arXiv ID)
            existing = articles_collection.find_one({"arxiv_id": paper.get("arxiv_id")})
            
            if existing:
                # Update existing paper
                articles_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": paper_doc}
                )
                return existing["_id"]
            else:
                # Insert new paper
                result = articles_collection.insert_one(paper_doc)
                return result.inserted_id
        except Exception as e:
            logger.error(f"Error storing paper: {str(e)}")
            return None

    def get_papers_by_category(self, category, limit=20, skip=0):
        """Get papers from database filtered by category"""
        try:
            # Build query to find arXiv papers with specific category
            query = {
                "source_name": "arXiv",
                "categories": category
            }
                
            # Get papers
            papers = list(articles_collection.find(query)
                         .sort("published_at", -1)
                         .skip(skip)
                         .limit(limit))
                          
            # Convert ObjectId to string for JSON serialization
            for paper in papers:
                paper["_id"] = str(paper["_id"])
                
            logger.info(f"Retrieved {len(papers)} papers from database for category: {category}")
            return papers
        except Exception as e:
            logger.error(f"Error getting papers: {str(e)}")
            return []

    def search_papers(self, query, limit=20, skip=0):
        """Search papers by text query"""
        try:
            # Build search query for arXiv papers
            search_query = {
                "$and": [
                    {"source_name": "arXiv"},
                    {"$text": {"$search": query}}
                ]
            }
            
            # Perform search
            papers = list(articles_collection.find(search_query)
                         .sort("published_at", -1)
                         .skip(skip)
                         .limit(limit))
                           
            # Convert ObjectId to string
            for paper in papers:
                paper["_id"] = str(paper["_id"])
                
            logger.info(f"Found {len(papers)} papers matching query: {query}")
            return papers
        except Exception as e:
            logger.error(f"Error searching papers: {str(e)}")
            return []