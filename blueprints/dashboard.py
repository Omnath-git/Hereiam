# blueprints/dashboard.py
from flask import Blueprint, render_template, session, flash, redirect, url_for
from models import db, User, Job

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('auth.login'))
    
    user = db.session.get(User, session['user_id'])
    
    if not user.profile_complete and user.user_type == 'jobseeker':
        flash('Please upload your CV to complete your profile.', 'info')
        return redirect(url_for('profile.upload_cv'))
    
    if user.user_type == 'employer':
        active_jobs = Job.query.filter_by(employer_id=user.id, is_active=True).count()
        total_jobs = Job.query.filter_by(employer_id=user.id).count()
        return render_template('dashboard.html', user=user, active_jobs=active_jobs, total_jobs=total_jobs)
    
    return render_template('dashboard.html', user=user)