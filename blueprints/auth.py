# blueprints/auth.py
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User
from utils.email_otp import generate_otp, send_email_otp, send_password_reset_otp
auth_bp = Blueprint('auth', __name__)
otp_storage = {}  # {email: {'otp': '123456', 'expires': datetime, 'attempts': 0}}

def clean_expired_otps():
    """एक्सपायर्ड OTPs हटाएं"""
    now = datetime.utcnow()
    expired = [email for email, data in otp_storage.items() if data['expires'] < now]
    for email in expired:
        del otp_storage[email]

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '')
        domain = request.form.get('domain', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        user_type = request.form.get('user_type', 'jobseeker')
        company_name = request.form.get('company_name', '')
        company_website = request.form.get('company_website', '')
        
        # ⭐ Privacy settings
        show_email = request.form.get('show_email') == 'on'
        show_mobile = request.form.get('show_mobile') == 'on'
        
        # Check existing user
        existing_user = User.query.filter(
            (User.email == email) | (User.mobile == mobile)
        ).first()
        
        if existing_user:
            flash('Email or mobile already registered!', 'error')
            return redirect(url_for('auth.register'))
        
        # Generate OTP
        clean_expired_otps()
        otp = generate_otp()
        expires = datetime.utcnow() + timedelta(minutes=5)
        
        otp_storage[email] = {
            'otp': otp,
            'expires': expires,
            'attempts': 0,
            'data': {
                'email': email, 'mobile': mobile, 'password': password,
                'full_name': full_name, 'domain': domain, 'city': city, 'state': state,
                'user_type': user_type, 'company_name': company_name,
                'company_website': company_website,
                'show_email': show_email, 'show_mobile': show_mobile  # ⭐
            }
        }
        
        # ⭐ Send email OTP
        send_email_otp(email, otp, purpose="verify")
        
        flash('OTP sent to your email! Please check your inbox.', 'info')
        return render_template('verify_otp.html', email=email)
    
    return render_template('register.html')


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email', '').strip().lower()
    otp_entered = request.form.get('email_otp', '').strip()
    
    clean_expired_otps()
    
    stored = otp_storage.get(email)
    
    if not stored:
        flash('OTP expired or not found. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    # Check attempts
    if stored['attempts'] >= 5:
        del otp_storage[email]
        flash('Too many attempts. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    stored['attempts'] += 1
    
    # Check OTP
    if stored['otp'] != otp_entered:
        remaining = 5 - stored['attempts']
        flash(f'Invalid OTP! {remaining} attempts remaining.', 'error')
        return render_template('verify_otp.html', email=email)
    
    # Check expiry
    if stored['expires'] < datetime.utcnow():
        del otp_storage[email]
        flash('OTP expired! Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    # ⭐ OTP सही है - यूजर बनाएं
    data = stored['data']
    
    user = User(
        email=data['email'],
        mobile=data['mobile'],
        password=data['password'],
        full_name=data['full_name'],
        domain=data['domain'],
        city=data['city'],
        state=data['state'],
        user_type=data['user_type'],
        company_name=data['company_name'],
        company_website=data['company_website'],
        show_email=data.get('show_email', False),    # ⭐
        show_mobile=data.get('show_mobile', False),  # ⭐
        email_verified=True,
        mobile_verified=False,  # ⭐ Mobile verify नहीं
    )
    
    db.session.add(user)
    
    # ⭐ Retry on lock
    import time
    for attempt in range(5):
        try:
            db.session.commit()
            break
        except Exception as e:
            db.session.rollback()
            if 'database is locked' in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise e
    
    del otp_storage[email]
    session['user_id'] = user.id
    session['user_type'] = user.user_type
    
    if user.user_type == 'employer':
        flash('Registration successful! Post your first job.', 'success')
        return redirect(url_for('jobs.post_job'))
    else:
        flash('Registration successful! Upload your CV to complete your profile.', 'success')
        return redirect(url_for('profile.upload_cv'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        
        flash('Invalid email or password!', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('main.index'))
# blueprints/auth.py में ये नए रूट्स जोड़ें

# ============================================================
# FORGOT PASSWORD ROUTES
# ============================================================

# Temporary storage for reset tokens
reset_tokens = {}  # {email: {'otp': '123456', 'expires': datetime}}

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - send OTP to email"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not (security)
            flash('If this email is registered, you will receive a reset OTP.', 'info')
            return redirect(url_for('auth.login'))
        
        # Generate OTP
        clean_expired_otps()
        otp = generate_otp()
        expires = datetime.utcnow() + timedelta(minutes=10)
        
        reset_tokens[email] = {
            'otp': otp,
            'expires': expires,
            'attempts': 0,
            'user_id': user.id
        }
        
        # Send OTP via email
        from utils.email_otp import send_email_otp
        send_password_reset_otp(email, otp)
        
        session['reset_email'] = email
        flash('Password reset OTP sent to your email!', 'success')
        return redirect(url_for('auth.reset_password'))
    
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with OTP verification"""
    email = session.get('reset_email', '')
    
    if not email:
        flash('Please request password reset first.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp_entered = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html', email=email)
        
        # Check OTP
        stored = reset_tokens.get(email)
        
        if not stored:
            flash('Reset session expired. Please try again.', 'error')
            session.pop('reset_email', None)
            return redirect(url_for('auth.forgot_password'))
        
        if stored['expires'] < datetime.utcnow():
            del reset_tokens[email]
            session.pop('reset_email', None)
            flash('OTP expired! Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        stored['attempts'] += 1
        
        if stored['otp'] != otp_entered:
            remaining = 5 - stored['attempts']
            if remaining <= 0:
                del reset_tokens[email]
                session.pop('reset_email', None)
                flash('Too many attempts. Please try again.', 'error')
                return redirect(url_for('auth.forgot_password'))
            flash(f'Invalid OTP! {remaining} attempts remaining.', 'error')
            return render_template('reset_password.html', email=email)
        
        # OTP correct - update password
        user = db.session.get(User, stored['user_id'])
        
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        user.password = new_password
        db.session.commit()
        
        # Clean up
        del reset_tokens[email]
        session.pop('reset_email', None)
        
        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', email=email)


@auth_bp.route('/resend-reset-otp', methods=['POST'])
def resend_reset_otp():
    """Resend password reset OTP"""
    email = session.get('reset_email', '')
    
    if not email:
        return jsonify({'success': False, 'message': 'Session expired'}), 400
    
    clean_expired_otps()
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 400
    
    # Generate new OTP
    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)
    
    reset_tokens[email] = {
        'otp': otp,
        'expires': expires,
        'attempts': 0,
        'user_id': user.id
    }
    
    # Send OTP
    from utils.email_otp import send_password_reset_otp
    send_password_reset_otp(email, otp)
    
    return jsonify({'success': True, 'message': 'New OTP sent!'})

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """OTP दोबारा भेजें"""
    email = request.form.get('email', '').strip().lower()
    
    clean_expired_otps()
    stored = otp_storage.get(email)
    
    if not stored:
        flash('Session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    # New OTP
    otp = generate_otp()
    stored['otp'] = otp
    stored['expires'] = datetime.utcnow() + timedelta(minutes=5)
    stored['attempts'] = 0
    
    send_email_otp(email, otp, purpose="verify")
    
    flash('New OTP sent to your email!', 'info')
    return render_template('verify_otp.html', email=email)