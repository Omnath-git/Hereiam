# blueprints/auth.py
import random
import string
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User
from utils.email_otp import generate_otp, send_email_otp, send_password_reset_otp

auth_bp = Blueprint('auth', __name__)

# OTP Storage - 30 minutes expiry
otp_storage = {}
reset_tokens = {}


# ============================================================
# AUTO CLEAN FUNCTIONS
# ============================================================

def clean_expired_otps():
    """सभी expired OTPs हटाएं"""
    now = datetime.utcnow()
    expired_reg = [email for email, data in otp_storage.items() if data['expires'] < now]
    for email in expired_reg:
        del otp_storage[email]
    
    expired_reset = [email for email, data in reset_tokens.items() if data['expires'] < now]
    for email in expired_reset:
        del reset_tokens[email]
    
    if expired_reg or expired_reset:
        print(f"🧹 Cleaned {len(expired_reg)} reg + {len(expired_reset)} reset expired OTPs")


def clean_old_otp_for_email(email):
    """किसी ईमेल का पुराना OTP हटाएं"""
    cleaned = False
    if email in otp_storage:
        old_otp = otp_storage[email]['otp']
        del otp_storage[email]
        print(f"🔄 Removed old OTP ({old_otp}) for {email}")
        cleaned = True
    if email in reset_tokens:
        old_otp = reset_tokens[email]['otp']
        del reset_tokens[email]
        print(f"🔄 Removed old reset OTP ({old_otp}) for {email}")
        cleaned = True
    return cleaned


# Auto clean every 5 minutes
@auth_bp.before_request
def auto_clean_before_request():
    current_time = time.time()
    if not hasattr(auth_bp, '_last_clean_time'):
        auth_bp._last_clean_time = 0
    if current_time - auth_bp._last_clean_time > 300:
        clean_expired_otps()
        auth_bp._last_clean_time = current_time


