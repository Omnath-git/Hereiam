# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    
    # ⭐ SQLite के लिए URI में भी timeout जोड़ें
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db?timeout=30'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': 30,
            'check_same_thread': False,
        },
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    UPLOAD_FOLDER = 'static/uploads/profile_photos'
    CV_UPLOAD_FOLDER = 'static/uploads/cvs'
    PROFILES_FOLDER = 'profiles'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')