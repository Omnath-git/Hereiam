# blueprints/search.py
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify
from urllib.parse import quote
import concurrent.futures
import time

search_bp = Blueprint('search', __name__)

# Search configurations for different websites
SEARCH_ENGINES = {
    'google_jobs': {
        'name': 'Google Jobs',
        'url': 'https://www.google.com/search?q={keyword}+jobs+{location}&ibp=htl;jobs',
        'parser': 'google'
    },
    'indeed': {
        'name': 'Indeed',
        'url': 'https://in.indeed.com/jobs?q={keyword}&l={location}&fromage=7',
        'parser': 'indeed'
    },
    'naukri': {
        'name': 'Naukri.com',
        'url': 'https://www.naukri.com/{keyword}-jobs-in-{location}?k={keyword}',
        'parser': 'naukri'
    },
    'linkedin': {
        'name': 'LinkedIn',
        'url': 'https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}',
        'parser': 'linkedin'
    },
    'foundit': {
        'name': 'Foundit',
        'url': 'https://www.foundit.in/jobs?q={keyword}&location={location}',
        'parser': 'generic'
    },
    'shine': {
        'name': 'Shine.com',
        'url': 'https://www.shine.com/jobs/search?q={keyword}&location={location}',
        'parser': 'generic'
    },
    'freshersworld': {
        'name': 'Freshersworld',
        'url': 'https://www.freshersworld.com/jobs?q={keyword}&location={location}',
        'parser': 'generic'
    },
    'timesjobs': {
        'name': 'TimesJobs',
        'url': 'https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&searchTextSrc=&searchTextText=&txtKeywords={keyword}&txtLocation={location}',
        'parser': 'generic'
    },
    'apna': {
        'name': 'Apna.co',
        'url': 'https://apna.co/jobs?q={keyword}&location={location}',
        'parser': 'generic'
    },
    'workindia': {
        'name': 'WorkIndia',
        'url': 'https://www.workindia.in/jobs?q={keyword}&location={location}',
        'parser': 'generic'
    },
    'internshala': {
        'name': 'Internshala',
        'url': 'https://internshala.com/jobs/search?keywords={keyword}&location={location}',
        'parser': 'generic'
    },
    'hirect': {
        'name': 'Hirect',
        'url': 'https://www.hirect.in/jobs?q={keyword}&location={location}',
        'parser': 'generic'
    },
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
]

def get_headers():
    import random
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    }

def search_single_site(site_key, config, keyword, location):
    """Search jobs on a single website"""
    try:
        url = config['url'].format(keyword=quote(keyword), location=quote(location))
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Generic job extraction
            selectors = [
                '.job-card', '[class*="job"]', '.result-card', '.listing-card',
                'article', '.job-listing', '.vacancy', '.job-item', 'li'
            ]
            
            cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if len(cards) > 3:
                    break
            
            for card in cards[:5]:  # Max 5 per site
                title = company = location_text = link = ''
                
                # Title
                for tag in ['h2', 'h3', 'h4', '.title', 'a strong', '.job-title']:
                    elem = card.select_one(tag)
                    if elem and len(elem.text.strip()) > 5:
                        title = elem.text.strip()[:100]
                        break
                
                # Company
                for cls in ['.company', '.employer', '.org', '.company-name']:
                    elem = card.select_one(cls)
                    if elem:
                        company = elem.text.strip()[:80]
                        break
                
                # Link
                link_elem = card.select_one('a[href]')
                if link_elem:
                    href = link_elem.get('href', '')
                    if href.startswith('http'):
                        link = href
                    elif href.startswith('/'):
                        from urllib.parse import urljoin
                        link = urljoin(url, href)
                
                if title:
                    jobs.append({
                        'title': title,
                        'company': company or 'Company',
                        'location': location,
                        'source': config['name'],
                        'link': link or url
                    })
            
            return jobs
        return []
    except Exception as e:
        return []


@search_bp.route('/search')
def search_page():
    """Search page"""
    return render_template('search.html')


@search_bp.route('/api/search-jobs')
def api_search_jobs():
    """API endpoint for live job search"""
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', 'India').strip()
    
    if not keyword or len(keyword) < 2:
        return jsonify({'success': False, 'message': 'Please enter at least 2 characters', 'jobs': []})
    
    all_jobs = []
    
    # Search multiple sites in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_site = {
            executor.submit(search_single_site, site_key, config, keyword, location): site_key
            for site_key, config in SEARCH_ENGINES.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_site):
            site_key = future_to_site[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error searching {site_key}: {e}")
    
    # Also search in our database
    from models import Job as JobModel
    db_jobs = JobModel.query.filter(
        JobModel.is_active == True,
        (JobModel.title.ilike(f'%{keyword}%')) |
        (JobModel.skills_required.ilike(f'%{keyword}%')) |
        (JobModel.description.ilike(f'%{keyword}%'))
    ).limit(20).all()
    
    for job in db_jobs:
        all_jobs.append({
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'source': 'Our Database',
            'link': job.apply_website or '#',
            'salary': job.salary_range or 'Not Disclosed',
            'type': job.job_type or 'Full-time'
        })
    
    return jsonify({
        'success': True,
        'count': len(all_jobs),
        'keyword': keyword,
        'location': location,
        'jobs': all_jobs[:50]  # Max 50 results
    })


@search_bp.route('/api/trending-keywords')
def trending_keywords():
    """Get trending search keywords"""
    keywords = [
        {'keyword': 'Python Developer', 'count': 1250},
        {'keyword': 'React Developer', 'count': 980},
        {'keyword': 'Data Scientist', 'count': 850},
        {'keyword': 'DevOps Engineer', 'count': 720},
        {'keyword': 'Java Developer', 'count': 680},
        {'keyword': 'Full Stack Developer', 'count': 650},
        {'keyword': 'AI/ML Engineer', 'count': 550},
        {'keyword': 'Cloud Architect', 'count': 480},
        {'keyword': 'Flutter Developer', 'count': 420},
        {'keyword': 'Business Analyst', 'count': 390},
    ]
    return jsonify({'keywords': keywords})