# blueprints/admin.py
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Job, Admin
from utils.email_otp import send_email_otp, generate_otp,send_admin_otp

admin_bp = Blueprint('admin', __name__)

# Admin OTP storage
admin_otp_storage = {}

# ⭐ Admin email - सिर्फ यही ईमेल एक्सेस कर सकता है
ADMIN_EMAIL = "omnath.mail@gmail.com"


@admin_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page - OTP based"""
    
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        # ⭐ STEP 1: Get Password (Send OTP)
        if action == 'get_otp':
            email = request.form.get('email', '').strip().lower()
            
            if email != ADMIN_EMAIL:
                flash('Invalid admin email!', 'error')
                return render_template('admin_login.html')
            
            # Generate OTP
            otp = generate_otp(6)
            expires = datetime.utcnow() + timedelta(minutes=5)
            
            admin_otp_storage[email] = {
                'otp': otp,
                'expires': expires,
                'attempts': 0
            }
            
            # ⭐ OTP भेजें - same function as registration
            from utils.email_otp import send_email_otp
            
            # Admin के लिए खास subject के साथ
            success = send_email_otp(email, otp, purpose="verify")
            
            if success:
                flash('OTP sent to your email! Please check.', 'success')
            else:
                # Console में print करें
                print(f"\n{'='*60}")
                print(f"🔑 ADMIN OTP for {email}: {otp}")
                print(f"{'='*60}\n")
                flash(f'Email sending failed. Check server console for OTP.', 'warning')
            
            session['admin_email'] = email
            return render_template('admin_login.html', otp_sent=True, email=email)
        
        # ⭐ STEP 2: Verify OTP & Login
        elif action == 'login':
            email = session.get('admin_email', '')
            otp_entered = request.form.get('otp', '').strip()
            
            if not email:
                flash('Session expired. Please try again.', 'error')
                return redirect(url_for('admin.admin_login'))
            
            stored = admin_otp_storage.get(email)
            
            if not stored:
                flash('OTP expired. Please request a new one.', 'error')
                return redirect(url_for('admin.admin_login'))
            
            # Check expiry
            if stored['expires'] < datetime.utcnow():
                del admin_otp_storage[email]
                session.pop('admin_email', None)
                flash('OTP expired! Please request a new one.', 'error')
                return redirect(url_for('admin.admin_login'))
            
            # Check attempts
            stored['attempts'] += 1
            if stored['attempts'] > 5:
                del admin_otp_storage[email]
                session.pop('admin_email', None)
                flash('Too many attempts! Please try again.', 'error')
                return redirect(url_for('admin.admin_login'))
            
            # Verify OTP
            if stored['otp'] != otp_entered:
                remaining = 5 - stored['attempts']
                flash(f'Invalid OTP! {remaining} attempts remaining.', 'error')
                return render_template('admin_login.html', otp_sent=True, email=email)
            
            # ✅ OTP correct - Login
            del admin_otp_storage[email]
            session['admin_logged_in'] = True
            session.pop('admin_email', None)
            
            # Create admin record if not exists
            admin = Admin.query.filter_by(email=email).first()
            if not admin:
                admin = Admin(email=email, name='Super Admin')
                db.session.add(admin)
                db.session.commit()
            
            flash('Welcome Admin! 🎉', 'success')
            return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('admin_login.html', otp_sent=False)

@admin_bp.route('/admin-dashboard')
def admin_dashboard():
    """Admin Dashboard - सभी डेटा मैनेज करें"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin.admin_login'))
    
    # Stats
    total_users = User.query.count()
    total_professionals = User.query.filter_by(user_type='jobseeker').count()
    total_employers = User.query.filter_by(user_type='employer').count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(is_active=True).count()
    scraped_jobs = Job.query.filter_by(source='scraped').count()
    user_jobs = Job.query.filter_by(source='user').count()
    verified_users = User.query.filter_by(email_verified=True).count()
    profile_complete = User.query.filter_by(profile_complete=True).count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent jobs
    recent_jobs = Job.query.order_by(Job.posted_date.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_professionals=total_professionals,
                         total_employers=total_employers,
                         total_jobs=total_jobs,
                         active_jobs=active_jobs,
                         scraped_jobs=scraped_jobs,
                         user_jobs=user_jobs,
                         verified_users=verified_users,
                         profile_complete=profile_complete,
                         recent_users=recent_users,
                         recent_jobs=recent_jobs)


@admin_bp.route('/admin/users')
def admin_users():
    """View all users"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin.admin_login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.email.contains(search)) |
            (User.mobile.contains(search)) |
            (User.domain.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin_users.html', users=users, search=search)


@admin_bp.route('/admin/jobs')
def admin_jobs():
    """View all jobs"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin.admin_login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    source = request.args.get('source', '')
    
    query = Job.query
    
    if search:
        query = query.filter(
            (Job.title.contains(search)) |
            (Job.company.contains(search)) |
            (Job.location.contains(search))
        )
    
    if source:
        query = query.filter_by(source=source)
    
    jobs = query.order_by(Job.posted_date.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin_jobs.html', jobs=jobs, search=search, source=source)


@admin_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Delete user's jobs if employer
    if user.user_type == 'employer':
        Job.query.filter_by(employer_id=user.id).delete()
    
    # Delete profile HTML file
    if user.profile_url:
        from flask import current_app
        import os
        filepath = os.path.join(current_app.config['PROFILES_FOLDER'], user.profile_url)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully!'})


@admin_bp.route('/admin/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    db.session.delete(job)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Job deleted successfully!'})


@admin_bp.route('/admin/reports')
def admin_reports():
    """View reports"""
    if not session.get('admin_logged_in'):
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin.admin_login'))
    
    # Domain-wise user count
    from sqlalchemy import func
    domain_stats = db.session.query(
        User.domain, func.count(User.id)
    ).filter(User.domain != '').group_by(User.domain).order_by(func.count(User.id).desc()).all()
    
    # City-wise user count
    city_stats = db.session.query(
        User.city, func.count(User.id)
    ).filter(User.city != '').group_by(User.city).order_by(func.count(User.id).desc()).limit(20).all()
    
    # User type stats
    user_type_stats = db.session.query(
        User.user_type, func.count(User.id)
    ).group_by(User.user_type).all()
    
    # Daily registrations (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_registrations = db.session.query(
        func.date(User.created_at), func.count(User.id)
    ).filter(User.created_at >= thirty_days_ago).group_by(func.date(User.created_at)).all()
    
    # Job source stats
    job_source_stats = db.session.query(
        Job.source, func.count(Job.id)
    ).group_by(Job.source).all()
    
    return render_template('admin_reports.html',
                         domain_stats=domain_stats,
                         city_stats=city_stats,
                         user_type_stats=user_type_stats,
                         daily_registrations=daily_registrations,
                         job_source_stats=job_source_stats)


@admin_bp.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    flash('Admin logged out!', 'info')
    return redirect(url_for('admin.admin_login'))