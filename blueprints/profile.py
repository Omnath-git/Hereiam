# blueprints/profile.py
import os, json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from models import db, User
from utils.cv_parser import extract_text_from_pdf, parse_cv
from utils.profile_generator import generate_profile_html

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/upload-cv', methods=['GET', 'POST'])
def upload_cv():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    
    if user.user_type == 'employer':
        flash('Employers cannot upload CV.', 'warning')
        return redirect(url_for('jobs.post_job'))
    
    if request.method == 'POST':
        if 'cv_file' not in request.files:
            flash('No file uploaded!', 'error')
            return redirect(request.url)
        
        cv_file = request.files['cv_file']
        profile_photo = request.files.get('profile_photo')
        
        if cv_file.filename == '' or not cv_file.filename.endswith('.pdf'):
            flash('Please upload a PDF file!', 'error')
            return redirect(request.url)
        
        from flask import current_app
        cv_filename = secure_filename(f"{user.id}_{cv_file.filename}")
        cv_path = os.path.join(current_app.config['CV_UPLOAD_FOLDER'], cv_filename)
        cv_file.save(cv_path)
        
        if profile_photo and profile_photo.filename:
            photo_filename = secure_filename(f"{user.id}_{profile_photo.filename}")
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
            profile_photo.save(photo_path)
            user.profile_photo = f"uploads/profile_photos/{photo_filename}"
        
        cv_text = extract_text_from_pdf(cv_path)
        if not cv_text or len(cv_text.strip()) < 50:
            flash('Could not extract text from PDF.', 'error')
            return redirect(request.url)
        
        parsed_data = parse_cv(cv_text)
        if parsed_data:
            user.summary = parsed_data.get('summary', '')
            user.experience_years = parsed_data.get('experience_years', '')
            user.skills = json.dumps(parsed_data.get('skills', []))
            user.education = json.dumps(parsed_data.get('education', []))
            user.experience = json.dumps(parsed_data.get('experience', []))
            user.projects = json.dumps(parsed_data.get('projects', []))
            user.certifications = json.dumps(parsed_data.get('certifications', []))
            user.languages = json.dumps(parsed_data.get('languages', []))
            user.achievements = json.dumps(parsed_data.get('achievements', []))
            user.linkedin = parsed_data.get('linkedin', '')
            user.github = parsed_data.get('github', '')
            user.portfolio = parsed_data.get('portfolio', '')
            user.profile_complete = True
            
            filename = generate_profile_html(user, current_app)
            user.profile_url = filename
            db.session.commit()
            
            flash('CV processed successfully!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Error processing CV.', 'error')
    
    return render_template('upload_cv.html', user=user)

