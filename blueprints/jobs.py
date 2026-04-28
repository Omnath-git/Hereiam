# blueprints/jobs.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Job
from datetime import datetime

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    
    if user.user_type != 'employer':
        flash('Only employers can post jobs.', 'warning')
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        job = Job(
            employer_id=user.id,
            title=request.form.get('title'),
            company=request.form.get('company', user.company_name or ''),
            location=request.form.get('location', ''),
            salary_range=request.form.get('salary_range', ''),
            experience_required=request.form.get('experience_required', ''),
            job_type=request.form.get('job_type', 'Full-time'),
            description=request.form.get('description', ''),
            requirements=request.form.get('requirements', ''),
            skills_required=request.form.get('skills_required', ''),
            apply_method=request.form.get('apply_method', 'email'),
            apply_email=request.form.get('apply_email', user.email),
            apply_website=request.form.get('apply_website', ''),
            source='user'
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('post_job.html', user=user)

@jobs_bp.route('/my-jobs')
def my_jobs():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    if user.user_type != 'employer':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    jobs = Job.query.filter_by(employer_id=user.id).order_by(Job.posted_date.desc()).all()
    return render_template('my_jobs.html', user=user, jobs=jobs)

@jobs_bp.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    job = Job.query.get_or_404(job_id)
    
    if job.employer_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        job.title = request.form.get('title', job.title)
        job.company = request.form.get('company', job.company)
        job.location = request.form.get('location', job.location)
        job.salary_range = request.form.get('salary_range', job.salary_range)
        job.experience_required = request.form.get('experience_required', job.experience_required)
        job.job_type = request.form.get('job_type', job.job_type)
        job.description = request.form.get('description', job.description)
        job.requirements = request.form.get('requirements', job.requirements)
        job.skills_required = request.form.get('skills_required', job.skills_required)
        job.apply_method = request.form.get('apply_method', job.apply_method)
        job.apply_email = request.form.get('apply_email', job.apply_email)
        job.apply_website = request.form.get('apply_website', job.apply_website)
        job.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Job updated!', 'success')
        return redirect(url_for('jobs.my_jobs'))
    
    return render_template('edit_job.html', user=user, job=job)

@jobs_bp.route('/toggle-job/<int:job_id>')
def toggle_job(job_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user = db.session.get(User, session['user_id'])
    job = Job.query.get_or_404(job_id)
    
    if job.employer_id != user.id:
        return jsonify({'success': False}), 403
    
    job.is_active = not job.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': job.is_active})

@jobs_bp.route('/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user = db.session.get(User, session['user_id'])
    job = Job.query.get_or_404(job_id)
    
    if job.employer_id != user.id:
        return jsonify({'success': False}), 403
    
    db.session.delete(job)
    db.session.commit()
    return jsonify({'success': True})