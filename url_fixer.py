# fix_urls.py - D:\Hereiam.in V4\ में सेव करें और रन करें
import os
import re

# URL मैपिंग - पुराना → नया
URL_REPLACEMENTS = {
    # index
    "url_for('index')": "url_for('main.index')",
    "url_for('index',": "url_for('main.index',",
    
    # login/register/logout
    "url_for('login')": "url_for('auth.login')",
    "url_for('login',": "url_for('auth.login',",
    "url_for('register')": "url_for('auth.register')",
    "url_for('register',": "url_for('auth.register',",
    "url_for('logout')": "url_for('auth.logout')",
    "url_for('logout',": "url_for('auth.logout',",
    
    # verify OTP
    "url_for('verify_otp')": "url_for('auth.verify_otp')",
    "url_for('get_demo_otp')": "url_for('auth.get_demo_otp')",
    
    # dashboard
    "url_for('dashboard')": "url_for('dashboard.dashboard')",
    "url_for('dashboard',": "url_for('dashboard.dashboard',",
    
    # profile
    "url_for('upload_cv')": "url_for('profile.upload_cv')",
    "url_for('upload_cv',": "url_for('profile.upload_cv',",
    "url_for('edit_profile')": "url_for('profile.edit_profile')",
    "url_for('edit_profile',": "url_for('profile.edit_profile',",
    "url_for('update_section')": "url_for('profile.update_section')",
    "url_for('regenerate_profile')": "url_for('profile.regenerate_profile')",
    "url_for('reupload_cv')": "url_for('profile.reupload_cv')",
    
    # jobs
    "url_for('post_job')": "url_for('jobs.post_job')",
    "url_for('post_job',": "url_for('jobs.post_job',",
    "url_for('my_jobs')": "url_for('jobs.my_jobs')",
    "url_for('my_jobs',": "url_for('jobs.my_jobs',",
    "url_for('edit_job')": "url_for('jobs.edit_job')",
    "url_for('edit_job',": "url_for('jobs.edit_job',",
    "url_for('toggle_job')": "url_for('jobs.toggle_job')",
    "url_for('delete_job')": "url_for('jobs.delete_job')",
    
    # view profile
    "url_for('view_profile')": "url_for('main.view_profile')",
    "url_for('view_profile',": "url_for('main.view_profile',",
    
    # scrape
    "url_for('scrape_jobs_now')": "url_for('scraper.scrape_jobs_now')",
    "url_for('scrape_status')": "url_for('scraper.scrape_status')",
    "url_for('debug_scrape')": "url_for('scraper.debug_scrape')",
}

def fix_template_file(filepath):
    """Fix url_for in a single template file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        for old, new in URL_REPLACEMENTS.items():
            if old in content:
                content = content.replace(old, new)
                changes += 1
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {changes} URLs: {os.path.basename(filepath)}")
            return changes
        else:
            print(f"⏭️  No changes: {os.path.basename(filepath)}")
            return 0
    except Exception as e:
        print(f"❌ Error: {os.path.basename(filepath)} - {e}")
        return 0

def fix_python_file(filepath):
    """Fix url_for in Python blueprint files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        for old, new in URL_REPLACEMENTS.items():
            # Python files mein url_for thoda different ho sakta hai
            python_old = old.replace("url_for('", "url_for('")
            if python_old in content:
                content = content.replace(python_old, new)
                changes += 1
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {changes} URLs: {os.path.basename(filepath)}")
            return changes
        else:
            print(f"⏭️  No changes: {os.path.basename(filepath)}")
            return 0
    except Exception as e:
        print(f"❌ Error: {os.path.basename(filepath)} - {e}")
        return 0

def main():
    print("\n" + "="*60)
    print("🔧 FIXING ALL URL_FOR REFERENCES")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, 'templates')
    blueprints_dir = os.path.join(base_dir, 'blueprints')
    
    total_changes = 0
    
    # Fix HTML templates
    print("\n📁 Processing Templates...")
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(templates_dir, filename)
                total_changes += fix_template_file(filepath)
    else:
        print(f"❌ Templates directory not found: {templates_dir}")
    
    # Fix Python blueprints
    print("\n📁 Processing Blueprints...")
    if os.path.exists(blueprints_dir):
        for filename in os.listdir(blueprints_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(blueprints_dir, filename)
                total_changes += fix_python_file(filepath)
    else:
        print(f"❌ Blueprints directory not found: {blueprints_dir}")
    
    # Fix app.py
    app_py = os.path.join(base_dir, 'app.py')
    if os.path.exists(app_py):
        print("\n📁 Processing app.py...")
        total_changes += fix_python_file(app_py)
    
    print("\n" + "="*60)
    print(f"✅ TOTAL FIXES: {total_changes}")
    print("="*60)
    print("\n🚀 Now run: python app.py")

if __name__ == '__main__':
    main()