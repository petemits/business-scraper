#!/usr/bin/env python3
"""
Batch scraper for multiple websites
"""

import csv
import json
from main import main as scrape_site
from utils import setup_logging
import time
import random

logger = setup_logging()

def scrape_from_csv(csv_file):
    """Scrape multiple websites from CSV file"""
    websites = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('url'):
                    websites.append(row['url'])
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return
    
    print(f"📋 Found {len(websites)} websites to scrape")
    
    for i, website in enumerate(websites, 1):
        print(f"\n{'='*60}")
        print(f"Scraping {i}/{len(websites)}: {website}")
        print(f"{'='*60}")
        
        try:
            # Simulate command line arguments
            import sys
            sys.argv = ['main.py', website, '--pages', '30', '--depth', '2']
            scrape_site()
            
        except Exception as e:
            logger.error(f"Failed to scrape {website}: {e}")
            print(f"❌ Failed: {e}")
        
        # Random delay between websites
        if i < len(websites):
            delay = random.randint(10, 30)
            print(f"\n⏳ Waiting {delay} seconds before next website...")
            time.sleep(delay)

def main():
    print("🏢 BATCH BUSINESS WEBSITE SCRAPER")
    print("="*50)
    
    # Example: Create a sample CSV if none exists
    sample_csv = 'websites_to_scrape.csv'
    
    try:
        with open(sample_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'company_name'])
            writer.writerow(['https://www.apple.com', 'Apple Inc.'])
            writer.writerow(['https://www.microsoft.com', 'Microsoft'])
            writer.writerow(['https://about.google', 'Google'])
        
        print(f"📝 Sample CSV created: {sample_csv}")
        print("Edit this file with your target websites and run:")
        print(f"python batch_scraper.py --csv {sample_csv}")
        
    except Exception as e:
        logger.error(f"Error creating sample CSV: {e}")

if __name__ == "__main__":
    main()