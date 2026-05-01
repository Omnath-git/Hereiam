# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
from functools import wraps
db = SQLAlchemy()

class User(db.Model):
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
    email_verified = db.Column(db.Boolean, default=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    profile_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_url = db.Column(db.String(200), default='')
    show_email = db.Column(db.Boolean, default=False) 
    show_mobile = db.Column(db.Boolean, default=False) 
# models.py में जोड़ें
class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), default='')
    salary_range = db.Column(db.String(100), default='')
    experience_required = db.Column(db.String(50), default='')
    job_type = db.Column(db.String(50), default='Full-time')
    description = db.Column(db.Text, default='')
    requirements = db.Column(db.Text, default='')
    skills_required = db.Column(db.Text, default='')
    apply_method = db.Column(db.String(50), default='email')
    apply_email = db.Column(db.String(200), default='')
    apply_website = db.Column(db.String(500), default='')
    source = db.Column(db.String(50), default='user')
    source_url = db.Column(db.String(500), default='')
    is_active = db.Column(db.Boolean, default=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
def retry_on_lock(max_retries=5, delay=0.5):
    """Database lock होने पर रिट्राई करें"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if 'database is locked' in str(e) and attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise e
        return wrapper
    return decorator