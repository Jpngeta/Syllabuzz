from services.news_service import NewsAPIClientService
from db import db
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import random

# Load environment variables from .env file
load_dotenv()

def seed_from_sample_data():
    """Seed the database with sample article data if no API key is available."""
    print("Using sample data to seed the database...")
    
    # Sample article data
    sample_articles = [
        {
            "title": "Scientists Discover New Species in Amazon Rainforest",
            "description": "A team of biologists has discovered a previously unknown species of tree frog in the Amazon rainforest, highlighting the region's incredible biodiversity.",
            "content": """Deep in the heart of the Amazon rainforest, scientists have made an extraordinary discovery: a new species of tree frog with unique colorations and behaviors. This finding underscores the incredible biodiversity of the region and the importance of conservation efforts.

The newly discovered species, temporarily named "Hyla amazonica" until formal classification, exhibits a remarkable combination of emerald green and sapphire blue patterns not previously documented in any related species. The research team, led by Dr. Maria Rodriguez, spent over six months tracking these elusive amphibians through the dense undergrowth of the western Amazon basin.

"What makes this discovery particularly significant is not just the frog's unique appearance, but its unusual mating behaviors and vocalization patterns," explained Dr. Rodriguez. "The males produce a distinct two-tone call that carries remarkably far through the forest canopy."

Initial genetic analysis suggests that this species diverged from related tree frogs approximately 1.2 million years ago, coinciding with a period of significant geological change in the Amazon basin. This timing provides valuable insights into how speciation occurs in response to environmental changes.

Conservation biologists are particularly concerned about the new species' future, as its habitat range appears quite limited. "We've only found these frogs in a relatively small area, which unfortunately is under threat from logging operations that are scheduled to begin next year," said team member Dr. Thomas Jenkins.

The researchers have already begun the process of advocating for protected status for the region, highlighting how this discovery demonstrates that the Amazon still holds many undiscovered species that could be lost before they are even known to science.

Their findings will be published next month in the Journal of Tropical Herpetology, with a recommendation for immediate conservation action for both the species and its habitat.""",
            "url": "https://example.com/amazon-discovery",
            "image_url": "https://images.unsplash.com/photo-1566487097168-e91a4f38bee2",
            "source_name": "Science Journal",
            "author": "Dr. Maria Rodriguez",
            "categories": ["science", "environment"],
            "published_at": datetime.now()
        },
        {
            "title": "New Study Shows Benefits of Mediterranean Diet",
            "description": "Research confirms that following a Mediterranean diet can significantly reduce the risk of heart disease and improve longevity.",
            "content": """A comprehensive study following participants over 10 years has shown that those who adhered to a Mediterranean diet had a 25% lower risk of heart disease compared to control groups. The diet, rich in olive oil, nuts, fruits, and vegetables, was also linked to improved cognitive function in older adults.

The research, conducted by a team at Central University Medical Center, followed 4,280 participants aged 40-70 over a decade, carefully tracking their dietary habits and health outcomes. Participants were randomly assigned to either follow a Mediterranean diet supplemented with extra-virgin olive oil, a Mediterranean diet supplemented with mixed nuts, or a control diet with reduced fat intake.

"What we found most striking was the consistency of benefits across different health markers," explained lead researcher Emma Johnson, PhD. "Beyond the cardiovascular improvements we expected, we saw significant benefits in cognitive function, particularly in memory and executive function tests."

The Mediterranean diet focuses on:
- Daily consumption of vegetables, fruits, whole grains, and healthy fats
- Weekly intake of fish, poultry, beans, and eggs
- Moderate portions of dairy products
- Limited intake of red meat and sweets
- Optional moderate consumption of red wine with meals

The study controlled for other lifestyle factors such as physical activity, smoking, and social engagement, strengthening the conclusion that the diet itself was responsible for the observed health benefits.

Participants who most closely followed the Mediterranean diet showed:
- 25% reduction in risk of heart disease
- 18% lower risk of stroke
- 30% reduction in markers of inflammation
- 17% improvement in memory retention tests
- 22% reduced risk of developing mild cognitive impairment

"What's particularly valuable about this diet is its accessibility and sustainability," noted Dr. Johnson. "Unlike restrictive diets that people struggle to maintain, the Mediterranean approach offers variety, flavor, and cultural traditions that make it easier to adopt long-term."

The researchers recommend that adults of all ages consider adopting elements of the Mediterranean diet, suggesting that benefits begin to accrue even when the diet is started later in life.""",
            "url": "https://example.com/mediterranean-diet-study",
            "image_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf",
            "source_name": "Health Research Today",
            "author": "Emma Johnson, PhD",
            "categories": ["health", "nutrition"],
            "published_at": datetime.now()
        },
        {
            "title": "Tech Giant Unveils Revolutionary AI System",
            "description": "A leading technology company has announced a breakthrough in artificial intelligence that could transform how machines learn and interact with humans.",
            "content": "In a major technological breakthrough, researchers have developed an AI system capable of learning from minimal data while achieving unprecedented accuracy. The system demonstrates remarkable capabilities in natural language processing and visual recognition tasks, potentially revolutionizing fields from healthcare to transportation.",
            "url": "https://example.com/ai-breakthrough",
            "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485",
            "source_name": "Tech Innovator",
            "author": "James Chen",
            "categories": ["technology", "artificial intelligence"],
            "published_at": datetime.now()
        },
        {
            "title": "Global Markets React to Economic Policy Changes",
            "description": "Stock markets worldwide experienced volatility as major economies announced shifts in monetary policy.",
            "content": "Financial markets showed significant movement today as central banks in several countries announced changes to interest rates and economic stimulus programs. Analysts suggest these policy adjustments could have far-reaching implications for global trade and investment strategies in the coming months.",
            "url": "https://example.com/market-reaction",
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3",
            "source_name": "Financial Times",
            "author": "Robert Williams",
            "categories": ["business", "economy"],
            "published_at": datetime.now()
        },
        {
            "title": "Breakthrough in Renewable Energy Storage",
            "description": "Engineers develop new battery technology that could solve the intermittency problem of renewable energy sources.",
            "content": "A team of engineers has developed a revolutionary energy storage system that addresses one of the biggest challenges in renewable energy: efficient storage. The new battery technology can store wind and solar power for extended periods with minimal loss, potentially transforming the renewable energy landscape and accelerating the transition away from fossil fuels.",
            "url": "https://example.com/energy-breakthrough",
            "image_url": "https://images.unsplash.com/photo-1509391618207-32bdb1702e3c",
            "source_name": "Energy Innovation",
            "author": "Dr. Sarah Chen",
            "categories": ["technology", "environment", "science"],
            "published_at": datetime.now()
        }
    ]
    
    # Add 15 more variations of articles with different titles by modifying the original 5
    all_articles = sample_articles.copy()
    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    
    for i in range(3):  # Create 3 variations of each sample article
        for article in sample_articles:
            new_article = article.copy()
            # Modify title with a random number
            new_article["title"] = f"New: {new_article['title']} (Part {i+2})"
            # Randomize image URL slightly
            new_article["image_url"] = f"{new_article['image_url']}?random={random.randint(1000, 9999)}"
            # Add a random category
            if "categories" in new_article:
                new_article["categories"] = [random.choice(categories)]
            all_articles.append(new_article)
    
    # Insert sample articles into the database
    for article in all_articles:
        # Check if article already exists (by URL)
        existing = db.articles.find_one({'title': article['title']})
        if not existing:
            db.articles.insert_one(article)
            print(f"Added sample article: {article['title']}")
    
    return len(all_articles)

