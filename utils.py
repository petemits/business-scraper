import requests
from bs4 import BeautifulSoup
import json
import csv
import pandas as pd
import logging
import time
import random
import os
import re
import urllib.parse
from datetime import datetime
from fake_useragent import UserAgent
from tqdm import tqdm
import magic

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('business_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_session():
    """Create requests session with random user agent"""
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    return session

def make_request(url, session, max_retries=3, delay=2):
    """Make HTTP request with retry logic and respect robots.txt"""
    for attempt in range(max_retries):
        try:
            # Check robots.txt first
            if not check_robots_txt(url, session):
                logging.warning(f"Robots.txt disallows scraping: {url}")
                return None
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if content is HTML
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                logging.warning(f"Non-HTML content from {url}: {content_type}")
                return None
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                sleep_time = delay * (attempt + 1) + random.uniform(0, 2)
                time.sleep(sleep_time)
    return None

def check_robots_txt(url, session):
    """Check robots.txt for scraping permissions"""
    try:
        parsed_url = urllib.parse.urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        response = session.get(robots_url, timeout=10)
        if response.status_code == 200:
            robots_content = response.text
            # Simple check - in production use robotparser
            if "Disallow: /" in robots_content:
                return False
    except:
        pass
    return True

def save_data(data, filename_prefix, format='all'):
    """Save data in multiple formats"""
    if not data:
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Create output directory
        os.makedirs('business_data', exist_ok=True)
        
        if format in ['all', 'json']:
            json_filename = f'business_data/{filename_prefix}_{timestamp}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        if format in ['all', 'csv'] and isinstance(data, list) and data and isinstance(data[0], dict):
            csv_filename = f'business_data/{filename_prefix}_{timestamp}.csv'
            df = pd.DataFrame(data)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        if format in ['all', 'excel'] and isinstance(data, list) and data and isinstance(data[0], dict):
            excel_filename = f'business_data/{filename_prefix}_{timestamp}.xlsx'
            df = pd.DataFrame(data)
            df.to_excel(excel_filename, index=False)
        
        logging.info(f"Data saved with prefix: {filename_prefix}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving data: {e}")
        return False

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = ' '.join(text.strip().split())
    # Remove multiple newlines
    text = re.sub(r'\n+', ' ', text)
    return text

def extract_emails(text):
    """Extract email addresses from text"""
    emails = set()
    for pattern in config.EMAIL_PATTERNS:
        found_emails = re.findall(pattern, text, re.IGNORECASE)
        emails.update(found_emails)
    return list(emails)

def extract_phones(text):
    """Extract phone numbers from text"""
    phones = set()
    for pattern in config.PHONE_PATTERNS:
        found_phones = re.findall(pattern, text)
        phones.update(found_phones)
    return list(phones)

def is_valid_url(url, base_domain):
    """Check if URL is valid and belongs to the same domain"""
    try:
        parsed = urllib.parse.urlparse(url)
        base_parsed = urllib.parse.urlparse(base_domain)
        
        # Check if same domain
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            return False
            
        # Check if it's a useful page (not admin, login, etc.)
        excluded_paths = ['admin', 'login', 'signin', 'dashboard', 'wp-admin']
        path = parsed.path.lower()
        if any(excluded in path for excluded in excluded_paths):
            return False
            
        return True
    except:
        return False

def normalize_url(url, base_url):
    """Convert relative URL to absolute URL"""
    try:
        return urllib.parse.urljoin(base_url, url)
    except:
        return url