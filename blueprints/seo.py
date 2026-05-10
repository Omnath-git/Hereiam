# blueprints/seo.py
from flask import Blueprint, make_response
from datetime import datetime

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/robots.txt')
def robots_txt():
    robots_content = """User-agent: *
Allow: /
Allow: /login
Allow: /register
Allow: /donate
Allow: /profile/
Allow: /search
Allow: /static/uploads/profile_photos/
Disallow: /admin-login
Disallow: /admin-dashboard
Disallow: /admin/
Disallow: /dashboard
Disallow: /verify-otp
Disallow: /get-demo-otp
Disallow: /api/
Disallow: /update-section
Disallow: /regenerate-profile
Disallow: /reupload-cv
Disallow: /static/uploads/cvs/
Disallow: /*.pdf$
Crawl-delay: 2
Sitemap: https://hereiam.in/sitemap.xml

User-agent: Googlebot
Allow: /
Disallow: /admin-login
Disallow: /admin-dashboard
Disallow: /admin/
Disallow: /api/
Disallow: /static/uploads/cvs/
Crawl-delay: 1

User-agent: GPTBot
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Claude-Web
Disallow: /"""
    
    return robots_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@seo_bp.route('/sitemap.xml')
def sitemap_xml():
    base_url = 'https://hereiam.in'
    today = datetime.utcnow().strftime('%Y-%m-%d')
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    pages = [
        ('/', '1.0', 'daily'),
        ('/login', '0.8', 'weekly'),
        ('/register', '0.9', 'weekly'),
        ('/donate', '0.5', 'monthly'),
        ('/search', '0.7', 'daily'),
        ('/?tab=jobs', '0.9', 'daily'),
        ('/?tab=professionals', '0.9', 'daily'),
    ]
    
    for url, priority, freq in pages:
        xml.append(f'<url><loc>{base_url}{url}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>')
    
    xml.append('</urlset>')
    
    response = make_response('\n'.join(xml))
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response