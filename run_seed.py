import os
import sys
from seed_articles import seed_from_sample_data, seed_from_api

if __name__ == "__main__":
    print("Starting database seeding process...")
    
    # Try to seed from API first
    api_success = seed_from_api()
    
    # If API seeding fails, use sample data
    if not api_success:
        print("API seeding failed, using sample data instead...")
        seed_from_sample_data()
        
    print("Seeding process completed.")