def seed_from_api():
    """Seed the database with articles from NewsAPI."""
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        print("No NEWS_API_KEY found in environment variables.")
        return False
    
    print("Fetching articles from News API...")
    
    # Initialize news service with API key
    news_service = NewsAPIClientService(api_key=api_key)
    
    # Categories to fetch
    categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    articles_added = 0
    
    # Fetch articles for each category
    for category in categories:
        try:
            print(f"Fetching {category} articles...")
            response = news_service.get_top_headlines(category=category, page_size=20)
            articles = news_service.format_articles(response)
            
            # Insert articles into the database
            for article in articles:
                # Check if article already exists (by URL)
                existing = db.articles.find_one({'url': article['url']})
                if not existing:
                    db.articles.insert_one(article)
                    articles_added += 1
            
            print(f"Added {len(articles)} {category} articles")
        except Exception as e:
            print(f"Error fetching {category} articles: {e}")
    
    if articles_added > 0:
        print(f"Successfully added {articles_added} articles from News API")
        return True
    else:
        print("No articles were added from News API")
        return False

if __name__ == "__main__":
    # Check if articles collection is empty
    existing_count = db.articles.count_documents({})
    print(f"Current article count in database: {existing_count}")
    
    if existing_count < 5:
        # Try to seed from API first
        api_success = seed_from_api()
        
        # If API seeding fails, use sample data
        if not api_success:
            seed_from_sample_data()
    else:
        print("Database already has articles. No seeding necessary.")
    
    # Final count
    final_count = db.articles.count_documents({})
    print(f"Final article count in database: {final_count}")