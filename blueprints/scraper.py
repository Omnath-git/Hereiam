# blueprints/scraper.py
import threading
import time
import random
import re
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, flash, redirect, url_for

from models import db, Job, ScrapeWebsite, ScrapeKeyword, ScrapeLocation

scraper_bp = Blueprint('scraper', __name__)

# ============================================================
# CONFIGURATION
# ============================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
]

# ⭐ Global flag - database operation in progress?
db_operation_in_progress = False
db_lock = threading.Lock()

# Track which websites have been scraped
scraped_websites_tracker = {}  # {site_id: last_scraped_time}
scraped_keywords_tracker = {}  # {keyword_id: last_used_time}

# ============================================================
# SCRAPING STATS
# ============================================================

class ScrapeStats:
    def __init__(self):
        self.total = 0
        self.done = 0
        self.success = 0
        self.found = 0
        self.added = 0
        self.current = ""
        self.running = False
        self.paused = False
        self.pause_reason = ""

scrape_stats = ScrapeStats()

# ============================================================
# ⭐ DATABASE OPERATION LOCK
# ============================================================

def wait_for_db_ready(timeout=30):
    """डेटाबेस फ्री होने का इंतजार करें"""
    start = time.time()
    while db_operation_in_progress:
        if time.time() - start > timeout:
            print("⚠️ DB lock timeout, proceeding anyway...")
            break
        time.sleep(0.5)
        scrape_stats.paused = True
        scrape_stats.pause_reason = "Waiting for DB operation to complete..."

def mark_db_operation_start():
    """डेटाबेस ऑपरेशन शुरू होने का mark करें"""
    global db_operation_in_progress
    db_operation_in_progress = True

def mark_db_operation_end():
    """डेटाबेस ऑपरेशन खत्म होने का mark करें"""
    global db_operation_in_progress
    db_operation_in_progress = False
    scrape_stats.paused = False
    scrape_stats.pause_reason = ""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
    }

def safe_request(url, timeout=10, retries=2):
    for _ in range(retries):
        try:
            r = requests.get(url, headers=get_headers(), timeout=timeout)
            if r.status_code == 200:
                return r
            time.sleep(1)
        except:
            time.sleep(2)
    return None

def clean_text(t):
    return re.sub(r'\s+', ' ', t).strip()[:300] if t else ""

def standardize_job(j):
    return {
        'title': clean_text(j.get('title', ''))[:200],
        'company': clean_text(j.get('company', 'Unknown'))[:200],
        'location': clean_text(j.get('location', 'India'))[:200],
        'salary_range': clean_text(j.get('salary_range', 'Not Disclosed'))[:100],
        'experience_required': clean_text(j.get('experience_required', 'Not Specified'))[:50],
        'job_type': clean_text(j.get('job_type', 'Full-time'))[:50],
        'description': clean_text(j.get('description', ''))[:500],
        'requirements': clean_text(j.get('requirements', ''))[:500],
        'skills_required': clean_text(j.get('skills_required', ''))[:500],
        'apply_method': j.get('apply_method', 'website'),
        'apply_email': j.get('apply_email', ''),
        'apply_website': j.get('apply_website', ''),
        'source': 'scraped',
        'source_url': j.get('source_url', ''),
        'is_active': True,
        'posted_date': datetime.utcnow(),
        'last_updated': datetime.utcnow()
    }

def extract_jobs(soup, url, config):
    """Generic job extractor"""
    jobs = []
    
    # Use configured selectors or fallback
    card_selectors = json.loads(config.get('card_selectors', '[]') or '[]')
    if not card_selectors:
        card_selectors = ['.job-card', '[class*="job"]', 'article', 'li', '.result-card']
    
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break
    
    if not cards:
        cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"]')[:30]
    
    for card in cards:
        title = company = location = ''
        
        # Title
        title_selectors = json.loads(config.get('title_selectors', '[]') or '[]')
        if not title_selectors:
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.job-title', 'a strong']
        for sel in title_selectors:
            e = card.select_one(sel)
            if e and len(e.text.strip()) > 3:
                title = e.text.strip()
                break
        
        # Company
        company_selectors = json.loads(config.get('company_selectors', '[]') or '[]')
        if not company_selectors:
            company_selectors = ['.company', '.employer', '.org', '.company-name']
        for sel in company_selectors:
            e = card.select_one(sel)
            if e and e.text.strip() != title:
                company = e.text.strip()
                break
        
        # Location
        location_selectors = json.loads(config.get('location_selectors', '[]') or '[]')
        if not location_selectors:
            location_selectors = ['.location', '[class*="location"]', '.city']
        for sel in location_selectors:
            e = card.select_one(sel)
            if e and e.text.strip():
                location = e.text.strip()
                break
        
        # Link
        link = ''
        link_sel = config.get('link_selector', 'a') or 'a'
        a = card.select_one(link_sel) or card.select_one('a[href]')
        if a:
            href = a.get('href', '')
            if href:
                link = urljoin(url, href)
        
        if title and len(title) > 3:
            jobs.append(standardize_job({
                'title': title,
                'company': company or 'Company',
                'location': location or 'India',
                'apply_website': link or url,
                'source_url': link or url
            }))
    
    return jobs[:5]


