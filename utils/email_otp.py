# utils/email_otp.py
import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ⚠️ PRODUCTION SETTINGS
SMTP_CONFIG = {
    'server': os.getenv("MAIL_SERVER") or 'smtp.gmail.com',
    'port': int(os.getenv("MAIL_PORT", 587)),
    'email': os.getenv("MAIL_USERNAME"),
    'password': os.getenv("MAIL_PASSWORD"),
    'use_tls': os.getenv("MAIL_USE_TLS", "True").lower() == "true",
}

# ⭐ Validate email configuration on startup
def _validate_email_config():
    """Validate SMTP configuration"""
    if not SMTP_CONFIG['email'] or not SMTP_CONFIG['password']:
        print("⚠️  WARNING: Email configuration incomplete!")
        print(f"   MAIL_USERNAME: {SMTP_CONFIG['email']}")
        print(f"   MAIL_PASSWORD: {'***' if SMTP_CONFIG['password'] else 'NOT SET'}")
        return False
    return True

_email_config_valid = _validate_email_config()

def generate_otp(length=6):
    """6-digit OTP जनरेट करें"""
    return ''.join(random.choices(string.digits, k=length))


def send_email(to_email, subject, html_body):
    """ईमेल भेजने का common function"""
    # ⭐ Check config validity
    if not _email_config_valid:
        print(f"❌ Email config is invalid. Cannot send to {to_email}")
        return False
    
    if not to_email or '@' not in to_email:
        print(f"❌ Invalid email address: {to_email}")
        return False
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Here I Am <{SMTP_CONFIG['email']}>"
            msg['To'] = to_email
            msg.attach(MIMEText(html_body, 'html'))

            # ⭐ Improved connection with timeout
            with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'], timeout=10) as server:
                if SMTP_CONFIG['use_tls']:
                    server.starttls()
                server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
                server.send_message(msg)

            print(f"✅ Email successfully sent to {to_email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error (Attempt {attempt+1}/{max_retries}): Invalid email/password")
            print(f"   Server: {SMTP_CONFIG['server']}, Port: {SMTP_CONFIG['port']}")
            return False
        except smtplib.SMTPException as e:
            print(f"⚠️  SMTP Error (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)  # Wait before retry
            else:
                return False
        except Exception as e:
            print(f"❌ Unexpected Error (Attempt {attempt+1}/{max_retries}): {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)  # Wait before retry
            else:
                return False
    
    return False


def send_email_otp(to_email, otp, purpose="verify"):
    """Verification OTP भेजें"""
    subject = "🔐 Here I Am - Email Verification OTP"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #8b5cf6; margin: 0;">Here I Am</h2>
                <p style="color: #64748b; margin: 4px 0 0;">Email Verification</p>
            </div>
            <div style="background: white; border-radius: 12px; padding: 24px; text-align: center;">
                <p style="color: #374151; font-size: 15px; margin: 0 0 16px;">Your verification code is:</p>
                <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; font-size: 36px; font-weight: 800; letter-spacing: 8px; padding: 16px 24px; border-radius: 12px; display: inline-block; margin: 0 0 16px;">
                    {otp}
                </div>
                <p style="color: #64748b; font-size: 13px; margin: 0;">This code will expire in 5 minutes.<br>Do not share this code with anyone.</p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center; margin: 20px 0 0;">If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """
    
    success = send_email(to_email, subject, html_body)
    if success:
        print(f"✅ Verification OTP sent to {to_email}")
    else:
        print(f"🔑 [FALLBACK] OTP for {to_email}: {otp}")
    return success


def send_password_reset_otp(to_email, otp):
    """Password Reset OTP भेजें"""
    subject = "🔐 Here I Am - Password Reset OTP"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #f59e0b; margin: 0;">Here I Am</h2>
                <p style="color: #64748b; margin: 4px 0 0;">Password Reset Request</p>
            </div>
            <div style="background: white; border-radius: 12px; padding: 24px; text-align: center;">
                <p style="color: #374151; font-size: 15px; margin: 0 0 16px;">
                    You requested to reset your password. Use this OTP:
                </p>
                <div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; font-size: 36px; font-weight: 800; letter-spacing: 8px; padding: 16px 24px; border-radius: 12px; display: inline-block; margin: 0 0 16px;">
                    {otp}
                </div>
                <p style="color: #64748b; font-size: 13px; margin: 0;">
                    This code will expire in 10 minutes.<br>
                    Do not share this code with anyone.
                </p>
            </div>
            <div style="background: #fef3c7; border-radius: 8px; padding: 12px; margin-top: 16px; text-align: center;">
                <p style="color: #92400e; font-size: 12px; margin: 0;">
                    <strong>⚠️ Security Notice:</strong> If you didn't request this, please ignore this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = send_email(to_email, subject, html_body)
    if success:
        print(f"✅ Password reset OTP sent to {to_email}")
    else:
        print(f"🔑 [FALLBACK] Reset OTP for {to_email}: {otp}")
    return success


# ⭐ NEW: Admin Login OTP
def send_admin_otp(to_email, otp):
    """Admin Panel Login OTP - Dark theme"""
    subject = "🔐 Admin Panel - Here I Am Login OTP"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #1e293b; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="font-size: 3rem; margin-bottom: 8px;">🛡️</div>
                <h2 style="color: #f59e0b; margin: 0;">Admin Panel Login</h2>
                <p style="color: #94a3b8; margin: 4px 0 0;">Here I Am - Professionals Data Bank</p>
            </div>
            <div style="background: #334155; border-radius: 12px; padding: 24px; text-align: center;">
                <p style="color: #e2e8f0; font-size: 15px; margin: 0 0 16px;">
                    Your admin login OTP is:
                </p>
                <div style="background: #f59e0b; color: #1e293b; font-size: 36px; font-weight: 800; letter-spacing: 8px; padding: 16px 24px; border-radius: 12px; display: inline-block; margin: 0 0 16px;">
                    {otp}
                </div>
                <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                    This code will expire in 5 minutes.<br>
                    If this wasn't you, secure your account immediately.
                </p>
            </div>
            <div style="background: #7f1d1d; border-radius: 8px; padding: 12px; margin-top: 16px; text-align: center;">
                <p style="color: #fca5a5; font-size: 12px; margin: 0;">
                    <strong>⚠️ Security Alert:</strong> Never share this OTP with anyone.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = send_email(to_email, subject, html_body)
    if success:
        print(f"✅ Admin OTP sent to {to_email}")
    else:
        print(f"\n{'='*60}")
        print(f"🔑 [FALLBACK] Admin OTP for {to_email}: {otp}")
        print(f"{'='*60}\n")
    return success