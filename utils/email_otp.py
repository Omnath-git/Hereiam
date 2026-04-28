# utils/email_otp.py
# ⭐ नई फाइल बनाएं

import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# ⚠️ PRODUCTION SETTINGS - अपनी ईमेल सेटिंग्स डालें
SMTP_CONFIG = {
    'server': os.getenv("MAIL_SERVER") or 'smtp.gmail.com',
    'port': int(os.getenv("MAIL_PORT", 587)),
    'email': os.getenv("MAIL_USERNAME"),
    'password': os.getenv("MAIL_PASSWORD"),
    'use_tls': True,
}

def generate_otp(length=6):
    """6-digit OTP जनरेट करें"""
    return ''.join(random.choices(string.digits, k=length))


def send_email(to_email, subject, html_body):
    """ईमेल भेजने का common function"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Professionals Data Bank <{SMTP_CONFIG['email']}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
            if SMTP_CONFIG['use_tls']:
                server.starttls()
            server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_email_otp(to_email, otp, purpose="verify"):
    """Verification OTP भेजें"""
    subject = "🔐 Professionals Data Bank - Email Verification OTP"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #8b5cf6; margin: 0;">Professionals Data Bank</h2>
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
    """⭐ Password Reset OTP भेजें"""
    subject = "🔐 Professionals Data Bank - Password Reset OTP"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #f59e0b; margin: 0;">Professionals Data Bank</h2>
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