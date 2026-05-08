import threading, time, random, re, json
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, flash, redirect, url_for
from models import db, Job, ScrapeWebsite, ScrapeKeyword, ScrapeLocation

scraper_bp = Blueprint('scraper', __name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
]

class ScrapeStats:
    def __init__(self):
        self.total = 0; self.done = 0; self.success = 0
        self.found = 0; self.added = 0; self.current = ""; self.running = False

scrape_stats = ScrapeStats()

def get_headers():
    return {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8'}

def safe_request(url, timeout=10, retries=2):
    for _ in range(retries):
        try:
            r = requests.get(url, headers=get_headers(), timeout=timeout)
            if r.status_code == 200: return r
            time.sleep(1)
        except: time.sleep(2)
    return None

def clean_text(t):
    return re.sub(r'\s+', ' ', t).strip()[:300] if t else ""

def standardize_job(j):
    return {
        'title': clean_text(j.get('title',''))[:200],
        'company': clean_text(j.get('company','Unknown'))[:200],
        'location': clean_text(j.get('location','India'))[:200],
        'salary_range': clean_text(j.get('salary_range','Not Disclosed'))[:100],
        'experience_required': clean_text(j.get('experience_required','Not Specified'))[:50],
        'job_type': clean_text(j.get('job_type','Full-time'))[:50],
        'description': clean_text(j.get('description',''))[:500],
        'requirements': clean_text(j.get('requirements',''))[:500],
        'skills_required': clean_text(j.get('skills_required',''))[:500],
        'apply_method': j.get('apply_method','website'),
        'apply_email': j.get('apply_email',''),
        'apply_website': j.get('apply_website',''),
        'source': 'scraped', 'source_url': j.get('source_url',''),
        'is_active': True, 'posted_date': datetime.utcnow(), 'last_updated': datetime.utcnow()
    }

def extract_jobs(soup, url, config):
    """Generic job extractor - works with any website structure"""
    jobs = []
    
    # Strategy 1: Use configured selectors
    for sel in json.loads(config.get('card_selectors','[]') or '[]') or ['.job-card', '[class*="job"]', 'article', 'li']:
        cards = soup.select(sel)
        if cards: break
    else:
        cards = []
    
    # Strategy 2: Find any job-like elements
    if not cards:
        cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"], [class*="opening"], [class*="listing"]')[:30]
    
    for card in cards:
        title = company = location = ''
        
        # Try all possible title selectors
        for sel in (json.loads(config.get('title_selectors','[]') or '[]') or ['h1','h2','h3','h4','h5','.title','.job-title','a strong','[class*="title"]']):
            e = card.select_one(sel)
            if e and len(e.text.strip()) > 3: title = e.text.strip(); break
        
        # Try all possible company selectors
        for sel in (json.loads(config.get('company_selectors','[]') or '[]') or ['.company','.employer','.org','.company-name','[class*="company"]','[class*="employer"]']):
            e = card.select_one(sel)
            if e and e.text.strip() != title: company = e.text.strip(); break
        
        # Try location
        for sel in (json.loads(config.get('location_selectors','[]') or '[]') or ['.location','[class*="location"]','.city']):
            e = card.select_one(sel)
            if e and e.text.strip(): location = e.text.strip(); break
        
        # Find link
        link = ''
        a = card.select_one(config.get('link_selector','a') or 'a') or card.select_one('a[href]')
        if a:
            href = a.get('href','')
            if href: link = urljoin(url, href)
        
        if title and len(title) > 3:
            jobs.append(standardize_job({'title': title, 'company': company or 'Company', 'location': location or 'India', 'apply_website': link or url, 'source_url': link or url}))
    
    return jobs[:5]

def scrape_site(config, keyword, location):
    try:
        url = config['base_url']
        if not config.get('is_static_url'):
            url = url.replace('{keyword}', quote(keyword)).replace('{location}', quote(location))
        r = safe_request(url)
        if r: return extract_jobs(BeautifulSoup(r.text, 'html.parser'), url, config)
    except: pass
    return []

def delete_old_jobs():
    d = Job.query.filter(Job.source=='scraped', Job.posted_date < datetime.utcnow()-timedelta(days=30)).delete()
    if d: db.session.commit(); print(f"🗑️ Deleted {d} old jobs")
    return d

def save_jobs_batch(jobs):
    added = 0
    for j in jobs:
        if not Job.query.filter_by(title=j['title'], company=j['company'], source='scraped').first():
            try:
                db.session.add(Job(**j)); added += 1
            except: pass
    if added:
        for _ in range(5):
            try: db.session.commit(); break
            except: db.session.rollback(); time.sleep(0.5)
    return added

def run_scrape(full=False):
    global scrape_stats
    delete_old_jobs()
    
    websites = ScrapeWebsite.query.filter_by(is_active=True).order_by(ScrapeWebsite.priority).all()
    keywords = ScrapeKeyword.query.filter_by(is_active=True).order_by(ScrapeKeyword.priority).all()
    locations = ScrapeLocation.query.filter_by(is_active=True).order_by(ScrapeLocation.priority).all()
    
    if not websites:
        # Seed default websites if empty
        seed_default_data()
        websites = ScrapeWebsite.query.filter_by(is_active=True).all()
        keywords = ScrapeKeyword.query.filter_by(is_active=True).all()
        locations = ScrapeLocation.query.filter_by(is_active=True).all()
    
    if not websites: return 0
    
    kw_list = [k.keyword for k in keywords] if keywords else ['software developer', 'python developer', 'data scientist', 'teacher', 'accountant', 'sales', 'marketing', 'hr', 'fresher', 'government job']
    loc_list = [l.location for l in locations] if locations else ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'India', 'Remote']
    
    scrape_stats = ScrapeStats()
    scrape_stats.total = len(websites)
    scrape_stats.running = True
    all_jobs = []
    
    print(f"🔍 Scraping {len(websites)} sites × {len(kw_list)} keywords × {len(loc_list)} locations")
    
    for i, site in enumerate(websites):
        scrape_stats.current = site.name
        scrape_stats.done = i + 1
        config = {'base_url': site.base_url, 'card_selectors': site.card_selectors, 'title_selectors': site.title_selectors, 'company_selectors': site.company_selectors, 'location_selectors': site.location_selectors, 'link_selector': site.link_selector, 'is_static_url': site.is_static_url}
        
        site_jobs = []
        # Pick random keywords & locations
        for kw in random.sample(kw_list, min(3 if full else 1, len(kw_list))):
            for loc in random.sample(loc_list, min(2 if full else 1, len(loc_list))):
                jobs = scrape_site(config, kw, loc)
                if jobs: site_jobs.extend(jobs); all_jobs.extend(jobs)
                if len(all_jobs) >= 50:
                    added = save_jobs_batch(all_jobs)
                    scrape_stats.added += added; scrape_stats.found += len(all_jobs)
                    print(f"  💾 +{added} jobs saved")
                    all_jobs = []
        
        if site_jobs:
            scrape_stats.success += 1
            site.last_scraped = datetime.utcnow()
            site.jobs_found = len(site_jobs)
            print(f"  ✅ {site.name}: {len(site_jobs)} jobs")
        else:
            print(f"  ⚠️ {site.name}: No jobs")
        db.session.commit()
    
    if all_jobs:
        added = save_jobs_batch(all_jobs)
        scrape_stats.added += added; scrape_stats.found += len(all_jobs)
    
    scrape_stats.running = False
    print(f"📊 Done: {scrape_stats.added} new jobs from {scrape_stats.success}/{scrape_stats.total} sites")
    return scrape_stats.added