def scrape_single_site(config, keyword, location):
    """Single site scrape"""
    try:
        url = config['base_url']
        if not config.get('is_static_url'):
            url = url.replace('{keyword}', quote(keyword)).replace('{location}', quote(location))
        
        r = safe_request(url)
        if r:
            return extract_jobs(BeautifulSoup(r.text, 'html.parser'), url, config)
    except:
        pass
    return []


# ============================================================
# ⭐ SMART SAVE WITH DB LOCK HANDLING
# ============================================================

def save_jobs_safely(jobs_batch):
    """Save jobs with database lock handling"""
    if not jobs_batch:
        return 0
    
    added = 0
    
    # ⭐ Mark DB operation start
    mark_db_operation_start()
    
    try:
        for j in jobs_batch:
            # Check duplicate
            existing = Job.query.filter_by(
                title=j['title'], company=j['company'], source='scraped'
            ).first()
            
            if not existing:
                try:
                    db.session.add(Job(**j))
                    added += 1
                except:
                    pass
        
        if added > 0:
            # Retry commit with lock handling
            for attempt in range(10):  # ⭐ 10 retries
                try:
                    db.session.commit()
                    break
                except Exception as e:
                    db.session.rollback()
                    if 'database is locked' in str(e) and attempt < 9:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    raise e
    finally:
        # ⭐ Mark DB operation end
        mark_db_operation_end()
    
    return added


# ============================================================
# ⭐ RANDOM WEBSITE/KEWORD/LOCATION SELECTION
# ============================================================

def get_random_website(websites):
    """Random website select करें - जो recently scraped न हुआ हो"""
    if not websites:
        return None
    
    now = datetime.utcnow()
    
    # Priority 1: जो websites पिछले 30 मिनट में scraped नहीं हुईं
    fresh_sites = []
    for site in websites:
        last_scraped = scraped_websites_tracker.get(site.id)
        if not last_scraped or (now - last_scraped).seconds > 1800:  # 30 minutes
            fresh_sites.append(site)
    
    if fresh_sites:
        return random.choice(fresh_sites)
    
    # Priority 2: कम priority वाली sites
    low_priority = [s for s in websites if s.priority >= 2]
    if low_priority:
        return random.choice(low_priority)
    
    # Fallback: कोई भी random
    return random.choice(websites)


def get_random_keyword(keywords):
    """Random keyword select करें"""
    if not keywords:
        return 'software developer'
    
    # ⭐ हाल में use हुए keywords को कम priority दें
    now = datetime.utcnow()
    fresh_keywords = []
    
    for kw in keywords:
        last_used = scraped_keywords_tracker.get(kw.id)
        if not last_used or (now - last_used).seconds > 600:  # 10 minutes
            fresh_keywords.append(kw)
    
    if fresh_keywords:
        selected = random.choice(fresh_keywords)
    else:
        selected = random.choice(keywords)
    
    scraped_keywords_tracker[selected.id] = now
    return selected.keyword


def get_random_location(locations):
    """Random location select करें"""
    if not locations:
        return 'India'
    return random.choice(locations).location


# ============================================================
# CLEANUP
# ============================================================

def delete_old_jobs():
    """Delete scraped jobs older than 30 days"""
    mark_db_operation_start()
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        d = Job.query.filter(
            Job.source == 'scraped',
            Job.posted_date < thirty_days_ago
        ).delete()
        if d:
            db.session.commit()
            print(f"🗑️ Deleted {d} old jobs (30+ days)")
        return d or 0
    except:
        db.session.rollback()
        return 0
    finally:
        mark_db_operation_end()


# ============================================================
# ⭐ MAIN SCRAPE FUNCTION
# ============================================================

