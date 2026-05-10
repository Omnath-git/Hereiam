from flask import Flask, send_from_directory
from config import Config
from models import db
import os

# app.py

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # ⭐ Create directories
    for folder in [app.config['UPLOAD_FOLDER'], app.config['CV_UPLOAD_FOLDER'], app.config['PROFILES_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
    
    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.profile import profile_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.jobs import jobs_bp
    from blueprints.main import main_bp
    from blueprints.scraper import scraper_bp, start_job_scraper
    from blueprints.admin import admin_bp
    from blueprints.admin_scraper import admin_scraper_bp
    from blueprints.donate import donate_bp
    from blueprints.locations import locations_bp
    
    app.register_blueprint(locations_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(scraper_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_scraper_bp)
    app.register_blueprint(donate_bp)
    
    # ⭐ Create all databases
    with app.app_context():
        db.create_all()  # Creates main.db and jobs.db
        print("✅ Databases created: main.db, jobs.db")
    
    # Start scraper
    #start_job_scraper(app)
    
    return app
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)