# ============================================================
# REGISTER
# ============================================================

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
        show_email = request.form.get('show_email') == 'on'
        show_mobile = request.form.get('show_mobile') == 'on'
        
        existing_user = User.query.filter(
            (User.email == email) | (User.mobile == mobile)
        ).first()
        
        if existing_user:
            flash('Email or mobile already registered!', 'error')
            return redirect(url_for('auth.register'))
        
        # Clean old OTPs
        clean_old_otp_for_email(email)
        clean_expired_otps()
        
        # Generate new OTP - 30 minutes expiry
        otp = generate_otp(6)
        expires = datetime.utcnow() + timedelta(minutes=30)
        
        otp_storage[email] = {
            'otp': otp, 'expires': expires, 'attempts': 0,
            'created_at': datetime.utcnow(),
            'data': {
                'email': email, 'mobile': mobile, 'password': password,
                'full_name': full_name, 'domain': domain, 'city': city, 'state': state,
                'user_type': user_type, 'company_name': company_name,
                'company_website': company_website,
                'show_email': show_email, 'show_mobile': show_mobile
            }
        }
        
        success = send_email_otp(email, otp, purpose="verify")
        
        if success:
            flash('OTP sent to your email! Valid for 30 minutes. Check spam folder too.', 'info')
        else:
            print(f"\n{'='*60}")
            print(f"🔑 REGISTRATION OTP for {email}: {otp}")
            print(f"⏰ Expires: {expires.strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            flash('Email sending failed. Check server console for OTP.', 'warning')
        
        return render_template('verify_otp.html', email=email, mobile=mobile)
    
    return render_template('register.html')


# ============================================================
# VERIFY OTP
# ============================================================

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email', '').strip().lower()
    mobile = request.form.get('mobile', '').strip()
    otp_entered = request.form.get('email_otp', '').strip()
    
    clean_expired_otps()
    
    stored = otp_storage.get(email)
    
    if not stored:
        flash('OTP expired or not found. Please register again to get a new OTP.', 'error')
        return redirect(url_for('auth.register'))
    
    if stored['expires'] < datetime.utcnow():
        del otp_storage[email]
        flash('OTP has expired (30 minutes). Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    # Check OTP
    if str(stored['otp']).strip() != str(otp_entered).strip():
        stored['attempts'] = stored.get('attempts', 0) + 1
        if stored['attempts'] >= 3:
            flash(f'Wrong OTP! Tried {stored["attempts"]} times. Try again or resend OTP.', 'warning')
        else:
            flash(f'Invalid OTP! Please try again.', 'error')
        return render_template('verify_otp.html', email=email, mobile=mobile)
    
    # OTP correct - Create user
    data = stored['data']
    
    user = User(
        email=data['email'], mobile=data['mobile'], password=data['password'],
        full_name=data['full_name'], domain=data['domain'],
        city=data['city'], state=data['state'],
        user_type=data['user_type'], company_name=data['company_name'],
        company_website=data['company_website'],
        show_email=data.get('show_email', False),
        show_mobile=data.get('show_mobile', False),
        email_verified=True, mobile_verified=False,
    )
    
    db.session.add(user)
    
    try:
        db.session.commit()
        print(f"✅ User created: {email}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating user: {e}")
        flash('Registration failed. Please try again.', 'error')
        return redirect(url_for('auth.register'))
    
    # Clean used OTP
    del otp_storage[email]
    print(f"✅ OTP verified and cleaned for {email}")
    
    session['user_id'] = user.id
    session['user_type'] = user.user_type
    
    if user.user_type == 'employer':
        flash('Registration successful! Post your first job.', 'success')
        return redirect(url_for('jobs.post_job'))
    else:
        flash('Registration successful! Upload your CV to complete your profile.', 'success')
        return redirect(url_for('profile.upload_cv'))


# ============================================================
# RESEND OTP
# ============================================================

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = request.form.get('email', '').strip().lower()
    
    clean_expired_otps()
    stored = otp_storage.get(email)
    
    if not stored:
        flash('Session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    old_otp = stored['otp']
    otp = generate_otp(6)
    stored['otp'] = otp
    stored['expires'] = datetime.utcnow() + timedelta(minutes=30)
    stored['attempts'] = 0
    
    print(f"🔄 Resent OTP for {email}: {otp} (old: {old_otp})")
    
    success = send_email_otp(email, otp, purpose="verify")
    
    if success:
        flash('New OTP sent! Valid for 30 minutes.', 'info')
    else:
        print(f"\n{'='*60}")
        print(f"🔑 RESENT OTP for {email}: {otp}")
        print(f"{'='*60}\n")
        flash('New OTP generated. Check server console if email not received.', 'warning')
    
    return render_template('verify_otp.html', email=email, mobile=stored['data'].get('mobile', ''))


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        
        flash('Invalid email or password!', 'error')
    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('main.index'))


# ============================================================
# FORGOT PASSWORD
# ============================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('If this email is registered, you will receive a reset OTP.', 'info')
            return redirect(url_for('auth.login'))
        
        clean_old_otp_for_email(email)
        clean_expired_otps()
        
        otp = generate_otp(6)
        expires = datetime.utcnow() + timedelta(minutes=30)
        
        reset_tokens[email] = {
            'otp': otp, 'expires': expires, 'attempts': 0,
            'created_at': datetime.utcnow(), 'user_id': user.id
        }
        
        success = send_password_reset_otp(email, otp)
        session['reset_email'] = email
        
        if success:
            flash('Password reset OTP sent! Valid for 30 minutes. Check spam folder.', 'success')
        else:
            print(f"\n🔑 PASSWORD RESET OTP for {email}: {otp} ⏰ Expires: {expires.strftime('%H:%M:%S')}\n")
            flash('Email sending failed. Check server console for OTP.', 'warning')
        
        return redirect(url_for('auth.reset_password'))
    
    return render_template('forgot_password.html')


# ============================================================
# RESET PASSWORD
# ============================================================

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email', '')
    
    if not email:
        flash('Please request password reset first.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp_entered = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html', email=email)
        
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
        
        if str(stored['otp']).strip() != str(otp_entered).strip():
            stored['attempts'] = stored.get('attempts', 0) + 1
            flash(f'Invalid OTP! Please try again.', 'error')
            return render_template('reset_password.html', email=email)
        
        user = db.session.get(User, stored['user_id'])
        
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        user.password = new_password
        db.session.commit()
        
        del reset_tokens[email]
        session.pop('reset_email', None)
        print(f"✅ Password reset for {email}")
        
        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', email=email)


# ============================================================
# RESEND RESET OTP
# ============================================================

@auth_bp.route('/resend-reset-otp', methods=['POST'])
def resend_reset_otp():
    email = session.get('reset_email', '')
    
    if not email:
        return jsonify({'success': False, 'message': 'Session expired'}), 400
    
    clean_expired_otps()
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 400
    
    if email in reset_tokens:
        del reset_tokens[email]
    
    otp = generate_otp(6)
    expires = datetime.utcnow() + timedelta(minutes=30)
    
    reset_tokens[email] = {
        'otp': otp, 'expires': expires, 'attempts': 0, 'user_id': user.id
    }
    
    success = send_password_reset_otp(email, otp)
    print(f"🔄 Resent reset OTP for {email}: {otp}")
    
    if success:
        return jsonify({'success': True, 'message': 'New OTP sent!'})
    else:
        print(f"\n🔑 RESENT RESET OTP for {email}: {otp}\n")
        return jsonify({'success': True, 'message': 'New OTP generated. Check console.'})


# ============================================================
# GET DEMO OTP (Development only - REMOVE IN PRODUCTION)
# ============================================================

@auth_bp.route('/get-demo-otp')
def get_demo_otp():
    email = request.args.get('email')
    if email in otp_storage:
        return jsonify({'email_otp': otp_storage[email]['otp']})
    return jsonify({'error': 'OTP not found'}), 404