def run_scrape(full=False):
    """Main scraping function with smart scheduling"""
    global scrape_stats
    
    # ⭐ Wait for any pending DB operation
    wait_for_db_ready(timeout=10)
    
    # Clean old jobs first
    delete_old_jobs()
    
    # Get data from database
    websites = ScrapeWebsite.query.filter_by(is_active=True).order_by(ScrapeWebsite.priority).all()
    keywords = ScrapeKeyword.query.filter_by(is_active=True).order_by(ScrapeKeyword.priority).all()
    locations = ScrapeLocation.query.filter_by(is_active=True).order_by(ScrapeLocation.priority).all()
    
    # Seed if empty
    if not websites:
        from seed_scraper_data import seed_all
        seed_all()
        websites = ScrapeWebsite.query.filter_by(is_active=True).all()
        keywords = ScrapeKeyword.query.filter_by(is_active=True).all()
        locations = ScrapeLocation.query.filter_by(is_active=True).all()
    
    if not websites or not keywords:
        print("⚠️ No websites or keywords configured!")
        return 0
    
    scrape_stats = ScrapeStats()
    scrape_stats.running = True
    
    # Determine how many sites to scrape
    sites_to_scrape = len(websites) if full else min(5, len(websites))
    
    print(f"\n{'='*60}")
    print(f"🕷️ SMART SCRAPING: {sites_to_scrape}/{len(websites)} sites")
    print(f"   Keywords: {len(keywords)} | Locations: {len(locations)}")
    print(f"{'='*60}")
    
    total_added = 0
    all_jobs = []
    
    for i in range(sites_to_scrape):
        # ⭐ RANDOM website select करें
        website = get_random_website(websites)
        if not website:
            continue
        
        scrape_stats.current = website.name
        scrape_stats.done = i + 1
        scrape_stats.total = sites_to_scrape
        
        config = {
            'base_url': website.base_url,
            'card_selectors': website.card_selectors,
            'title_selectors': website.title_selectors,
            'company_selectors': website.company_selectors,
            'location_selectors': website.location_selectors,
            'link_selector': website.link_selector,
            'is_static_url': website.is_static_url,
        }
        
        site_jobs = []
        
        # Scrape with 2 random keywords and 1 random location
        for _ in range(2 if full else 1):
            kw = get_random_keyword(keywords)
            loc = get_random_location(locations)
            
            # ⭐ Check DB lock before scraping
            wait_for_db_ready(timeout=5)
            
            jobs = scrape_single_site(config, kw, loc)
            if jobs:
                site_jobs.extend(jobs)
                all_jobs.extend(jobs)
            
            # ⭐ Save every 20 jobs (not too frequent)
            if len(all_jobs) >= 20:
                added = save_jobs_safely(all_jobs)
                total_added += added
                scrape_stats.added += added
                scrape_stats.found += len(all_jobs)
                print(f"  💾 +{added} jobs saved (total: {total_added})")
                all_jobs = []
        
        # Update tracker
        scraped_websites_tracker[website.id] = datetime.utcnow()
        
        if site_jobs:
            scrape_stats.success += 1
            
            # Update website stats safely
            wait_for_db_ready(timeout=5)
            mark_db_operation_start()
            try:
                website.last_scraped = datetime.utcnow()
                website.jobs_found = len(site_jobs)
                db.session.commit()
            except:
                db.session.rollback()
            finally:
                mark_db_operation_end()
            
            print(f"  ✅ {website.name}: {len(site_jobs)} jobs")
        else:
            print(f"  ⚠️ {website.name}: No jobs")
        
        # ⭐ 10 मिनट का gap between sites (user operations के लिए)
        if i < sites_to_scrape - 1:
            print(f"  ⏸️ Waiting 10 minutes before next site...")
            time.sleep(600)  # 10 minutes
    
    # Save remaining jobs
    if all_jobs:
        added = save_jobs_safely(all_jobs)
        total_added += added
        scrape_stats.added += added
        scrape_stats.found += len(all_jobs)
    
    scrape_stats.running = False
    print(f"\n📊 SCRAPE COMPLETE: {total_added} new jobs from {scrape_stats.success} sites")
    return total_added


# ============================================================
# LIGHTWEIGHT SCRAPE (for scheduled runs)
# ============================================================

def scrape_lightweight():
    """Quick scrape - 3 random sites"""
    return run_scrape(full=False)


# ============================================================
# SCHEDULER - Every 20 hours with smart restart
# ============================================================

def start_job_scraper(app):
    """Start scraper in background"""
    def run():
        time.sleep(30)
        with app.app_context():
            print("\n🚀 Initial lightweight scrape...")
            scrape_lightweight()
        
        while True:
            time.sleep(72000)  # ⭐ 20 hours
            with app.app_context():
                print("\n🔄 Scheduled scrape...")
                scrape_lightweight()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🔄 Smart Scraper: Random sites + 10min gaps + DB lock handling + Auto-delete 30d")


# ============================================================
# ROUTES
# ============================================================

@scraper_bp.route('/scrape-jobs-now')
def scrape_now():
    try:
        c = run_scrape(full=True)
        flash(f'✅ {c} jobs scraped from random sites!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/scrape-light')
def scrape_light():
    try:
        c = scrape_lightweight()
        flash(f'✅ Light scrape: {c} jobs!', 'success')
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
        'paused': scrape_stats.paused,
        'pause_reason': scrape_stats.pause_reason,
        'progress': f"{scrape_stats.done}/{scrape_stats.total}" if scrape_stats.running else "Idle",
        'current': scrape_stats.current if scrape_stats.running else 'Idle',
        'added_today': scrape_stats.added,
        'db_locked': db_operation_in_progress,
    })