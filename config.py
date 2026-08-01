import os
from dotenv import load_dotenv

load_dotenv()

# Scraping Configuration
REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', '3'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
TIMEOUT = int(os.getenv('TIMEOUT', '30'))
MAX_PAGES = int(os.getenv('MAX_PAGES', '50'))
MAX_DEPTH = int(os.getenv('MAX_DEPTH', '3'))

# Contact Information Patterns
EMAIL_PATTERNS = [
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
]

PHONE_PATTERNS = [
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
    r'\b\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
]

# Business Information Selectors
CONTACT_SELECTORS = {
    'email': ['a[href*="mailto:"]', '.email', '[class*="email"]', '[id*="email"]'],
    'phone': ['a[href*="tel:"]', '.phone', '.telephone', '[class*="phone"]', '[id*="phone"]'],
    'address': ['.address', '[class*="address"]', '[itemprop="address"]', '.location'],
    'contact_form': ['form[action*="contact"]', '.contact-form', '#contact-form'],
    'social_links': ['a[href*="facebook.com"]', 'a[href*="twitter.com"]', 'a[href*="linkedin.com"]', 
                    'a[href*="instagram.com"]', '.social-links', '.social-media']
}

BUSINESS_SELECTORS = {
    'about': ['.about', '.about-us', '#about', '[class*="about"]'],
    'services': ['.services', '.what-we-do', '#services', '.service-list'],
    'team': ['.team', '.staff', '#team', '.employees'],
    'testimonials': ['.testimonials', '.reviews', '#testimonials'],
    'products': ['.products', '.portfolio', '#products', '.items']
}

# Output Configuration
OUTPUT_DIR = 'business_data'
LOG_FILE = 'business_scraper.log'