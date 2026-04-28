# utils/helpers.py
import re
import os
from werkzeug.utils import secure_filename

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:300]

def safe_json_loads(data):
    """Safely load JSON data"""
    import json
    try:
        return json.loads(data) if data else []
    except:
        return []

def create_directories(app):
    """Create necessary directories"""
    dirs = [
        app.config['UPLOAD_FOLDER'],
        app.config['CV_UPLOAD_FOLDER'],
        app.config['PROFILES_FOLDER']
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)