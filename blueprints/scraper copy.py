# blueprints/scraper.py
import threading
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, flash, redirect, url_for

from models import db, Job

scraper_bp = Blueprint('scraper', __name__)

# ============================================================
# CONFIGURATION
# ============================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
]

WEBSITE_CONFIGS = {
    'naukri': {
        'urls': [
            'https://www.naukri.com/python-developer-jobs',
            'https://www.naukri.com/software-developer-jobs',
            'https://www.naukri.com/it-jobs',
        ],
        'card_selectors': ['.jobTuple', '[class*="jobTuple"]', '.list-item', 'article'],
        'title_selectors': ['a.title', '.jobTuple-title', 'h2 a', '.title'],
        'company_selectors': ['.subTitle', '.companyName', '.orgName'],
        'location_selectors': ['.location', '.loc', '.fleft'],
        'link_selector': 'a.title',
    },
    'indeed': {
        'urls': [
            'https://in.indeed.com/jobs?q=software+developer&l=India',
            'https://in.indeed.com/jobs?q=python+developer&l=India',
        ],
        'card_selectors': ['.job_seen_beacon', '.cardOutline', '.resultContent', 'td.resultContent'],
        'title_selectors': ['h2.jobTitle', 'h2 span', 'a.jobTitle', '.title a'],
        'company_selectors': ['.companyName', '.company_name', 'span.companyName'],
        'location_selectors': ['.companyLocation', '.location', '.recJobLoc'],
        'link_selector': 'a.jobTitle',
    },
    'foundit': {
        'urls': ['https://www.foundit.in/jobs'],
        'card_selectors': ['.jobCard', '[class*="job"]', '.card'],
        'title_selectors': ['h3', '.title', '[class*="title"]'],
        'company_selectors': ['.company', '.org', '[class*="company"]'],
        'location_selectors': ['.location', '[class*="location"]'],
        'link_selector': 'a',
    },
    'shine': {
        'urls': ['https://www.shine.com/jobs/search'],
        'card_selectors': ['.jobCard', '.resultCard', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.company', '.org'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'wellfound': {
        'urls': ['https://wellfound.com/location/india'],
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.company', '.startup-name'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'cutshort': {
        'urls': ['https://cutshort.io/jobs'],
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.company', '.org-name'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'hirist': {
        'urls': ['https://www.hirist.tech/jobs'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'internshala': {
        'urls': ['https://internshala.com/jobs/'],
        'card_selectors': ['.individual_internship', '[class*="individual"]'],
        'title_selectors': ['h3', 'h4', '.heading_4_5', '.job-title'],
        'company_selectors': ['.company-name', '.company_name', '.link_display_like_text'],
        'location_selectors': ['.location', '#location_names'],
        'link_selector': 'a',
    },
    'freshersworld': {
        'urls': ['https://www.freshersworld.com/jobs'],
        'card_selectors': ['.job-container', '.job-list', '[class*="job"]'],
        'title_selectors': ['h3', '.job-title', 'a strong'],
        'company_selectors': ['.company-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'apna': {
        'urls': ['https://apna.co/jobs'],
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.employer-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'workindia': {
        'urls': ['https://www.workindia.in/jobs'],
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'linkedin': {
        'urls': [
            'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=software+developer&location=India&start=0',
            'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python+developer&location=India&start=0',
        ],
        'card_selectors': ['.base-card', '.job-search-card', 'li'],
        'title_selectors': ['.base-search-card__title', '.job-search-card__title', 'h3'],
        'company_selectors': ['.base-search-card__subtitle', '.job-search-card__subtitle', 'h4'],
        'location_selectors': ['.job-search-card__location', '.location'],
        'link_selector': 'a.base-card__full-link',
    },
    'ncs': {
        'urls': ['https://www.ncs.gov.in/jobs'],
        'card_selectors': ['.job-listing', '[class*="job"]', '.card'],
        'title_selectors': ['h3', 'h4', '.title'],
        'company_selectors': ['.company', '.employer'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'reliefweb': {
        'urls': ['https://reliefweb.int/jobs'],
        'card_selectors': ['.job-listing', '[class*="job"]', 'article'],
        'title_selectors': ['h3', 'h4', '.title a'],
        'company_selectors': ['.company', '.source', '.organization'],
        'location_selectors': ['.location', '.country'],
        'link_selector': 'a',
    },
    'idealist': {
        'urls': ['https://www.idealist.org/en/jobs'],
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'devex': {
        'urls': ['https://www.devex.com/jobs/search'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'unjobnet': {
        'urls': ['https://www.unjobnet.org/'],
        'card_selectors': ['.job-listing', '[class*="job"]', '.vacancy'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.agency'],
        'location_selectors': ['.location', '.country'],
        'link_selector': 'a',
    },
    'devnetjobs': {
        'urls': ['https://devnetjobs.org/'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'devnetjobsindia': {
        'urls': ['https://devnetjobsindia.org/'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'arthan': {
        'urls': ['https://arthancareers.com/job-listing'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'impactpool': {
        'urls': ['https://www.impactpool.org/'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'charityjob': {
        'urls': ['https://www.charityjob.co.uk'],
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.charity', '.employer'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
    }

def create_session():
    session = requests.Session()
    session.headers.update(get_random_headers())
    return session

def safe_request(url, timeout=15, max_retries=2):
    """Safe HTTP request with retry"""
    for attempt in range(max_retries):
        try:
            session = create_session()
            response = session.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response
            time.sleep(1)
        except:
            time.sleep(2)
    return None

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:300]

def standardize_job(job_dict):
    """Standardize job data format"""
    return {
        'title': clean_text(job_dict.get('title', ''))[:200],
        'company': clean_text(job_dict.get('company', 'Unknown'))[:200],
        'location': clean_text(job_dict.get('location', 'India'))[:200],
        'salary_range': clean_text(job_dict.get('salary_range', 'Not Disclosed'))[:100],
        'experience_required': clean_text(job_dict.get('experience_required', 'Not Specified'))[:50],
        'job_type': clean_text(job_dict.get('job_type', 'Full-time'))[:50],
        'description': clean_text(job_dict.get('description', ''))[:500],
        'requirements': clean_text(job_dict.get('requirements', ''))[:500],
        'skills_required': clean_text(job_dict.get('skills_required', ''))[:500],
        'apply_method': job_dict.get('apply_method', 'website'),
        'apply_email': job_dict.get('apply_email', ''),
        'apply_website': job_dict.get('apply_website', ''),
        'source': 'scraped',
        'source_url': job_dict.get('source_url', ''),
        'is_active': True,
        'posted_date': datetime.utcnow(),
        'last_updated': datetime.utcnow()
    }

# ============================================================
# JOB EXTRACTOR
# ============================================================

def extract_jobs_from_html(soup, url, selectors_config):
    """Universal job extractor using config"""
    jobs = []
    cards = []
    
    # Try each card selector
    for card_selector in selectors_config.get('card_selectors', []):
        cards = soup.select(card_selector)
        if cards:
            break
    
    if not cards:
        cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"], [class*="opening"]')[:20]
    
    for card in cards:
        title = ''
        company = ''
        location = ''
        
        # Extract title
        for sel in selectors_config.get('title_selectors', []):
            elem = card.select_one(sel) if card else None
            if elem:
                title = elem.text.strip()
                if title and len(title) > 3:
                    break
        
        # Extract company
        for sel in selectors_config.get('company_selectors', []):
            elem = card.select_one(sel) if card else None
            if elem:
                company = elem.text.strip()
                if company and company != title:
                    break
        
        # Extract location
        for sel in selectors_config.get('location_selectors', []):
            elem = card.select_one(sel) if card else None
            if elem:
                location = elem.text.strip()
                if location:
                    break
        
        # Extract link
        job_link = ''
        link_sel = selectors_config.get('link_selector', 'a')
        link_elem = card.select_one(link_sel) if card else None
        if link_elem:
            href = link_elem.get('href', '')
            if href:
                job_link = urljoin(url, href)
        
        if title and len(title) > 3:
            jobs.append(standardize_job({
                'title': title,
                'company': company or 'Company',
                'location': location or 'India',
                'apply_method': 'website',
                'apply_website': job_link or url,
                'source_url': job_link or url,
            }))
    
    return jobs[:10]

# ============================================================
# GENERIC FALLBACK SCRAPER
# ============================================================

def generic_scrape(url, name):
    """Generic scraper that tries to find any jobs on any website"""
    jobs = []
    try:
        response = safe_request(url, timeout=10)
        if not response:
            return jobs
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strategy 1: Find all links with job-related text
        job_keywords = ['job', 'career', 'vacancy', 'opening', 'position', 'hiring', 'apply']
        
        for link in soup.select('a[href]'):
            text = link.text.strip().lower()
            href = link.get('href', '').lower()
            
            if any(kw in text or kw in href for kw in job_keywords):
                if len(text) > 10 and len(text) < 150:
                    jobs.append(standardize_job({
                        'title': link.text.strip()[:200],
                        'company': name,
                        'location': 'India',
                        'apply_method': 'website',
                        'apply_website': urljoin(url, link.get('href', '')),
                        'source_url': urljoin(url, link.get('href', '')),
                    }))
        
        # Strategy 2: Look for heading + paragraph patterns
        if not jobs:
            for heading in soup.select('h2, h3, h4'):
                text = heading.text.strip()
                if len(text) > 10 and len(text) < 150:
                    next_elem = heading.find_next_sibling()
                    company = next_elem.text.strip() if next_elem else name
                    
                    jobs.append(standardize_job({
                        'title': text,
                        'company': company[:200],
                        'location': 'India',
                        'apply_method': 'website',
                        'apply_website': url,
                        'source_url': url,
                    }))
        
        return jobs[:5]
    except Exception as e:
        print(f"Generic scrape error: {str(e)[:100]}")
        return jobs

# ============================================================
# MAIN SCRAPER FUNCTION
# ============================================================

def scrape_all_websites():
    """Scrape all configured websites"""
    all_jobs = []
    total_sources = len(WEBSITE_CONFIGS)
    successful = 0
    
    print(f"\n{'='*60}")
    print(f"🔍 SCRAPING {total_sources} JOB WEBSITES...")
    print(f"{'='*60}")
    
    for name, config in WEBSITE_CONFIGS.items():
        try:
            source_jobs = []
            urls = config.get('urls', [])
            
            for url in urls[:2]:
                print(f"  📡 {name}: {url[:80]}...")
                response = safe_request(url, timeout=10)
                
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    jobs = extract_jobs_from_html(soup, url, config)
                    source_jobs.extend(jobs)
                    
                    if jobs:
                        break
            
            # If config didn't work, try generic
            if not source_jobs and urls:
                print(f"  🔄 {name}: Trying generic scraper...")
                source_jobs = generic_scrape(urls[0], name)
            
            if source_jobs:
                successful += 1
                all_jobs.extend(source_jobs)
                print(f"  ✅ {name}: {len(source_jobs)} jobs")
            else:
                print(f"  ⚠️ {name}: 0 jobs")
                
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:80]}")
    
    print(f"\n📊 Results: {successful}/{total_sources} sources successful")
    print(f"📊 Total jobs scraped: {len(all_jobs)}")
    
    # Save to database
    if all_jobs:
        added = 0
        skipped = 0
        
        # Delete old scraped jobs (older than 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        Job.query.filter(Job.source == 'scraped', Job.posted_date < seven_days_ago).delete()
        
        for job_data in all_jobs:
            existing = Job.query.filter_by(
                title=job_data['title'],
                company=job_data['company'],
                source='scraped'
            ).first()
            
            if not existing:
                try:
                    job = Job(**job_data)
                    db.session.add(job)
                    added += 1
                except Exception as e:
                    print(f"⚠️ Error adding job: {str(e)[:100]}")
                    skipped += 1
            else:
                skipped += 1
        
        db.session.commit()
        print(f"💾 Added {added} new, Skipped {skipped} duplicates")
    
    return len(all_jobs)

# ============================================================
# SCHEDULER
# ============================================================

def start_job_scraper(app):
    """Start scraper thread"""
    def run():
        time.sleep(5)
        print("\n🚀 Initial job scraping...")
        with app.app_context():
            scrape_all_websites()
        
        while True:
            time.sleep(3600)  # 1 hour
            print("\n🔄 Scheduled scraping...")
            with app.app_context():
                scrape_all_websites()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🔄 Job scraper started (runs every 1 hour)")

# ============================================================
# ROUTES
# ============================================================

@scraper_bp.route('/scrape-jobs-now')
def scrape_jobs_now():
    """Manual trigger for job scraping"""
    try:
        count = scrape_all_websites()
        if count > 0:
            flash(f'✅ Successfully scraped {count} jobs!', 'success')
        else:
            flash('⚠️ No jobs could be scraped. Websites may be blocking requests.', 'warning')
    except Exception as e:
        flash(f'❌ Scraping failed: {str(e)[:100]}', 'error')
    
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/api/scrape-status')
def scrape_status():
    """Get scraping status"""
    job_count = Job.query.filter_by(source='scraped', is_active=True).count()
    latest_job = Job.query.filter_by(source='scraped').order_by(Job.posted_date.desc()).first()
    
    return jsonify({
        'total_scraped_jobs': job_count,
        'last_scraped': latest_job.posted_date.strftime('%d %b, %Y %H:%M') if latest_job else 'Never',
        'sources': list(WEBSITE_CONFIGS.keys())
    })

@scraper_bp.route('/debug-scrape/<source>')
def debug_scrape(source):
    """Debug endpoint to see raw HTML structure"""
    config = WEBSITE_CONFIGS.get(source)
    if not config:
        return f"<h2>Invalid source: {source}</h2><p>Available: {', '.join(WEBSITE_CONFIGS.keys())}</p>"
    
    url = config['urls'][0]
    response = safe_request(url, timeout=20)
    
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Show all unique class names
        classes = set()
        for elem in soup.select('[class]'):
            for cls in elem.get('class', []):
                if any(kw in cls.lower() for kw in ['job', 'title', 'company', 'location', 'salary', 'card', 'result', 'list']):
                    classes.add(cls)
        
        # Show sample HTML
        sample = ''
        for selector in config['card_selectors'][:3]:
            cards = soup.select(selector)
            if cards:
                sample += f"\n\n=== Selector: {selector} (Found: {len(cards)}) ===\n"
                sample += str(cards[0])[:1500]
                break
        
        return f"""
        <html><head><title>Debug: {source}</title>
        <style>body{{font-family:sans-serif;padding:20px;background:#f5f5f5}}pre{{background:#fff;padding:15px;border-radius:8px;overflow-x:auto;font-size:12px}}ul{{columns:2}}</style>
        </head><body>
        <h1>Debug: {source}</h1>
        <p>URL: <a href="{url}" target="_blank">{url}</a></p>
        <h3>Relevant Classes Found ({len(classes)}):</h3>
        <ul>{"".join(f'<li>{c}</li>' for c in sorted(classes))}</ul>
        <h3>Sample HTML:</h3>
        <pre>{sample}</pre>
        </body></html>
        """
    
    return f"<h2>Failed to fetch {url}</h2>"