# blueprints/admin_scraper.py
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, ScrapeWebsite, ScrapeKeyword, ScrapeLocation, ScrapeDesignation

admin_scraper_bp = Blueprint('admin_scraper', __name__)


def admin_required():
    if not session.get('admin_logged_in'):
        flash('Please login as admin first!', 'error')
        return False
    return True


# ============================================================
# WEBSITES MANAGEMENT
# ============================================================

@admin_scraper_bp.route('/admin/websites')
def manage_websites():
    if not admin_required():
        return redirect(url_for('admin.admin_login'))
    
    websites = ScrapeWebsite.query.order_by(ScrapeWebsite.priority).all()
    return render_template('admin_websites.html', websites=websites)


@admin_scraper_bp.route('/admin/website/add', methods=['POST'])
def add_website():
    if not admin_required():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        website = ScrapeWebsite(
            name=request.form.get('name', ''),
            base_url=request.form.get('base_url', ''),
            card_selectors=json.dumps([s.strip() for s in request.form.get('card_selectors', '').split(',') if s.strip()]),
            title_selectors=json.dumps([s.strip() for s in request.form.get('title_selectors', '').split(',') if s.strip()]),
            company_selectors=json.dumps([s.strip() for s in request.form.get('company_selectors', '').split(',') if s.strip()]),
            location_selectors=json.dumps([s.strip() for s in request.form.get('location_selectors', '').split(',') if s.strip()]),
            link_selector=request.form.get('link_selector', 'a'),
            is_static_url=request.form.get('is_static_url') == 'on',
            priority=int(request.form.get('priority', 1))
        )
        db.session.add(website)
        db.session.commit()
        flash('Website added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_scraper.manage_websites'))


@admin_scraper_bp.route('/admin/website/edit/<int:id>', methods=['POST'])
def edit_website(id):
    if not admin_required():
        return jsonify({'success': False})
    
    website = db.session.get(ScrapeWebsite, id)
    if not website:
        return jsonify({'success': False, 'message': 'Not found'})
    
    try:
        website.name = request.form.get('name', website.name)
        website.base_url = request.form.get('base_url', website.base_url)
        website.card_selectors = json.dumps([s.strip() for s in request.form.get('card_selectors', '').split(',') if s.strip()])
        website.title_selectors = json.dumps([s.strip() for s in request.form.get('title_selectors', '').split(',') if s.strip()])
        website.company_selectors = json.dumps([s.strip() for s in request.form.get('company_selectors', '').split(',') if s.strip()])
        website.location_selectors = json.dumps([s.strip() for s in request.form.get('location_selectors', '').split(',') if s.strip()])
        website.link_selector = request.form.get('link_selector', website.link_selector)
        website.is_static_url = request.form.get('is_static_url') == 'on'
        website.priority = int(request.form.get('priority', website.priority))
        website.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Website updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_scraper.manage_websites'))


@admin_scraper_bp.route('/admin/website/delete/<int:id>', methods=['POST'])
def delete_website(id):
    if not admin_required():
        return jsonify({'success': False})
    
    website = db.session.get(ScrapeWebsite, id)
    if website:
        db.session.delete(website)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})


@admin_scraper_bp.route('/admin/website/toggle/<int:id>')
def toggle_website(id):
    if not admin_required():
        return jsonify({'success': False})
    
    website = db.session.get(ScrapeWebsite, id)
    if website:
        website.is_active = not website.is_active
        db.session.commit()
        return jsonify({'success': True, 'is_active': website.is_active})
    return jsonify({'success': False})


# ============================================================
# KEYWORDS MANAGEMENT
# ============================================================

@admin_scraper_bp.route('/admin/keywords')
def manage_keywords():
    if not admin_required():
        return redirect(url_for('admin.admin_login'))
    
    keywords = ScrapeKeyword.query.order_by(ScrapeKeyword.category, ScrapeKeyword.priority).all()
    categories = db.session.query(ScrapeKeyword.category).distinct().all()
    return render_template('admin_keywords.html', keywords=keywords, categories=categories)


@admin_scraper_bp.route('/admin/keyword/add', methods=['POST'])
def add_keyword():
    if not admin_required():
        return jsonify({'success': False})
    
    try:
        keyword = ScrapeKeyword(
            category=request.form.get('category', 'general'),
            keyword=request.form.get('keyword', ''),
            priority=int(request.form.get('priority', 1))
        )
        db.session.add(keyword)
        db.session.commit()
        flash('Keyword added!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_scraper.manage_keywords'))


@admin_scraper_bp.route('/admin/keyword/edit/<int:id>', methods=['POST'])
def edit_keyword(id):
    if not admin_required():
        return jsonify({'success': False})
    
    kw = db.session.get(ScrapeKeyword, id)
    if kw:
        kw.category = request.form.get('category', kw.category)
        kw.keyword = request.form.get('keyword', kw.keyword)
        kw.priority = int(request.form.get('priority', kw.priority))
        kw.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Keyword updated!', 'success')
    
    return redirect(url_for('admin_scraper.manage_keywords'))


