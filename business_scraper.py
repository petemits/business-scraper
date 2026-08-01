import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from collections import deque
from config import *
from utils import setup_logging, get_session, make_request, save_data, clean_text, extract_emails, extract_phones, is_valid_url, normalize_url

logger = setup_logging()

class BusinessWebsiteScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = get_session()
        self.visited_urls = set()
        self.business_data = []
        self.contact_info = {}
        
    def scrape_website(self, max_pages=MAX_PAGES, max_depth=MAX_DEPTH):
        """Main method to scrape entire website"""
        logger.info(f"Starting to scrape: {self.base_url}")
        
        queue = deque([(self.base_url, 0)])  # (url, depth)
        page_count = 0
        
        with tqdm(total=max_pages, desc="Scraping Pages") as pbar:
            while queue and page_count < max_pages:
                url, depth = queue.popleft()
                
                if url in self.visited_urls or depth > max_depth:
                    continue
                
                self.visited_urls.add(url)
                logger.info(f"Scraping: {url} (depth: {depth})")
                
                # Scrape the page
                page_data = self.scrape_page(url, depth)
                if page_data:
                    self.business_data.append(page_data)
                    page_count += 1
                    pbar.update(1)
                
                # Find and add new links to queue
                if depth < max_depth:
                    new_links = self.extract_links(url)
                    for link in new_links:
                        if link not in self.visited_urls:
                            queue.append((link, depth + 1))
                
                # Respectful delay
                time.sleep(random.uniform(REQUEST_DELAY, REQUEST_DELAY + 2))
        
        # Compile final results
        final_data = self.compile_results()
        return final_data
    
    def scrape_page(self, url, depth):
        """Scrape a single page for business information"""
        response = make_request(url, self.session)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        # Extract basic information
        page_info = {
            'url': url,
            'depth': depth,
            'title': clean_text(soup.title.string) if soup.title else '',
            'meta_description': self.extract_meta_description(soup),
            'headings': self.extract_headings(soup),
            'page_type': self.classify_page(url, soup),
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract contact information
        contact_data = self.extract_contact_info(soup, page_text)
        page_info.update(contact_data)
        
        # Extract business information
        business_data = self.extract_business_info(soup, page_text)
        page_info.update(business_data)
        
        # Update global contact info
        self.update_global_contacts(contact_data)
        
        logger.debug(f"Scraped page: {url} - Found {len(contact_data.get('emails', []))} emails, {len(contact_data.get('phones', []))} phones")
        return page_info
    
    def extract_links(self, url):
        """Extract all internal links from a page"""
        response = make_request(url, self.session)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = normalize_url(href, url)
            
            if is_valid_url(full_url, self.base_url):
                links.append(full_url)
        
        # Remove duplicates and already visited
        links = list(set(links) - self.visited_urls)
        return links[:50]  # Limit to 50 links per page
    
    def extract_contact_info(self, soup, page_text):
        """Extract contact information from page"""
        contact_data = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'social_links': [],
            'contact_forms': []
        }
        
        # Extract emails using regex
        emails = extract_emails(page_text)
        contact_data['emails'].extend(emails)
        
        # Extract emails from mailto links
        for mail_link in soup.select('a[href^="mailto:"]'):
            href = mail_link.get('href', '')
            email = href.replace('mailto:', '').split('?')[0]
            if email and email not in contact_data['emails']:
                contact_data['emails'].append(email)
        
        # Extract phones using regex
        phones = extract_phones(page_text)
        contact_data['phones'].extend(phones)
        
        # Extract phones from tel links
        for tel_link in soup.select('a[href^="tel:"]'):
            href = tel_link.get('href', '')
            phone = href.replace('tel:', '')
            if phone and phone not in contact_data['phones']:
                contact_data['phones'].append(phone)
        
        # Extract addresses
        addresses = self.extract_addresses(soup, page_text)
        contact_data['addresses'].extend(addresses)
        
        # Extract social links
        social_links = self.extract_social_links(soup)
        contact_data['social_links'].extend(social_links)
        
        # Check for contact forms
        if soup.find('form') and any(term in page_text.lower() for term in ['contact', 'message', 'inquiry']):
            contact_data['contact_forms'].append('Contact form detected')
        
        # Clean up duplicates
        for key in contact_data:
            contact_data[key] = list(set(contact_data[key]))
        
        return contact_data
    
    def extract_business_info(self, soup, page_text):
        """Extract business-specific information"""
        business_data = {
            'about_text': '',
            'services': [],
            'team_members': [],
            'testimonials': [],
            'products': [],
            'business_scope': ''
        }
        
        # Extract about information
        about_text = self.extract_section_text(soup, BUSINESS_SELECTORS['about'])
        business_data['about_text'] = clean_text(about_text[:1000])  # Limit length
        
        # Extract services
        services = self.extract_services(soup)
        business_data['services'] = services
        
        # Extract team members
        team = self.extract_team(soup)
        business_data['team_members'] = team
        
        # Extract testimonials
        testimonials = self.extract_testimonials(soup)
        business_data['testimonials'] = testimonials
        
        # Extract products
        products = self.extract_products(soup)
        business_data['products'] = products
        
        # Determine business scope
        business_data['business_scope'] = self.analyze_business_scope(page_text)
        
        return business_data
    
    def extract_section_text(self, soup, selectors):
        """Extract text from a section using multiple selectors"""
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([clean_text(el.get_text()) for el in elements])
                if text.strip():
                    return text
        return ""
    
    def extract_services(self, soup):
        """Extract services offered"""
        services = []
        for selector in BUSINESS_SELECTORS['services']:
            elements = soup.select(selector)
            for element in elements:
                # Try to find list items or headings
                items = element.select('li, h3, h4, .service-item')
                for item in items:
                    service_text = clean_text(item.get_text())
                    if service_text and len(service_text) > 10:
                        services.append(service_text)
        return list(set(services))[:20]  # Limit to 20 services
    
    def extract_team(self, soup):
        """Extract team member information"""
        team = []
        for selector in BUSINESS_SELECTORS['team']:
            elements = soup.select(selector)
            for element in elements:
                # Look for team member elements
                members = element.select('.team-member, .staff-member, .employee')
                for member in members:
                    name = member.select_one('h3, h4, .name')
                    position = member.select_one('.position, .title, .role')
                    
                    if name:
                        member_info = {
                            'name': clean_text(name.get_text()),
                            'position': clean_text(position.get_text()) if position else ''
                        }
                        team.append(member_info)
        return team[:50]  # Limit to 50 team members
    
    def extract_testimonials(self, soup):
        """Extract customer testimonials"""
        testimonials = []
        for selector in BUSINESS_SELECTORS['testimonials']:
            elements = soup.select(selector)
            for element in elements:
                # Look for testimonial text
                quotes = element.select('.testimonial-text, .review-content, blockquote')
                for quote in quotes:
                    text = clean_text(quote.get_text())
                    if text and len(text) > 20:
                        testimonials.append(text)
        return testimonials[:20]  # Limit to 20 testimonials
    
    def extract_products(self, soup):
        """Extract products or portfolio items"""
        products = []
        for selector in BUSINESS_SELECTORS['products']:
            elements = soup.select(selector)
            for element in elements:
                # Look for product items
                items = element.select('.product, .portfolio-item, .item')
                for item in items:
                    name = item.select_one('h3, h4, .product-name')
                    description = item.select_one('.description, .product-desc')
                    
                    if name:
                        product_info = {
                            'name': clean_text(name.get_text()),
                            'description': clean_text(description.get_text()) if description else ''
                        }
                        products.append(product_info)
        return products[:50]  # Limit to 50 products
    
    def extract_addresses(self, soup, page_text):
        """Extract physical addresses"""
        addresses = []
        
        # Look for address elements
        for selector in CONTACT_SELECTORS['address']:
            elements = soup.select(selector)
            for element in elements:
                address_text = clean_text(element.get_text())
                if self.looks_like_address(address_text):
                    addresses.append(address_text)
        
        return addresses
    
    def extract_social_links(self, soup):
        """Extract social media links"""
        social_links = []
        social_patterns = [
            'facebook.com', 'twitter.com', 'linkedin.com', 
            'instagram.com', 'youtube.com', 'github.com'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform in social_patterns:
                if platform in href:
                    social_links.append({
                        'platform': platform.split('.')[0],
                        'url': href
                    })
                    break
        
        return social_links
    
    def looks_like_address(self, text):
        """Check if text looks like a physical address"""
        if not text or len(text) < 20:
            return False
        
        address_indicators = ['street', 'st.', 'avenue', 'ave.', 'road', 'rd.', 
                             'city', 'state', 'zip', 'country', 'address']
        
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in address_indicators):
            return True
        
        # Check for common address patterns
        if re.search(r'\d+\s+[\w\s]+,?\s*\w+,\s*\w+\s+\d{5}', text):
            return True
        
        return False
    
    def analyze_business_scope(self, text):
        """Analyze text to determine business scope/industry"""
        text_lower = text.lower()
        
        industry_keywords = {
            'technology': ['software', 'app', 'tech', 'IT', 'development', 'programming'],
            'consulting': ['consulting', 'advisor', 'consultant', 'strategy'],
            'healthcare': ['medical', 'health', 'clinic', 'hospital', 'doctor'],
            'education': ['education', 'school', 'university', 'training', 'course'],
            'retail': ['store', 'shop', 'retail', 'product', 'sell'],
            'service': ['service', 'maintenance', 'repair', 'support']
        }
        
        detected_industries = []
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_industries.append(industry)
        
        return ', '.join(detected_industries) if detected_industries else 'General Business'
    
    def classify_page(self, url, soup):
        """Classify the type of page"""
        url_lower = url.lower()
        text_lower = soup.get_text().lower()
        
        if any(term in url_lower for term in ['contact', 'about', 'services', 'products']):
            return url_lower.split('/')[-2]  # Get the page name from URL
        
        if 'contact' in text_lower:
            return 'contact'
        elif 'about' in text_lower:
            return 'about'
        elif 'service' in text_lower:
            return 'services'
        elif 'product' in text_lower:
            return 'products'
        
        return 'other'
    
    def extract_meta_description(self, soup):
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return clean_text(meta_desc['content']) if meta_desc else ''
    
    def extract_headings(self, soup):
        """Extract all headings from the page"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [clean_text(h.get_text()) for h in h_tags if clean_text(h.get_text())]
        return headings
    
    def update_global_contacts(self, contact_data):
        """Update global contact information"""
        for key in ['emails', 'phones', 'addresses']:
            if key not in self.contact_info:
                self.contact_info[key] = set()
            self.contact_info[key].update(contact_data.get(key, []))
    
    def compile_results(self):
        """Compile final results from all scraped pages"""
        # Convert sets to lists in contact_info
        for key in self.contact_info:
            self.contact_info[key] = list(self.contact_info[key])
        
        # Create summary
        summary = {
            'website': self.base_url,
            'total_pages_scraped': len(self.business_data),
            'unique_emails_found': len(self.contact_info.get('emails', [])),
            'unique_phones_found': len(self.contact_info.get('phones', [])),
            'unique_addresses_found': len(self.contact_info.get('addresses', [])),
            'scraping_completed_at': datetime.now().isoformat(),
            'contact_summary': self.contact_info,
            'detailed_pages': self.business_data
        }
        
        return summary