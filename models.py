# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================
# MAIN DATABASE - Users, Admin, Donations, Scraper Config
# ============================================================

class User(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), default='')
    domain = db.Column(db.String(100), default='')
    city = db.Column(db.String(100), default='')
    state = db.Column(db.String(100), default='')
    profile_photo = db.Column(db.String(200), default='')
    summary = db.Column(db.Text, default='')
    experience_years = db.Column(db.String(10), default='')
    skills = db.Column(db.Text, default='')
    education = db.Column(db.Text, default='')
    experience = db.Column(db.Text, default='')
    projects = db.Column(db.Text, default='')
    certifications = db.Column(db.Text, default='')
    languages = db.Column(db.Text, default='')
    achievements = db.Column(db.Text, default='')
    linkedin = db.Column(db.String(200), default='')
    github = db.Column(db.String(200), default='')
    portfolio = db.Column(db.String(200), default='')
    expected_salary = db.Column(db.String(50), default='')
    notice_period = db.Column(db.String(50), default='')
    user_type = db.Column(db.String(20), default='jobseeker')
    company_name = db.Column(db.String(200), default='')
    company_website = db.Column(db.String(200), default='')
    show_email = db.Column(db.Boolean, default=False)
    show_mobile = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    profile_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_url = db.Column(db.String(200), default='')


class Admin(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Donation(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database
    __tablename__ = 'donation'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    donor_name = db.Column(db.String(100))
    donor_email = db.Column(db.String(120))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScrapeWebsite(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database (scraper config)
    __tablename__ = 'scrape_website'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    card_selectors = db.Column(db.Text, default='[]')
    title_selectors = db.Column(db.Text, default='[]')
    company_selectors = db.Column(db.Text, default='[]')
    location_selectors = db.Column(db.Text, default='[]')
    link_selector = db.Column(db.String(200), default='a')
    is_static_url = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    last_scraped = db.Column(db.DateTime, nullable=True)
    jobs_found = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScrapeKeyword(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database
    __tablename__ = 'scrape_keyword'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(100), default='general')
    keyword = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScrapeLocation(db.Model):
    __bind_key__ = 'main'  # ⭐ Main database
    __tablename__ = 'scrape_location'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# JOBS DATABASE - Separate to avoid locking with user operations
# ============================================================

class Job(db.Model):
    __bind_key__ = 'jobs'  # ⭐⭐ SEPARATE JOBS DATABASE ⭐⭐
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), default='')
    salary_range = db.Column(db.String(100), default='')
    experience_required = db.Column(db.String(50), default='')
    job_type = db.Column(db.String(50), default='Full-time')
    description = db.Column(db.Text, default='')
    requirements = db.Column(db.Text, default='')
    skills_required = db.Column(db.Text, default='')
    apply_method = db.Column(db.String(50), default='website')
    apply_email = db.Column(db.String(200), default='')
    apply_website = db.Column(db.String(500), default='')
    source = db.Column(db.String(50), default='user')
    source_url = db.Column(db.String(500), default='')
    is_active = db.Column(db.Boolean, default=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
class ScrapeDesignation(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'scrape_designation'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    designation = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# models.py में जोड़ें

class District(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'district'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    district_name = db.Column(db.String(200), nullable=False)
    state_name = db.Column(db.String(200), nullable=False)