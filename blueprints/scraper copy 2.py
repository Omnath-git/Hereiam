# blueprints/scraper.py
import threading
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, flash, redirect, url_for

from models import db, Job

scraper_bp = Blueprint('scraper', __name__)

# ============================================================
# CONFIGURATION
# ============================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
]

# ⭐ MULTI-DOMAIN SEARCH KEYWORDS
SEARCH_KEYWORDS = {
    # IT & Software
    'software_developer': ['software developer', 'software engineer', 'programmer', 'web developer', 'full stack developer'],
    'python_developer': ['python developer', 'django developer', 'python engineer', 'flask developer'],
    'java_developer': ['java developer', 'java engineer', 'spring boot developer', 'j2ee developer'],
    'javascript_developer': ['javascript developer', 'react developer', 'angular developer', 'vue.js developer', 'node.js developer'],
    'dotnet_developer': ['.net developer', 'c# developer', 'asp.net developer', '.net core developer'],
    'php_developer': ['php developer', 'laravel developer', 'wordpress developer', 'php engineer'],
    'mobile_developer': ['android developer', 'ios developer', 'react native developer', 'flutter developer'],
    'devops_engineer': ['devops engineer', 'cloud engineer', 'aws engineer', 'azure engineer', 'kubernetes engineer'],
    'data_scientist': ['data scientist', 'data analyst', 'machine learning engineer', 'ai engineer', 'nlp engineer'],
    'cybersecurity': ['cybersecurity analyst', 'security engineer', 'ethical hacker', 'penetration tester', 'security consultant'],
    'qa_engineer': ['qa engineer', 'test engineer', 'automation tester', 'quality analyst', 'sdet'],
    'database_admin': ['database administrator', 'dba', 'sql developer', 'data engineer', 'etl developer'],
    'system_admin': ['system administrator', 'network engineer', 'it support', 'helpdesk', 'technical support'],
    'ui_ux': ['ui designer', 'ux designer', 'product designer', 'graphic designer', 'visual designer'],
    
    # Management & Business
    'project_manager': ['project manager', 'program manager', 'scrum master', 'agile coach', 'delivery manager'],
    'product_manager': ['product manager', 'product owner', 'business analyst', 'product analyst'],
    'hr_recruitment': ['hr manager', 'recruiter', 'talent acquisition', 'hr executive', 'hr generalist'],
    'finance_accounting': ['accountant', 'finance manager', 'financial analyst', 'chartered accountant', 'auditor'],
    'marketing_sales': ['marketing manager', 'digital marketing', 'seo specialist', 'sales executive', 'business development'],
    'operations': ['operations manager', 'supply chain', 'logistics', 'warehouse manager', 'procurement'],
    'customer_service': ['customer support', 'customer service', 'call center', 'bpo', 'client relationship'],
    
    # Healthcare
    'doctor': ['doctor', 'physician', 'surgeon', 'medical officer', 'general practitioner'],
    'nurse': ['nurse', 'staff nurse', 'nursing officer', 'registered nurse', 'healthcare assistant'],
    'pharmacist': ['pharmacist', 'pharmacy assistant', 'medical representative', 'drug safety'],
    'lab_technician': ['lab technician', 'medical lab technologist', 'pathology technician', 'radiology technician'],
    'healthcare_admin': ['hospital administrator', 'healthcare manager', 'medical coder', 'medical billing'],
    
    # Education
    'teacher': ['teacher', 'professor', 'lecturer', 'faculty', 'teaching assistant', 'education coordinator'],
    'principal': ['principal', 'vice principal', 'school administrator', 'academic coordinator'],
    'counselor': ['counselor', 'student counselor', 'career counselor', 'admission counselor'],
    
    # Engineering (Non-IT)
    'civil_engineer': ['civil engineer', 'structural engineer', 'construction engineer', 'site engineer'],
    'mechanical_engineer': ['mechanical engineer', 'design engineer', 'production engineer', 'quality engineer'],
    'electrical_engineer': ['electrical engineer', 'electronics engineer', 'instrumentation engineer'],
    'chemical_engineer': ['chemical engineer', 'process engineer', 'safety engineer'],
    
    # Legal
    'lawyer': ['lawyer', 'attorney', 'legal advisor', 'legal counsel', 'advocate'],
    'legal_officer': ['legal officer', 'compliance officer', 'company secretary', 'legal assistant'],
    
    # Content & Media
    'content_writer': ['content writer', 'copywriter', 'technical writer', 'blogger', 'content strategist'],
    'journalist': ['journalist', 'reporter', 'editor', 'news anchor', 'correspondent'],
    'video_editor': ['video editor', 'video producer', 'animator', 'motion graphics', 'multimedia'],
    'photographer': ['photographer', 'videographer', 'photo editor', 'cinematographer'],
    
    # Government & NGO
    'government_jobs': ['government job', 'sarkari naukri', 'public sector', 'psu jobs', 'civil services'],
    'banking': ['banking', 'bank job', 'bank po', 'bank clerk', 'relationship manager', 'insurance'],
    'ngo_social': ['ngo', 'social worker', 'development sector', 'humanitarian', 'nonprofit', 'csr'],
    
    # Fresher & Entry Level
    'fresher': ['fresher', 'trainee', 'intern', 'entry level', 'graduate trainee', 'apprentice'],
    'work_from_home': ['work from home', 'remote job', 'work from anywhere', 'telecommute', 'virtual job'],
    
    # Sector Specific
    'manufacturing': ['manufacturing', 'factory', 'production', 'assembly', 'industrial'],
    'retail': ['retail', 'store manager', 'merchandiser', 'sales associate', 'cashier'],
    'hospitality': ['hotel', 'restaurant', 'chef', 'cook', 'housekeeping', 'front office'],
    'logistics': ['delivery', 'driver', 'warehouse', 'shipping', 'fleet manager'],
    'real_estate': ['real estate', 'property manager', 'broker', 'real estate agent'],
    'agriculture': ['agriculture', 'farming', 'agribusiness', 'food technology', 'horticulture'],
}