def seed_default_data():
    """Seed default websites, keywords, locations if DB is empty"""
    if ScrapeWebsite.query.count() == 0:
        sites = [
            ScrapeWebsite(name='Naukri.com', base_url='https://www.naukri.com/{keyword}-jobs?k={keyword}', card_selectors='[".jobTuple"]', title_selectors='["a.title"]', company_selectors='[".subTitle"]', location_selectors='[".location"]', priority=1),
            ScrapeWebsite(name='Indeed India', base_url='https://in.indeed.com/jobs?q={keyword}&l={location}', card_selectors='[".job_seen_beacon"]', title_selectors='["h2.jobTitle"]', company_selectors='[".companyName"]', location_selectors='[".companyLocation"]', priority=1),
            ScrapeWebsite(name='LinkedIn Jobs', base_url='https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0', card_selectors='[".base-card"]', title_selectors='[".base-search-card__title"]', company_selectors='[".base-search-card__subtitle"]', location_selectors='[".job-search-card__location"]', priority=1),
            ScrapeWebsite(name='Foundit.in', base_url='https://www.foundit.in/jobs?q={keyword}', card_selectors='[".jobCard"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Shine.com', base_url='https://www.shine.com/jobs/search?q={keyword}', card_selectors='[".jobCard"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Freshersworld', base_url='https://www.freshersworld.com/jobs?q={keyword}', card_selectors='[".job-container"]', title_selectors='["h3"]', company_selectors='[".company-name"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Internshala', base_url='https://internshala.com/jobs/search?keyword={keyword}', card_selectors='[".individual_internship"]', title_selectors='["h3"]', company_selectors='[".company-name"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Apna.co', base_url='https://apna.co/jobs?q={keyword}', card_selectors='[".job-card"]', title_selectors='["h3"]', company_selectors='[".employer-name"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='WorkIndia', base_url='https://www.workindia.in/jobs?q={keyword}', card_selectors='[".job-card"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='TimesJobs', base_url='https://www.timesjobs.com/jobfunction/{keyword}-jobs', card_selectors='[".job-listing"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Google Jobs', base_url='https://www.google.com/search?q={keyword}+jobs+in+{location}&ibp=htl;jobs', card_selectors='["[class*=\\"job\\"]"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=3),
            ScrapeWebsite(name='CareerJet India', base_url='https://www.careerjet.co.in/search/jobs?q={keyword}', card_selectors='[".job-listing"]', title_selectors='["h3"]', company_selectors='[".company"]', location_selectors='[".location"]', priority=3),
            ScrapeWebsite(name='SAMS Social Sector', base_url='https://www.sams.co.in/Jobs/job-list', card_selectors='["article"]', title_selectors='["h3","h4"]', company_selectors='[".company"]', location_selectors='[".location"]', is_static_url=True, priority=2),
            ScrapeWebsite(name='DevNetJobs India', base_url='https://devnetjobsindia.org/?s={keyword}', card_selectors='[".job-listing"]', title_selectors='["h3"]', company_selectors='[".organization"]', location_selectors='[".location"]', priority=2),
            ScrapeWebsite(name='Idealist.org', base_url='https://www.idealist.org/en/jobs?q={keyword}&location=India', card_selectors='[".job-listing"]', title_selectors='["h3"]', company_selectors='[".organization"]', location_selectors='[".location"]', priority=3),
        ]
        db.session.add_all(sites)
    
    if ScrapeKeyword.query.count() == 0:
        kws = [
            ('it', 'software developer'), ('it', 'python developer'), ('it', 'java developer'), ('it', 'react developer'), ('it', 'node.js developer'), ('it', 'full stack developer'), ('it', 'devops engineer'), ('it', 'data scientist'), ('it', 'machine learning engineer'), ('it', 'cybersecurity analyst'), ('it', 'qa engineer'), ('it', 'ui ux designer'), ('it', 'database administrator'), ('it', 'system administrator'), ('it', 'cloud architect'),
            ('management', 'project manager'), ('management', 'product manager'), ('management', 'business analyst'), ('management', 'scrum master'),
            ('hr', 'hr manager'), ('hr', 'recruiter'), ('hr', 'talent acquisition'),
            ('finance', 'accountant'), ('finance', 'finance manager'), ('finance', 'chartered accountant'),
            ('marketing', 'marketing manager'), ('marketing', 'digital marketing'), ('marketing', 'sales executive'), ('marketing', 'business development'),
            ('healthcare', 'doctor'), ('healthcare', 'nurse'), ('healthcare', 'pharmacist'), ('healthcare', 'medical officer'),
            ('education', 'teacher'), ('education', 'professor'), ('education', 'lecturer'), ('education', 'faculty'),
            ('engineering', 'civil engineer'), ('engineering', 'mechanical engineer'), ('engineering', 'electrical engineer'),
            ('legal', 'lawyer'), ('legal', 'legal advisor'), ('legal', 'compliance officer'),
            ('government', 'government job'), ('government', 'sarkari naukri'), ('government', 'psu jobs'), ('government', 'bank job'),
            ('ngo', 'program manager ngo'), ('ngo', 'social worker'), ('ngo', 'fundraising'), ('ngo', 'development sector'),
            ('fresher', 'fresher'), ('fresher', 'trainee'), ('fresher', 'intern'), ('fresher', 'entry level'),
            ('other', 'data entry'), ('other', 'customer service'), ('other', 'delivery'), ('other', 'security guard'), ('other', 'housekeeping'), ('other', 'electrician'), ('other', 'beautician'), ('other', 'receptionist'), ('other', 'cook'), ('other', 'supervisor'),
        ]
        for cat, kw in kws:
            db.session.add(ScrapeKeyword(category=cat, keyword=kw))
    
    if ScrapeLocation.query.count() == 0:
        locs = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Noida', 'Gurgaon', 'Indore', 'Bhopal', 'Chandigarh', 'Kochi', 'Coimbatore', 'Nagpur', 'Surat', 'Patna', 'Ranchi', 'Bhubaneswar', 'Dehradun', 'Guwahati', 'India', 'Remote', 'Work from Home']
        for l in locs:
            db.session.add(ScrapeLocation(location=l))
    
    db.session.commit()
    print("✅ Default scraper data seeded!")

def start_job_scraper(app):
    def run():
        time.sleep(10)
        with app.app_context():
            seed_default_data()
            print("🚀 Initial scrape...")
            run_scrape(full=True)
        while True:
            time.sleep(72000)  # 20 hours
            with app.app_context():
                run_scrape(full=False)
    threading.Thread(target=run, daemon=True).start()
    print("🔄 Scraper started (every 20h, auto-delete 30d)")

@scraper_bp.route('/scrape-jobs-now')
def scrape_now():
    try:
        c = run_scrape(full=True)
        flash(f'✅ {c} jobs scraped!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/api/scrape-status')
def status():
    return jsonify({
        'total_jobs': Job.query.filter_by(source='scraped', is_active=True).count(),
        'websites': ScrapeWebsite.query.filter_by(is_active=True).count(),
        'keywords': ScrapeKeyword.query.filter_by(is_active=True).count(),
        'locations': ScrapeLocation.query.filter_by(is_active=True).count(),
        'running': scrape_stats.running,
        'progress': f"{scrape_stats.done}/{scrape_stats.total}" if scrape_stats.running else "Idle",
        'current': scrape_stats.current if scrape_stats.running else 'Idle',
        'added_today': scrape_stats.added,
    })