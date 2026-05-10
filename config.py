# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    
    # ⭐ Main database (Users, Donations, Admin, Scraper Config)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///main.db?timeout=30'
    
    # ⭐ Separate binds for different databases
    SQLALCHEMY_BINDS = {
        'main': 'sqlite:///main.db?timeout=30',      # Users, Admin, Donations, Scraper Config
        'jobs': 'sqlite:///jobs.db?timeout=30',       # Jobs only
        'profiles': 'sqlite:///profiles.db?timeout=30' # Profile pages tracking
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 30, 'check_same_thread': False},
        'pool_size': 10, 'pool_recycle': 3600, 'pool_pre_ping': True,
    }
    
    UPLOAD_FOLDER = 'static/uploads/profile_photos'
    CV_UPLOAD_FOLDER = 'static/uploads/cvs'
    PROFILES_FOLDER = 'profiles'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')