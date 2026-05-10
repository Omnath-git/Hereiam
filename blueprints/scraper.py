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

# ⭐ Scraper Control Flags
scraper_control = {
    'enabled': True,
    'paused': False,
    'stop_requested': False,
}

# Trackers for random selection
scraped_websites_tracker = {}
scraped_keywords_tracker = {}


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
# HELPER FUNCTIONS
# ============================================================

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive', 'DNT': '1',
    }

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
        'title': clean_text(j.get('title',''))[:200], 'company': clean_text(j.get('company','Unknown'))[:200],
        'location': clean_text(j.get('location','India'))[:200], 'salary_range': clean_text(j.get('salary_range','Not Disclosed'))[:100],
        'experience_required': clean_text(j.get('experience_required','Not Specified'))[:50], 'job_type': clean_text(j.get('job_type','Full-time'))[:50],
        'description': clean_text(j.get('description',''))[:500], 'requirements': clean_text(j.get('requirements',''))[:500],
        'skills_required': clean_text(j.get('skills_required',''))[:500], 'apply_method': j.get('apply_method','website'),
        'apply_email': j.get('apply_email',''), 'apply_website': j.get('apply_website',''),
        'source': 'scraped', 'source_url': j.get('source_url',''), 'is_active': True,
        'posted_date': datetime.utcnow(), 'last_updated': datetime.utcnow()
    }

def extract_jobs(soup, url, config):
    """Generic job extractor"""
    jobs = []
    card_selectors = json.loads(config.get('card_selectors','[]') or '[]') or ['.job-card','[class*="job"]','article','li']
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards: break
    if not cards: cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"]')[:30]
    
    for card in cards:
        title = company = location = ''
        for sel in (json.loads(config.get('title_selectors','[]') or '[]') or ['h1','h2','h3','.title','.job-title']):
            e = card.select_one(sel)
            if e and len(e.text.strip()) > 3: title = e.text.strip(); break
        for sel in (json.loads(config.get('company_selectors','[]') or '[]') or ['.company','.employer','.org']):
            e = card.select_one(sel)
            if e and e.text.strip() != title: company = e.text.strip(); break
        for sel in (json.loads(config.get('location_selectors','[]') or '[]') or ['.location','[class*="location"]']):
            e = card.select_one(sel)
            if e and e.text.strip(): location = e.text.strip(); break
        link = ''
        a = card.select_one(config.get('link_selector','a') or 'a') or card.select_one('a[href]')
        if a:
            href = a.get('href','')
            if href: link = urljoin(url, href)
        if title and len(title) > 3:
            jobs.append(standardize_job({'title':title,'company':company or 'Company','location':location or 'India','apply_website':link or url,'source_url':link or url}))
    return jobs[:5]

def scrape_single_site(config, keyword, location):
    try:
        url = config['base_url']
        if not config.get('is_static_url'): url = url.replace('{keyword}', quote(keyword)).replace('{location}', quote(location))
        r = safe_request(url)
        if r: return extract_jobs(BeautifulSoup(r.text, 'html.parser'), url, config)
    except: pass
    return []


# ============================================================
# ⭐ SIMPLE SAVE (No lock needed - separate DB)
# ============================================================

def save_jobs_batch(jobs_batch):
    """Save jobs - separate DB so no locking issues"""
    if not jobs_batch: return 0
    added = 0
    try:
        for j in jobs_batch:
            if not Job.query.filter_by(title=j['title'], company=j['company'], source='scraped').first():
                try: db.session.add(Job(**j)); added += 1
                except: pass
        if added > 0: db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Save error: {str(e)[:100]}")
    return added


# ============================================================
# RANDOM SELECTORS
# ============================================================

def get_random_website(websites):
    if not websites: return None
    now = datetime.utcnow()
    fresh = [s for s in websites if not scraped_websites_tracker.get(s.id) or (now - scraped_websites_tracker[s.id]).total_seconds() > 1800]
    return random.choice(fresh or websites)

def get_random_keyword(keywords):
    if not keywords: return 'software developer'
    now = datetime.utcnow()
    fresh = [k for k in keywords if not scraped_keywords_tracker.get(k.id) or (now - scraped_keywords_tracker[k.id]).total_seconds() > 600]
    selected = random.choice(fresh or keywords)
    scraped_keywords_tracker[selected.id] = now
    return selected.keyword

def get_random_location(locations):
    return random.choice(locations).location if locations else 'India'


# ============================================================
# CLEANUP
# ============================================================

def delete_old_jobs():
    try:
        d = Job.query.filter(Job.source=='scraped', Job.posted_date < datetime.utcnow()-timedelta(days=30)).delete()
        if d: db.session.commit(); print(f"🗑️ Deleted {d} old jobs")
        return d or 0
    except: db.session.rollback(); return 0


# ============================================================
# ⭐ MAIN SCRAPE FUNCTION
# ============================================================

