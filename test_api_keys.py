import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_newsapi():
    """Test the NewsAPI connection"""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        print("⚠️ No NewsAPI key found in environment variables")
        return False
    
    try:
        url = 'https://newsapi.org/v2/top-headlines'
        params = {'country': 'us', 'apiKey': api_key}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ NewsAPI connection successful!")
            return True
        else:
            print(f"❌ NewsAPI returned status code {response.status_code}")
            print(f"Error message: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error testing NewsAPI: {str(e)}")
        return False

def test_serpapi():
    """Test the SerpAPI connection"""
    api_key = os.getenv('SERPAPI_KEY')
    
    if not api_key:
        print("⚠️ No SerpAPI key found in environment variables")
        return False
    
    try:
        url = 'https://serpapi.com/search'
        params = {
            'engine': 'google',
            'q': 'test',
            'api_key': api_key
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ SerpAPI connection successful!")
            return True
        else:
            print(f"❌ SerpAPI returned status code {response.status_code}")
            print(f"Error message: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error testing SerpAPI: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing API connections...")
    test_newsapi()
    test_serpapi()
    print("Done!")