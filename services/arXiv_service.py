# Updated arXiv service with simplified, reliable approach
import logging
import requests
import xml.etree.ElementTree as ET
import time
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

    def fetch_papers(self, search_query="cs.AI", max_results=30, start=0, sort_by="submittedDate", years_limit=5):
        """Fetch papers from arXiv API with improved reliability"""
        try:
            # Better handling for all category types
            if ":" not in search_query and "." in search_query:
                # Handle any category with subcategory (cs.AI, stat.ML, math.NT, etc.)
                formatted_query = f"cat:{search_query}"
            elif search_query in ["cs", "stat", "math", "physics"]:
                # Handle any main category
                formatted_query = f"cat:{search_query}"
                    
            # Add basic search if query uses complex syntax
            if "all:" in formatted_query or "ti:" in formatted_query:
                # Keep it as is
                pass
            
            # Prepare parameters
            params = {
                "search_query": formatted_query,
                "start": start,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": "descending"
            }
            
            logger.info(f"Querying arXiv with: {formatted_query}")
            
            # Add rate limiting compliance
            time.sleep(1)
            
            # Make API request with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(self.base_url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        break
                        
                    logger.warning(f"arXiv API attempt {attempt+1}/{max_retries} failed: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Network error attempt {attempt+1}/{max_retries}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
            
            if response.status_code != 200:
                logger.error(f"All arXiv API attempts failed: {response.status_code}")
                return []
                
            # Parse XML response - check response content first
            content = response.content
            if not content or len(content) < 100:
                logger.error(f"arXiv API returned empty or invalid response: {content}")
                return []
                
            # Parse the XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(f"Failed to parse arXiv response XML: {str(e)}")
                logger.error(f"Response content: {content[:200]}...")
                return []
            
            # Extract papers from response
            papers = []
            namespace = {"atom": "http://www.w3.org/2005/Atom", 
                         "arxiv": "http://arxiv.org/schemas/atom"}
            
            # Count entries to verify we received results
            entries = root.findall("atom:entry", namespace)
            logger.info(f"Found {len(entries)} entries in arXiv response")
            
            for entry in root.findall("atom:entry", namespace):
                # Skip the OpenSearch entry if present
                title_elem = entry.find("atom:title", namespace)
                summary_elem = entry.find("atom:summary", namespace)
                
                # More explicit checks - avoid using truth value of Element objects
                if title_elem is None or summary_elem is None:
                    continue
                
                # Also check if the text content exists
                if title_elem.text is None or summary_elem.text is None:
                    continue
                    
                # Extract basic paper information
                title = title_elem.text.strip()
                summary = summary_elem.text.strip()
                
                # Extract authors
                authors = []
                for author in entry.findall("atom:author", namespace):
                    name_elem = author.find("atom:name", namespace)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                # Extract arXiv ID and URLs
                id_elem = entry.find("atom:id", namespace)
                if id_elem is None or not id_elem.text:
                    continue
                    
                paper_id = id_elem.text
                arxiv_id = paper_id.split("/abs/")[-1]
                
                # Get PDF URL
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                abstract_url = f"https://arxiv.org/abs/{arxiv_id}"
                
                # Extract categories
                categories = []
                primary_category = entry.find("arxiv:primary_category", namespace)
                if primary_category is not None:
                    cat_term = primary_category.attrib.get("term")
                    if cat_term:
                        categories.append(cat_term)
                
                for category in entry.findall("atom:category", namespace):
                    cat_term = category.attrib.get("term")
                    if cat_term and cat_term not in categories:
                        categories.append(cat_term)
                
                # Extract publication date
                published_elem = entry.find("atom:published", namespace)
                if published_elem is None or not published_elem.text:
                    published_date = datetime.utcnow()
                else:
                    try:
                        published_date = datetime.strptime(published_elem.text, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        published_date = datetime.utcnow()
                
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

                if years_limit > 0:
            # Calculate cutoff date
                    from datetime import datetime, timedelta
                    cutoff_date = datetime.now() - timedelta(days=365 * years_limit)
                    
                    # Filter papers by date
                    filtered_papers = [paper for paper in papers if paper["published_at"] >= cutoff_date]
                    
                    logger.info(f"Date filtering: kept {len(filtered_papers)} out of {len(papers)} papers (limit: {years_limit} years)")
                    papers = filtered_papers
            
            logger.info(f"Successfully extracted {len(papers)} papers from arXiv for query: {search_query}")
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {str(e)}", exc_info=True)
            return []
        
    def fetch_and_store_papers(self, search_query="cs", max_results=20, years_limit=5):
        """Fetch papers from arXiv and store them in the database"""
        try:
            # Fetch papers
            papers = self.fetch_papers(search_query=search_query, max_results=max_results, years_limit=years_limit)
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