def run_scrape(full=False):
    global scrape_stats, scraper_control
    
    if not scraper_control['enabled']:
        print("⏸️ Scraper disabled"); return 0
    
    scraper_control['stop_requested'] = False
    scraper_control['paused'] = False
    
    delete_old_jobs()
    
    websites = ScrapeWebsite.query.filter_by(is_active=True).order_by(ScrapeWebsite.priority).all()
    keywords = ScrapeKeyword.query.filter_by(is_active=True).order_by(ScrapeKeyword.priority).all()
    locations = ScrapeLocation.query.filter_by(is_active=True).order_by(ScrapeLocation.priority).all()
    
    if not websites: return 0
    
    sites_to_scrape = len(websites) if full else min(5, len(websites))
    scrape_stats = ScrapeStats(); scrape_stats.running = True
    
    print(f"\n🕷️ SCRAPING: {sites_to_scrape}/{len(websites)} sites")
    total_added = 0; all_jobs = []
    
    for i in range(sites_to_scrape):
        if scraper_control['stop_requested']: print("🛑 Stopped!"); break
        
        while scraper_control['paused']:
            scrape_stats.paused = True; scrape_stats.pause_reason = "Paused by admin"
            time.sleep(5)
        scrape_stats.paused = False
        
        website = get_random_website(websites)
        if not website: continue
        
        scrape_stats.current = website.name; scrape_stats.done = i+1; scrape_stats.total = sites_to_scrape
        
        config = {'base_url': website.base_url, 'card_selectors': website.card_selectors, 'title_selectors': website.title_selectors, 'company_selectors': website.company_selectors, 'location_selectors': website.location_selectors, 'link_selector': website.link_selector, 'is_static_url': website.is_static_url}
        site_jobs = []
        
        for _ in range(2 if full else 1):
            if scraper_control['stop_requested']: break
            kw = get_random_keyword(keywords); loc = get_random_location(locations)
            jobs = scrape_single_site(config, kw, loc)
            if jobs: site_jobs.extend(jobs); all_jobs.extend(jobs)
            if len(all_jobs) >= 20:
                added = save_jobs_batch(all_jobs); total_added += added; scrape_stats.added += added; scrape_stats.found += len(all_jobs)
                print(f"  💾 +{added} jobs"); all_jobs = []
        
        scraped_websites_tracker[website.id] = datetime.utcnow()
        
        if site_jobs:
            scrape_stats.success += 1
            try: website.last_scraped = datetime.utcnow(); website.jobs_found = len(site_jobs); db.session.commit()
            except: db.session.rollback()
            print(f"  ✅ {website.name}: {len(site_jobs)} jobs")
        else: print(f"  ⚠️ {website.name}: No jobs")
        
        if i < sites_to_scrape-1 and not scraper_control['stop_requested']:
            for _ in range(600):  # 10 min with stop check
                if scraper_control['stop_requested'] or scraper_control['paused']: break
                time.sleep(1)
    
    if all_jobs:
        added = save_jobs_batch(all_jobs); total_added += added; scrape_stats.added += added
    scrape_stats.running = False
    print(f"📊 Done: {total_added} jobs")
    return total_added


def scrape_lightweight():
    return run_scrape(full=False)


# ============================================================
# SCHEDULER
# ============================================================

def start_job_scraper(app):
    def run():
        time.sleep(30)
        with app.app_context():
            if scraper_control['enabled']: scrape_lightweight()
        while True:
            time.sleep(72000)
            with app.app_context():
                if scraper_control['enabled'] and not scraper_control['paused']: scrape_lightweight()
    threading.Thread(target=run, daemon=True).start()
    print("🔄 Smart Scraper started (20h, random sites, separate DB)")


# ============================================================
# SCRAPE ROUTES
# ============================================================

@scraper_bp.route('/scrape-jobs-now')
def scrape_now():
    try: c = run_scrape(full=True); flash(f'✅ {c} jobs scraped!', 'success')
    except Exception as e: flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/scrape-light')
def scrape_light():
    try: c = scrape_lightweight(); flash(f'✅ {c} jobs!', 'success')
    except Exception as e: flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))


# ============================================================
# ⭐ CONTROL ROUTES
# ============================================================

@scraper_bp.route('/api/scraper/pause')
def pause_scraper():
    scraper_control['paused'] = True; scrape_stats.paused = True; scrape_stats.pause_reason = "Paused by admin"
    return jsonify({'success': True, 'message': 'Paused!', 'status': 'paused'})

@scraper_bp.route('/api/scraper/resume')
def resume_scraper():
    scraper_control['paused'] = False; scrape_stats.paused = False; scrape_stats.pause_reason = ""
    return jsonify({'success': True, 'message': 'Resumed!', 'status': 'running'})

@scraper_bp.route('/api/scraper/stop')
def stop_scraper():
    scraper_control['stop_requested'] = True; scraper_control['paused'] = False; scrape_stats.running = False
    return jsonify({'success': True, 'message': 'Stopped!', 'status': 'stopped'})

@scraper_bp.route('/api/scraper/disable')
def disable_scraper():
    scraper_control['enabled'] = False; scraper_control['stop_requested'] = True; scraper_control['paused'] = False
    return jsonify({'success': True, 'message': 'Disabled!', 'status': 'disabled'})

@scraper_bp.route('/api/scraper/enable')
def enable_scraper():
    scraper_control['enabled'] = True; scraper_control['stop_requested'] = False; scraper_control['paused'] = False
    return jsonify({'success': True, 'message': 'Enabled!', 'status': 'enabled'})

@scraper_bp.route('/api/scraper/control-status')
def control_status():
    return jsonify({
        'enabled': scraper_control['enabled'], 'paused': scraper_control['paused'],
        'running': scrape_stats.running, 'current_site': scrape_stats.current,
        'progress': f"{scrape_stats.done}/{scrape_stats.total}", 'jobs_added': scrape_stats.added,
        'total_jobs': Job.query.filter_by(source='scraped', is_active=True).count(),
    })

@scraper_bp.route('/api/scrape-status')
def status():
    return jsonify({
        'total_jobs': Job.query.filter_by(source='scraped', is_active=True).count(),
        'running': scrape_stats.running, 'current': scrape_stats.current,
        'paused': scrape_stats.paused, 'enabled': scraper_control['enabled'],
    })