@profile_bp.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        from flask import current_app
        user.full_name = request.form.get('full_name', user.full_name)
        user.domain = request.form.get('domain', user.domain)
        user.city = request.form.get('city', user.city)
        user.state = request.form.get('state', user.state)
        user.summary = request.form.get('summary', user.summary)
        user.experience_years = request.form.get('experience_years', user.experience_years)
        user.linkedin = request.form.get('linkedin', user.linkedin)
        user.github = request.form.get('github', user.github)
        user.portfolio = request.form.get('portfolio', user.portfolio)
        
        skills = request.form.get('skills', '')
        user.skills = json.dumps([s.strip() for s in skills.split(',') if s.strip()])
        languages = request.form.get('languages', '')
        user.languages = json.dumps([l.strip() for l in languages.split(',') if l.strip()])
        achievements = request.form.get('achievements', '')
        user.achievements = json.dumps([a.strip() for a in achievements.split('\n') if a.strip()])
        
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo.filename:
                photo_filename = secure_filename(f"{user.id}_{photo.filename}")
                photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
                photo.save(photo_path)
                user.profile_photo = f"uploads/profile_photos/{photo_filename}"
        
        db.session.commit()
        generate_profile_html(user, current_app)
        flash('Profile updated!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    skills = json.loads(user.skills) if user.skills else []
    languages = json.loads(user.languages) if user.languages else []
    achievements = json.loads(user.achievements) if user.achievements else []
    
    return render_template('edit_profile.html', user=user,
                         skills=','.join(skills) if skills else '',
                         languages=','.join(languages) if languages else '',
                         achievements='\n'.join(achievements) if achievements else '')

@profile_bp.route('/update-section', methods=['POST'])
def update_section():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user = db.session.get(User, session['user_id'])
    section = request.form.get('section')
    
    try:
        if section == 'skills':
            skills_text = request.form.get('skills', '')
            user.skills = json.dumps([s.strip() for s in skills_text.split(',') if s.strip()])
        elif section == 'experience':
            experience_list = []
            index = 0
            while True:
                title = request.form.get(f'exp_title_{index}')
                if not title: break
                experience_list.append({
                    'title': title,
                    'company': request.form.get(f'exp_company_{index}', ''),
                    'duration': request.form.get(f'exp_duration_{index}', ''),
                    'description': request.form.get(f'exp_description_{index}', '')
                })
                index += 1
            user.experience = json.dumps(experience_list)
        elif section == 'education':
            education_list = []
            index = 0
            while True:
                degree = request.form.get(f'edu_degree_{index}')
                if not degree: break
                education_list.append({
                    'degree': degree,
                    'institution': request.form.get(f'edu_institution_{index}', ''),
                    'year': request.form.get(f'edu_year_{index}', '')
                })
                index += 1
            user.education = json.dumps(education_list)
        elif section == 'projects':
            projects_list = []
            index = 0
            while True:
                name = request.form.get(f'proj_name_{index}')
                if not name: break
                projects_list.append({
                    'name': name,
                    'description': request.form.get(f'proj_description_{index}', ''),
                    'technologies': request.form.get(f'proj_technologies_{index}', '')
                })
                index += 1
            user.projects = json.dumps(projects_list)
        elif section == 'certifications':
            certs_text = request.form.get('certifications', '')
            user.certifications = json.dumps([c.strip() for c in certs_text.split('\n') if c.strip()])
        elif section == 'languages':
            langs_text = request.form.get('languages', '')
            user.languages = json.dumps([l.strip() for l in langs_text.split(',') if l.strip()])
        elif section == 'achievements':
            ach_text = request.form.get('achievements', '')
            user.achievements = json.dumps([a.strip() for a in ach_text.split('\n') if a.strip()])
        elif section == 'job_preferences':
            user.expected_salary = request.form.get('expected_salary', '')
            user.notice_period = request.form.get('notice_period', '')
        else:
            return jsonify({'success': False, 'message': 'Invalid section'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{section} updated!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@profile_bp.route('/regenerate-profile', methods=['POST'])
def regenerate_profile():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401    
    from flask import current_app
    user = db.session.get(User, session['user_id'])
    filename = generate_profile_html(user, current_app)
    if filename:
        user.profile_url = filename
        user.profile_complete = True
        db.session.commit()
        return jsonify({'success': True, 'profile_url': url_for('main.view_profile', filename=filename)})
    return jsonify({'success': False}), 500

@profile_bp.route('/reupload-cv', methods=['POST'])
def reupload_cv():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    from flask import current_app
    user = db.session.get(User, session['user_id'])
    
    if 'cv_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file'}), 400
    
    cv_file = request.files['cv_file']
    if not cv_file.filename.endswith('.pdf'):
        return jsonify({'success': False, 'message': 'PDF only'}), 400
    
    cv_filename = secure_filename(f"{user.id}_{cv_file.filename}")
    cv_path = os.path.join(current_app.config['CV_UPLOAD_FOLDER'], cv_filename)
    cv_file.save(cv_path)
    
    cv_text = extract_text_from_pdf(cv_path)
    if not cv_text:
        return jsonify({'success': False}), 400
    
    parsed_data = parse_cv(cv_text)
    if parsed_data:
        user.summary = parsed_data.get('summary', '')
        user.experience_years = parsed_data.get('experience_years', '')
        user.skills = json.dumps(parsed_data.get('skills', []))
        user.education = json.dumps(parsed_data.get('education', []))
        user.experience = json.dumps(parsed_data.get('experience', []))
        user.projects = json.dumps(parsed_data.get('projects', []))
        user.certifications = json.dumps(parsed_data.get('certifications', []))
        user.languages = json.dumps(parsed_data.get('languages', []))
        user.achievements = json.dumps(parsed_data.get('achievements', []))
        
        filename = generate_profile_html(user, current_app)
        user.profile_url = filename
        user.profile_complete = True
        db.session.commit()
        return jsonify({'success': True, 'profile_url': url_for('main.view_profile', filename=filename)})
    
    return jsonify({'success': False}), 500