@admin_scraper_bp.route('/admin/keyword/delete/<int:id>', methods=['POST'])
def delete_keyword(id):
    if not admin_required():
        return jsonify({'success': False})
    
    kw = db.session.get(ScrapeKeyword, id)
    if kw:
        db.session.delete(kw)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})


@admin_scraper_bp.route('/admin/keyword/bulk-add', methods=['POST'])
def bulk_add_keywords():
    if not admin_required():
        return jsonify({'success': False})
    
    category = request.form.get('category', 'general')
    keywords_text = request.form.get('keywords', '')
    keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]
    
    added = 0
    for kw in keywords:
        existing = ScrapeKeyword.query.filter_by(keyword=kw).first()
        if not existing:
            db.session.add(ScrapeKeyword(category=category, keyword=kw))
            added += 1
    
    db.session.commit()
    flash(f'{added} keywords added!', 'success')
    return redirect(url_for('admin_scraper.manage_keywords'))


# ============================================================
# LOCATIONS MANAGEMENT
# ============================================================

@admin_scraper_bp.route('/admin/locations')
def manage_locations():
    if not admin_required():
        return redirect(url_for('admin.admin_login'))
    
    locations = ScrapeLocation.query.order_by(ScrapeLocation.priority).all()
    return render_template('admin_locations.html', locations=locations)


@admin_scraper_bp.route('/admin/location/add', methods=['POST'])
def add_location():
    if not admin_required():
        return jsonify({'success': False})
    
    try:
        loc = ScrapeLocation(
            location=request.form.get('location', ''),
            priority=int(request.form.get('priority', 1))
        )
        db.session.add(loc)
        db.session.commit()
        flash('Location added!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_scraper.manage_locations'))


@admin_scraper_bp.route('/admin/location/edit/<int:id>', methods=['POST'])
def edit_location(id):
    if not admin_required():
        return jsonify({'success': False})
    
    loc = db.session.get(ScrapeLocation, id)
    if loc:
        loc.location = request.form.get('location', loc.location)
        loc.priority = int(request.form.get('priority', loc.priority))
        loc.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Location updated!', 'success')
    
    return redirect(url_for('admin_scraper.manage_locations'))


@admin_scraper_bp.route('/admin/location/delete/<int:id>', methods=['POST'])
def delete_location(id):
    if not admin_required():
        return jsonify({'success': False})
    
    loc = db.session.get(ScrapeLocation, id)
    if loc:
        db.session.delete(loc)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})


@admin_scraper_bp.route('/admin/location/bulk-add', methods=['POST'])
def bulk_add_locations():
    if not admin_required():
        return jsonify({'success': False})
    
    locations_text = request.form.get('locations', '')
    locations = [l.strip() for l in locations_text.split('\n') if l.strip()]
    
    added = 0
    for loc in locations:
        existing = ScrapeLocation.query.filter_by(location=loc).first()
        if not existing:
            db.session.add(ScrapeLocation(location=loc))
            added += 1
    
    db.session.commit()
    flash(f'{added} locations added!', 'success')
    return redirect(url_for('admin_scraper.manage_locations'))


# ============================================================
# DESIGNATIONS MANAGEMENT
# ============================================================

@admin_scraper_bp.route('/admin/designations')
def manage_designations():
    if not admin_required():
        return redirect(url_for('admin.admin_login'))
    
    designations = ScrapeDesignation.query.order_by(ScrapeDesignation.category).all()
    categories = db.session.query(ScrapeDesignation.category).distinct().all()
    return render_template('admin_designations.html', designations=designations, categories=categories)


@admin_scraper_bp.route('/admin/designation/add', methods=['POST'])
def add_designation():
    if not admin_required():
        return jsonify({'success': False})
    
    try:
        des = ScrapeDesignation(
            designation=request.form.get('designation', ''),
            category=request.form.get('category', 'general')
        )
        db.session.add(des)
        db.session.commit()
        flash('Designation added!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_scraper.manage_designations'))


@admin_scraper_bp.route('/admin/designation/edit/<int:id>', methods=['POST'])
def edit_designation(id):
    if not admin_required():
        return jsonify({'success': False})
    
    des = db.session.get(ScrapeDesignation, id)
    if des:
        des.designation = request.form.get('designation', des.designation)
        des.category = request.form.get('category', des.category)
        des.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Designation updated!', 'success')
    
    return redirect(url_for('admin_scraper.manage_designations'))


@admin_scraper_bp.route('/admin/designation/delete/<int:id>', methods=['POST'])
def delete_designation(id):
    if not admin_required():
        return jsonify({'success': False})
    
    des = db.session.get(ScrapeDesignation, id)
    if des:
        db.session.delete(des)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})