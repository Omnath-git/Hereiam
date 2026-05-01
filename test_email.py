# test_email.py - V5 फोल्डर में बनाएं और रन करें
import smtplib
from email.mime.text import MIMEText

# Bluehost Settings टेस्ट करें
configs = [
    {'server': 'mail.hereiam.in', 'port': 465, 'ssl': True},
    {'server': 'mail.hereiam.in', 'port': 587, 'ssl': False},
    {'server': 'smtp.gmail.com', 'port': 587, 'ssl': False},
]

email = 'support.hereiam@gmail.com'
password = 'ompohouboqtrzggf'
to = 'omnath.mail@gmail.com'  # जहाँ OTP जाना चाहिए

for config in configs:
    try:
        print(f"\n🔍 Testing: {config['server']}:{config['port']}...")
        
        if config['ssl']:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
        else:
            server = smtplib.SMTP(config['server'], config['port'], timeout=10)
            server.starttls()
        
        server.login(email, password)
        
        msg = MIMEText(f"Test email from {config['server']}")
        msg['Subject'] = f"Test - {config['server']}:{config['port']}"
        msg['From'] = email
        msg['To'] = to
        
        server.sendmail(email, to, msg.as_string())
        server.quit()
        print(f"✅ SUCCESS: {config['server']}:{config['port']}")
        
    except Exception as e:
        print(f"❌ FAILED: {config['server']}:{config['port']} - {str(e)[:100]}")