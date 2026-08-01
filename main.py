#!/usr/bin/env python3
"""
Main Business Website Scraper
"""

import argparse
import json
from business_scraper import BusinessWebsiteScraper
from utils import setup_logging, save_data
import pandas as pd
from urllib.parse import urlparse

logger = setup_logging()

def validate_url(url):
    """Validate and normalize URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return url
    except:
        pass
    
    return None

def display_results(summary):
    """Display scraping results in a readable format"""
    print("\n" + "="*80)
    print("🏢 BUSINESS WEBSITE SCRAPING RESULTS")
    print("="*80)
    
    print(f"\n📊 Summary for: {summary['website']}")
    print(f"   Pages Scraped: {summary['total_pages_scraped']}")
    print(f"   Emails Found: {summary['unique_emails_found']}")
    print(f"   Phone Numbers Found: {summary['unique_phones_found']}")
    print(f"   Addresses Found: {summary['unique_addresses_found']}")
    
    # Display contact information
    contacts = summary.get('contact_summary', {})
    
    if contacts.get('emails'):
        print(f"\n📧 Email Addresses:")
        for email in contacts['emails']:
            print(f"   • {email}")
    
    if contacts.get('phones'):
        print(f"\n📞 Phone Numbers:")
        for phone in contacts['phones']:
            print(f"   • {phone}")
    
    if contacts.get('addresses'):
        print(f"\n📍 Addresses:")
        for address in contacts['addresses']:
            print(f"   • {address}")
    
    if contacts.get('social_links'):
        print(f"\n🌐 Social Media Links:")
        for social in contacts['social_links']:
            print(f"   • {social['platform']}: {social['url']}")
    
    # Display business scope from first page
    if summary.get('detailed_pages'):
        first_page = summary['detailed_pages'][0]
        if first_page.get('business_scope'):
            print(f"\n🎯 Business Scope: {first_page['business_scope']}")
        
        # Show page types scraped
        page_types = {}
        for page in summary['detailed_pages']:
            page_type = page.get('page_type', 'other')
            page_types[page_type] = page_types.get(page_type, 0) + 1
        
        print(f"\n📄 Pages by Type:")
        for page_type, count in page_types.items():
            print(f"   • {page_type}: {count}")

def main():
    parser = argparse.ArgumentParser(description='Business Website Scraper')
    parser.add_argument('url', help='Website URL to scrape (e.g., https://example.com)')
    parser.add_argument('--pages', type=int, default=50, help='Maximum pages to scrape')
    parser.add_argument('--depth', type=int, default=3, help='Maximum depth to crawl')
    parser.add_argument('--output', choices=['json', 'csv', 'excel', 'all'], 
                       default='all', help='Output format')
    
    args = parser.parse_args()
    
    # Validate URL
    target_url = validate_url(args.url)
    if not target_url:
        print("❌ Error: Please provide a valid URL (e.g., https://example.com)")
        return
    
    print(f"🚀 Starting Business Website Scraper")
    print(f"🌐 Target: {target_url}")
    print(f"📄 Max Pages: {args.pages}")
    print(f"📏 Max Depth: {args.depth}")
    print("="*60)
    
    try:
        # Initialize scraper
        scraper = BusinessWebsiteScraper(target_url)
        
        # Start scraping
        results = scraper.scrape_website(
            max_pages=args.pages,
            max_depth=args.depth
        )
        
        if results and results.get('total_pages_scraped', 0) > 0:
            # Save data
            domain = urlparse(target_url).netloc
            filename = f"business_info_{domain}"
            save_data(results, filename, args.output)
            
            # Display results
            display_results(results)
            
            print(f"\n✅ Scraping completed successfully!")
            print(f"💾 Data saved to: business_data/{filename}_*")
            
        else:
            print("❌ No data was scraped. The website might be blocking requests or have no accessible content.")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()