# ⭐ ALL INDIAN CITIES FOR LOCATION SEARCH
INDIAN_CITIES = [
    # Metro Cities
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
    # Tier 1
    'Jaipur', 'Lucknow', 'Indore', 'Bhopal', 'Chandigarh', 'Kochi', 'Coimbatore', 'Nagpur',
    'Surat', 'Vadodara', 'Noida', 'Gurgaon', 'Bhubaneswar', 'Visakhapatnam', 'Patna', 'Ranchi',
    # Tier 2
    'Agra', 'Allahabad', 'Amritsar', 'Aurangabad', 'Dehradun', 'Dhanbad', 'Gwalior', 'Jabalpur',
    'Jodhpur', 'Kanpur', 'Ludhiana', 'Madurai', 'Mangalore', 'Meerut', 'Mysore', 'Nashik',
    'Pondicherry', 'Raipur', 'Rajkot', 'Thiruvananthapuram', 'Varanasi', 'Vijayawada',
    # Pan-India
    'India', 'Remote', 'Anywhere in India',
]


WEBSITE_CONFIGS = {
    'linkedin': {
        'base_url': 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0',
        'card_selectors': ['.base-card', '.job-search-card', 'li'],
        'title_selectors': ['.base-search-card__title', '.job-search-card__title', 'h3'],
        'company_selectors': ['.base-search-card__subtitle', '.job-search-card__subtitle', 'h4'],
        'location_selectors': ['.job-search-card__location', '.location'],
        'link_selector': 'a.base-card__full-link',
    },
    'indeed': {
        'base_url': 'https://in.indeed.com/jobs?q={keyword}&l={location}',
        'card_selectors': ['.job_seen_beacon', '.cardOutline', '.resultContent', 'td.resultContent'],
        'title_selectors': ['h2.jobTitle', 'h2 span', 'a.jobTitle', '.title a'],
        'company_selectors': ['.companyName', '.company_name', 'span.companyName'],
        'location_selectors': ['.companyLocation', '.location', '.recJobLoc'],
        'link_selector': 'a.jobTitle',
    },
    'naukri': {
        'base_url': 'https://www.naukri.com/{keyword}-jobs?k={keyword}',
        'card_selectors': ['.jobTuple', '[class*="jobTuple"]', '.list-item', 'article'],
        'title_selectors': ['a.title', '.jobTuple-title', 'h2 a', '.title'],
        'company_selectors': ['.subTitle', '.companyName', '.orgName'],
        'location_selectors': ['.location', '.loc', '.fleft'],
        'link_selector': 'a.title',
    },
    'freshersworld': {
        'base_url': 'https://www.freshersworld.com/jobs?q={keyword}',
        'card_selectors': ['.job-container', '.job-list', '[class*="job"]'],
        'title_selectors': ['h3', '.job-title', 'a strong'],
        'company_selectors': ['.company-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'internshala': {
        'base_url': 'https://internshala.com/jobs/search?keyword={keyword}',
        'card_selectors': ['.individual_internship', '[class*="individual"]'],
        'title_selectors': ['h3', 'h4', '.heading_4_5', '.job-title'],
        'company_selectors': ['.company-name', '.company_name', '.link_display_like_text'],
        'location_selectors': ['.location', '#location_names'],
        'link_selector': 'a',
    },
    'apna': {
        'base_url': 'https://apna.co/jobs?q={keyword}',
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.employer-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'workindia': {
        'base_url': 'https://www.workindia.in/jobs?q={keyword}',
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'foundit': {
        'base_url': 'https://www.foundit.in/jobs?q={keyword}',
        'card_selectors': ['.jobCard', '[class*="job"]', '.card'],
        'title_selectors': ['h3', '.title', '[class*="title"]'],
        'company_selectors': ['.company', '.org', '[class*="company"]'],
        'location_selectors': ['.location', '[class*="location"]'],
        'link_selector': 'a',
    },
    'shine': {
        'base_url': 'https://www.shine.com/jobs/search?q={keyword}',
        'card_selectors': ['.jobCard', '.resultCard', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.company', '.org'],
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

def safe_request(url, timeout=15, max_retries=2):
    """Safe HTTP request with retry"""
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.headers.update(get_random_headers())
            response = session.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response
            time.sleep(1)
        except:
            time.sleep(2)
    return None

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:300]

def standardize_job(job_dict):
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

def extract_jobs_from_html(soup, url, config):
    """Extract jobs from HTML using config selectors"""
    jobs = []
    cards = []
    
    for card_selector in config.get('card_selectors', []):
        cards = soup.select(card_selector)
        if cards:
            break
    
    if not cards:
        cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"], [class*="opening"]')[:20]
    
    for card in cards:
        title = ''
        company = ''
        location = ''
        
        for sel in config.get('title_selectors', []):
            elem = card.select_one(sel)
            if elem:
                title = elem.text.strip()
                if title and len(title) > 3:
                    break
        
        for sel in config.get('company_selectors', []):
            elem = card.select_one(sel)
            if elem:
                company = elem.text.strip()
                if company and company != title:
                    break
        
        for sel in config.get('location_selectors', []):
            elem = card.select_one(sel)
            if elem:
                location = elem.text.strip()
                if location:
                    break
        
        job_link = ''
        link_elem = card.select_one(config.get('link_selector', 'a'))
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
    
    return jobs[:5]

def scrape_single_search(keyword, location, config):
    """Scrape jobs for a single keyword + location combination"""
    jobs = []
    try:
        url = config['base_url'].format(
            keyword=quote(keyword),
            location=quote(location)
        )
        
        response = safe_request(url, timeout=10)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = extract_jobs_from_html(soup, url, config)
    except:
        pass
    
    return jobs

# ============================================================
# ⭐ COMPREHENSIVE SCRAPER - ALL DOMAINS
# ============================================================

def scrape_all_domains():
    """Scrape jobs for ALL domains, sectors, and positions"""
    all_jobs = []
    total_searches = 0
    successful_searches = 0
    
    print(f"\n{'='*70}")
    print(f"🔍 COMPREHENSIVE JOB SCRAPING - ALL DOMAINS & SECTORS")
    print(f"{'='*70}")
    print(f"📋 Categories: {len(SEARCH_KEYWORDS)}")
    print(f"🏙️  Locations: {len(INDIAN_CITIES)}")
    print(f"🌐 Websites: {len(WEBSITE_CONFIGS)}")
    print(f"{'='*70}")
    
    # For each category
    for category_name, keywords in SEARCH_KEYWORDS.items():
        print(f"\n📂 Category: {category_name.upper()} ({len(keywords)} keywords)")
        
        # Pick 3 random keywords from this category (to save time)
        selected_keywords = random.sample(keywords, min(3, len(keywords)))
        
        # Pick 3 random major cities + "India" + "Remote"
        selected_locations = random.sample(INDIAN_CITIES[:15], 3) + ['India', 'Remote']
        
        for keyword in selected_keywords:
            for location in selected_locations:
                # Pick 2 random websites
                selected_sites = random.sample(list(WEBSITE_CONFIGS.keys()), min(2, len(WEBSITE_CONFIGS)))
                
                for site_name in selected_sites:
                    config = WEBSITE_CONFIGS[site_name]
                    total_searches += 1
                    
                    try:
                        jobs = scrape_single_search(keyword, location, config)
                        if jobs:
                            successful_searches += 1
                            all_jobs.extend(jobs)
                    except Exception as e:
                        pass
        
        print(f"  ✅ Found {len(all_jobs)} jobs so far...")
    
    print(f"\n{'='*70}")
    print(f"📊 SEARCH STATS:")
    print(f"   Total searches: {total_searches}")
    print(f"   Successful: {successful_searches}")
    print(f"   Jobs found: {len(all_jobs)}")
    print(f"{'='*70}")
    
    # Save to database
    if all_jobs:
        added = 0
        skipped = 0
        
        # Remove old scraped jobs (older than 7 days)
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
                except:
                    skipped += 1
            else:
                skipped += 1
        
        db.session.commit()
        print(f"💾 Added {added} new jobs, Skipped {skipped} duplicates")
        print(f"📊 Total scraped jobs in DB: {Job.query.filter_by(source='scraped', is_active=True).count()}")
    
    return len(all_jobs)

# ============================================================
# LIGHTWEIGHT SCRAPER (For scheduled runs - fewer searches)
# ============================================================

def scrape_lightweight():
    """Lightweight scraper for scheduled runs"""
    all_jobs = []
    
    # Pick 5 random categories
    selected_categories = random.sample(list(SEARCH_KEYWORDS.keys()), min(5, len(SEARCH_KEYWORDS)))
    
    for category_name in selected_categories:
        keywords = SEARCH_KEYWORDS[category_name]
        keyword = random.choice(keywords)
        location = random.choice(INDIAN_CITIES[:10] + ['India'])
        site_name = random.choice(list(WEBSITE_CONFIGS.keys()))
        config = WEBSITE_CONFIGS[site_name]
        
        try:
            jobs = scrape_single_search(keyword, location, config)
            all_jobs.extend(jobs)
        except:
            pass
    
    # Save to DB
    if all_jobs:
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
                except:
                    pass
        db.session.commit()
    
    return len(all_jobs)

# ============================================================
# SCHEDULER
# ============================================================

def start_job_scraper(app):
    """Start scraper thread"""
    def run():
        time.sleep(10)
        print("\n" + "="*70)
        print("🚀 INITIAL FULL JOB SCRAPING - ALL DOMAINS")
        print("="*70)
        with app.app_context():
            count = scrape_all_domains()
            print(f"✅ Initial scrape complete: {count} jobs\n")
        
        # Then lightweight scrape every 30 minutes
        while True:
            time.sleep(1800)  # 30 minutes
            print("\n🔄 Scheduled lightweight scraping...")
            with app.app_context():
                count = scrape_lightweight()
                print(f"✅ Scheduled scrape: {count} new jobs\n")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🔄 Job scraper started (Full scrape on start, light every 30 min)")

# ============================================================
# ROUTES
# ============================================================

@scraper_bp.route('/scrape-jobs-now')
def scrape_jobs_now():
    """Manual trigger - Full comprehensive scraping"""
    try:
        count = scrape_all_domains()
        if count > 0:
            flash(f'✅ Successfully scraped {count} jobs across all domains!', 'success')
        else:
            flash('⚠️ No jobs could be scraped.', 'warning')
    except Exception as e:
        flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/scrape-light')
def scrape_light():
    """Manual trigger - Lightweight scraping"""
    try:
        count = scrape_lightweight()
        flash(f'✅ Light scrape: {count} jobs found!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/api/scrape-status')
def scrape_status():
    """Get scraping status"""
    total = Job.query.filter_by(source='scraped', is_active=True).count()
    latest = Job.query.filter_by(source='scraped').order_by(Job.posted_date.desc()).first()
    
    # Count by source
    from sqlalchemy import func
    source_counts = db.session.query(
        Job.source_url, func.count(Job.id)
    ).filter_by(source='scraped', is_active=True).group_by(Job.source_url).all()
    
    return jsonify({
        'total_scraped_jobs': total,
        'last_scraped': latest.posted_date.strftime('%d %b, %Y %H:%M') if latest else 'Never',
        'categories': len(SEARCH_KEYWORDS),
        'sources': len(WEBSITE_CONFIGS),
        'locations': len(INDIAN_CITIES),
    })