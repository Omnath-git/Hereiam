# utils/profile_generator.py
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.helpers import safe_json_loads

def generate_profile_html(user, app):
    """Generate beautiful, modern HTML profile page"""
    try:
        skills = safe_json_loads(user.skills)
        education = safe_json_loads(user.education)
        experience = safe_json_loads(user.experience)
        projects = safe_json_loads(user.projects)
        certifications = safe_json_loads(user.certifications)
        languages = safe_json_loads(user.languages)
        achievements = safe_json_loads(user.achievements)
        
        # Create safe filename with TIMESTAMP
        full_name = (user.full_name or 'User').replace(' ', '_')
        domain = (user.domain or 'General').replace(' ', '_')
        city = (user.city or 'City').replace(' ', '_')
        state = (user.state or 'State').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{full_name}_{domain}_{city}_{state}_{timestamp}.html"
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['PROFILES_FOLDER'], filename)
        
        # Delete old profile
        if user.profile_url and user.profile_url != filename:
            old_path = os.path.join(app.config['PROFILES_FOLDER'], user.profile_url)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Profile photo
        profile_photo_url = f"../static/{user.profile_photo}" if user.profile_photo else "../static/uploads/profile_photos/avatar.png"
        
        # Privacy
        if user.show_email:
            email_display = user.email
            email_link = f"mailto:{user.email}"
        else:
            parts = user.email.split('@')
            email_display = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else 'Hidden'
            email_link = "#"
        
        if user.show_mobile:
            mobile_display = user.mobile
            mobile_link = f"tel:{user.mobile}"
        else:
            mobile_display = user.mobile[:3] + '****' + user.mobile[-3:] if len(user.mobile) >= 10 else 'Hidden'
            mobile_link = "#"
        
        # Build HTML
        html = build_complete_html(
            user, profile_photo_url,
            email_display, email_link,
            mobile_display, mobile_link,
            skills, education, experience, projects,
            certifications, languages, achievements
        )
        
        # Save
        os.makedirs(app.config['PROFILES_FOLDER'], exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Profile generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def build_complete_html(user, photo_url, email_display, email_link, mobile_display, mobile_link,
                        skills, education, experience, projects, certifications, languages, achievements):
    """Build complete HTML"""
    
    sections_html = build_all_sections(
        user, skills, education, experience, projects,
        certifications, languages, achievements
    )
    
    # ⭐ Social links
    social_links = build_social_links(user)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{user.full_name} - {user.domain} | Here I am">
    <title>{user.full_name} - {user.domain} | Here I am</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --primary-bg: #eef2ff;
            --secondary: #64748b;
            --dark: #0f172a;
            --dark-2: #1e293b;
            --light: #f8fafc;
            --light-2: #f1f5f9;
            --white: #ffffff;
            --success: #10b981;
            --success-light: #d1fae5;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
            --danger: #ef4444;
            --danger-light: #fee2e2;
            --info: #3b82f6;
            --info-light: #dbeafe;
            --purple: #8b5cf6;
            --gradient-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            --gradient-2: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            --gradient-hero: linear-gradient(160deg, #eef2ff 0%, #e0e7ff 30%, #f8fafc 100%);
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
            --shadow-lg: 0 10px 25px -5px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 40px -10px rgba(0,0,0,0.1);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --radius-2xl: 24px;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
            background: var(--light);
            color: var(--dark-2);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* ============ NAVBAR ============ */
        .navbar {{
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 14px 0;
            border-bottom: 1px solid rgba(226,232,240,0.8);
            transition: all 0.3s;
        }}
        .navbar.scrolled {{ box-shadow: var(--shadow-lg); }}
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--dark);
        }}
        .nav-brand-icon {{
            width: 38px;
            height: 38px;
            background: var(--gradient-1);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1rem;
        }}
        .nav-links {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .nav-link {{
            color: var(--secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.85rem;
            padding: 8px 14px;
            border-radius: var(--radius-sm);
            transition: all 0.2s;
        }}
        .nav-link:hover {{ color: var(--primary); background: var(--primary-bg); }}
        
        /* ============ HERO ============ */
        .hero {{
            background: var(--gradient-hero);
            padding: 140px 0 80px;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: -100px;
            right: -100px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .hero::after {{
            content: '';
            position: absolute;
            bottom: -80px;
            left: -80px;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .hero-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            gap: 60px;
            position: relative;
            z-index: 1;
        }}
        .hero-content {{ flex: 1; }}
        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: white;
            color: var(--primary);
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 16px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--primary-bg);
        }}
        .hero-badge i {{ font-size: 0.7rem; }}
        .hero-name {{
            font-family: 'Playfair Display', serif;
            font-size: 3.8rem;
            font-weight: 800;
            color: var(--dark);
            line-height: 1.1;
            margin-bottom: 12px;
            letter-spacing: -1px;
        }}
        .hero-title-text {{
            font-size: 1.2rem;
            color: var(--primary);
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .hero-summary {{
            font-size: 1rem;
            color: var(--secondary);
            margin-bottom: 24px;
            max-width: 600px;
            line-height: 1.7;
        }}
        .hero-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 24px;
        }}
        .hero-meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
            padding: 10px 18px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid #e2e8f0;
            color: var(--dark-2);
        }}
        .hero-meta-item i {{ color: var(--primary); font-size: 0.9rem; }}
        .hero-meta-item .salary {{ color: var(--success); }}
        .hero-meta-item .notice {{ color: var(--warning); }}
        
        .hero-photo-wrapper {{
            flex-shrink: 0;
            position: relative;
        }}
        .hero-photo-ring {{
            position: absolute;
            inset: -15px;
            border-radius: 50%;
            border: 3px dashed var(--primary-light);
            opacity: 0.4;
            animation: spin 30s linear infinite;
        }}
        @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        .hero-photo {{
            width: 260px;
            height: 260px;
            border-radius: 50%;
            overflow: hidden;
            border: 6px solid white;
            box-shadow: var(--shadow-xl);
            position: relative;
            z-index: 1;
        }}
        .hero-photo img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        /* ============ MAIN LAYOUT ============ */
        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 32px;
            margin-top: -30px;
            position: relative;
            z-index: 10;
        }}
        
        /* ============ SECTION CARD ============ */
        .section-card {{
            background: white;
            border-radius: var(--radius-xl);
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
            border: 1px solid #f1f5f9;
            transition: all 0.3s;
        }}
        .section-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }}
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 24px;
            padding-bottom: 14px;
            border-bottom: 2px solid var(--light-2);
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .section-title i {{
            color: var(--primary);
            font-size: 1.3rem;
        }}
        .section-subtitle {{
            color: var(--secondary);
            font-size: 0.9rem;
            margin-bottom: 20px;
            line-height: 1.6;
        }}
        
        /* ============ SKILLS ============ */
        .skills-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .skill-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--primary-bg);
            color: var(--primary-dark);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.3s;
            border: 1px solid transparent;
        }}
        .skill-item:hover {{
            background: var(--primary);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99,102,241,0.3);
        }}
        .skill-item.skill-level-expert {{
            background: linear-gradient(135deg, #dbeafe, #ede9fe);
            border-color: #c4b5fd;
        }}
        .skill-item.skill-level-advanced {{
            background: #f0fdf4;
            border-color: #bbf7d0;
        }}
        
        /* ============ EXPERIENCE TIMELINE ============ */
        .timeline {{ position: relative; padding-left: 32px; }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, var(--primary), var(--primary-light), transparent);
        }}
        .timeline-item {{
            position: relative;
            margin-bottom: 32px;
            padding-left: 24px;
        }}
        .timeline-item:last-child {{ margin-bottom: 0; }}
        .timeline-dot {{
            position: absolute;
            left: -28px;
            top: 6px;
            width: 14px;
            height: 14px;
            background: var(--primary);
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 4px var(--primary-bg);
        }}
        .timeline-dot.current {{
            background: var(--success);
            box-shadow: 0 0 0 4px var(--success-light);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 0 4px var(--success-light); }}
            50% {{ box-shadow: 0 0 0 10px rgba(16,185,129,0.1); }}
        }}
        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 6px;
        }}
        .timeline-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--dark);
        }}
        .timeline-company {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--primary);
        }}
        .timeline-duration {{
            display: inline-block;
            background: var(--primary-bg);
            color: var(--primary-dark);
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .timeline-duration.current-duration {{
            background: var(--success-light);
            color: #065f46;
        }}
        .timeline-description {{
            font-size: 0.88rem;
            color: var(--secondary);
            margin-top: 8px;
            line-height: 1.7;
        }}
        
        /* ============ EDUCATION ============ */
        .education-item {{
            display: flex;
            gap: 16px;
            padding: 16px;
            margin-bottom: 16px;
            background: var(--light-2);
            border-radius: var(--radius-md);
            border-left: 4px solid var(--primary);
            transition: all 0.3s;
        }}
        .education-item:hover {{
            background: white;
            box-shadow: var(--shadow-md);
            border-left-color: var(--primary-dark);
        }}
        .education-icon {{
            width: 44px;
            height: 44px;
            background: var(--primary-bg);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
            font-size: 1.1rem;
            flex-shrink: 0;
        }}
        .education-info {{ flex: 1; }}
        .education-degree {{
            font-weight: 700;
            color: var(--dark);
            font-size: 0.95rem;
            margin-bottom: 2px;
        }}
        .education-institution {{
            color: var(--secondary);
            font-size: 0.85rem;
        }}
        .education-year {{
            display: inline-block;
            background: white;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            color: var(--secondary);
            margin-top: 4px;
        }}
        
        /* ============ PROJECTS ============ */
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}
        .project-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: var(--radius-lg);
            padding: 20px;
            transition: all 0.3s;
        }}
        .project-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-3px);
            border-color: var(--primary-light);
        }}
        .project-card-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .project-icon {{
            width: 40px;
            height: 40px;
            background: var(--gradient-1);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            flex-shrink: 0;
        }}
        .project-name {{
            font-weight: 700;
            font-size: 0.95rem;
            color: var(--dark);
        }}
        .project-desc {{
            font-size: 0.82rem;
            color: var(--secondary);
            margin-bottom: 10px;
            line-height: 1.6;
        }}
        .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}
        .project-tech-tag {{
            background: var(--light-2);
            color: var(--secondary);
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 500;
        }}
        
        /* ============ CERTIFICATIONS ============ */
        .cert-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .cert-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #fef3c7, #fef9c3);
            padding: 10px 16px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.82rem;
            color: #92400e;
            border: 1px solid #fde68a;
        }}
        .cert-item i {{ color: var(--warning); }}
        
        /* ============ LANGUAGES ============ */
        .lang-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .lang-item {{
            background: white;
            border: 2px solid #e2e8f0;
            padding: 8px 16px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--dark-2);
            transition: all 0.3s;
        }}
        .lang-item:hover {{
            border-color: var(--primary);
            color: var(--primary);
            transform: translateY(-2px);
        }}
        
        /* ============ ACHIEVEMENTS ============ */
        .achievement-item {{
            display: flex;
            gap: 14px;
            padding: 14px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #faf5ff, #f5f3ff);
            border-radius: var(--radius-md);
            border-left: 3px solid var(--purple);
        }}
        .achievement-item i {{ color: var(--warning); font-size: 1.1rem; margin-top: 2px; }}
        .achievement-item span {{ color: var(--dark-2); font-weight: 500; font-size: 0.9rem; }}
        
        /* ============ SIDEBAR ============ */
        .sidebar-card {{
            background: white;
            border-radius: var(--radius-xl);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-sm);
            border: 1px solid #f1f5f9;
            text-align: center;
        }}
        .sidebar-avatar {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid white;
            box-shadow: var(--shadow-lg);
            margin-bottom: 12px;
        }}
        .sidebar-name {{
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--dark);
            margin-bottom: 2px;
        }}
        .sidebar-domain {{
            color: var(--primary);
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 16px;
        }}
        .sidebar-info-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 0;
            border-bottom: 1px solid var(--light-2);
            font-size: 0.82rem;
            color: var(--secondary);
        }}
        .sidebar-info-item:last-child {{ border-bottom: none; }}
        .sidebar-info-item i {{
            width: 20px;
            color: var(--primary);
            text-align: center;
        }}
        
        /* ============ CONTACT SECTION ============ */
        .contact-section {{
            background: var(--gradient-2);
            border-radius: var(--radius-xl);
            padding: 48px;
            text-align: center;
            color: white;
            margin-top: 24px;
        }}
        .contact-section h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            margin-bottom: 8px;
        }}
        .contact-section p {{ opacity: 0.8; margin-bottom: 24px; }}
        .contact-buttons {{
            display: flex;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        }}
        .contact-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 50px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s;
            font-size: 0.9rem;
        }}
        .contact-btn-email {{
            background: white;
            color: var(--dark);
        }}
        .contact-btn-email:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            color: var(--dark);
        }}
        .contact-btn-phone {{
            background: rgba(255,255,255,0.15);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        .contact-btn-phone:hover {{
            background: rgba(255,255,255,0.25);
            transform: translateY(-2px);
            color: white;
        }}
        
        /* ============ SOCIAL LINKS ============ */
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 16px;
        }}
        .social-link {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1rem;
            transition: all 0.3s;
            text-decoration: none;
        }}
        .social-link:hover {{
            transform: translateY(-4px);
            color: white;
        }}
        .social-link.linkedin {{ background: #0077b5; }}
        .social-link.github {{ background: #333; }}
        .social-link.website {{ background: var(--success); }}
        
        /* ============ FOOTER ============ */
        .footer {{
            text-align: center;
            padding: 32px;
            color: var(--secondary);
            font-size: 0.8rem;
            border-top: 1px solid #e2e8f0;
            margin-top: 40px;
        }}
        
        /* ============ RESPONSIVE ============ */
        @media (max-width: 1024px) {{
            .main-container {{
                grid-template-columns: 1fr;
            }}
            .hero-container {{
                flex-direction: column-reverse;
                text-align: center;
                gap: 30px;
            }}
            .hero-name {{ font-size: 2.5rem; }}
            .hero-summary {{ margin: 0 auto 24px; }}
            .hero-meta {{ justify-content: center; }}
            .hero-photo {{ width: 180px; height: 180px; }}
        }}
        @media (max-width: 768px) {{
            .hero {{ padding: 120px 0 60px; }}
            .hero-name {{ font-size: 2rem; }}
            .section-card {{ padding: 20px; }}
            .projects-grid {{ grid-template-columns: 1fr; }}
            .contact-section {{ padding: 32px 20px; }}
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar" id="navbar">
        <div class="nav-container">
            <a href="#" class="nav-brand">
                <span class="nav-brand-icon"><i class="fas fa-database"></i></span>
                Here I am
            </a>
            <div class="nav-links">
                <a href="#about" class="nav-link">About</a>
                <a href="#skills" class="nav-link">Skills</a>
                <a href="#experience" class="nav-link">Experience</a>
                <a href="#education" class="nav-link">Education</a>
                <a href="#projects" class="nav-link">Projects</a>
                <a href="#contact" class="nav-link">Contact</a>
            </div>
        </div>
    </nav>
    
    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <div class="hero-badge">
                    <i class="fas fa-check-circle"></i> Verified Professional
                </div>
                <h1 class="hero-name">{user.full_name}</h1>
                <p class="hero-title-text">{user.domain}</p>
                <p class="hero-summary">{user.summary or ''}</p>
                <div class="hero-meta">
                    <span class="hero-meta-item">
                        <i class="fas fa-clock"></i> {user.experience_years or 'Fresher'}
                    </span>
                    <span class="hero-meta-item">
                        <i class="fas fa-map-marker-alt"></i> {user.city}, {user.state}
                    </span>
                    {f'<span class="hero-meta-item"><i class="fas fa-rupee-sign salary"></i> {user.expected_salary}</span>' if user.expected_salary else ''}
                    {f'<span class="hero-meta-item"><i class="fas fa-calendar-alt notice"></i> {user.notice_period}</span>' if user.notice_period else ''}
                </div>
            </div>
            <div class="hero-photo-wrapper">
                <div class="hero-photo-ring"></div>
                <div class="hero-photo">
                    <img src="{photo_url}" alt="{user.full_name}" onerror="this.src='../static/uploads/profile_photos/avatar.png'">
                </div>
            </div>
        </div>
    </section>
    
    <!-- Main Content + Sidebar -->
    <div class="main-container">
        <!-- Left Column -->
        <div class="main-content">
            {sections_html}
        </div>
        
        <!-- Right Sidebar -->
        <div class="sidebar">
            <!-- Profile Card -->
            <div class="sidebar-card">
                <img src="{photo_url}" alt="{user.full_name}" class="sidebar-avatar" onerror="this.src='../static/uploads/profile_photos/avatar.png'">
                <h3 class="sidebar-name">{user.full_name}</h3>
                <p class="sidebar-domain">{user.domain}</p>
                <div class="sidebar-info-item"><i class="fas fa-clock"></i> {user.experience_years or 'Fresher'}</div>
                <div class="sidebar-info-item"><i class="fas fa-map-marker-alt"></i> {user.city}, {user.state}</div>
                <div class="sidebar-info-item"><i class="fas fa-envelope"></i> {email_display}</div>
                <div class="sidebar-info-item"><i class="fas fa-phone"></i> {mobile_display}</div>
                {f'<div class="sidebar-info-item"><i class="fas fa-rupee-sign"></i> {user.expected_salary}</div>' if user.expected_salary else ''}
                {f'<div class="sidebar-info-item"><i class="fas fa-calendar-alt"></i> {user.notice_period}</div>' if user.notice_period else ''}
            </div>
            
            <!-- Quick Stats -->
            <div class="sidebar-card">
                <h4 style="font-weight:700;margin-bottom:12px;color:var(--dark);">
                    <i class="fas fa-chart-bar me-2" style="color:var(--primary);"></i>Quick Stats
                </h4>
                <div class="sidebar-info-item"><i class="fas fa-tools"></i> <strong>{len(skills)}</strong> Skills</div>
                <div class="sidebar-info-item"><i class="fas fa-briefcase"></i> <strong>{len(experience)}</strong> Experiences</div>
                <div class="sidebar-info-item"><i class="fas fa-graduation-cap"></i> <strong>{len(education)}</strong> Education</div>
                <div class="sidebar-info-item"><i class="fas fa-project-diagram"></i> <strong>{len(projects)}</strong> Projects</div>
                <div class="sidebar-info-item"><i class="fas fa-certificate"></i> <strong>{len(certifications)}</strong> Certifications</div>
            </div>
            
            <!-- Social Links -->
            {f'''<div class="sidebar-card">
                <h4 style="font-weight:700;margin-bottom:12px;color:var(--dark);">
                    <i class="fas fa-link me-2" style="color:var(--primary);"></i>Connect
                </h4>
                <div class="social-links">{social_links}</div>
            </div>''' if social_links else ''}
        </div>
    </div>
    
    <!-- Contact Section -->
    <section id="contact" style="max-width:1200px;margin:0 auto;padding:0 24px;">
        <div class="contact-section">
            <h2>Get In Touch</h2>
            <p>Interested in collaborating? Feel free to reach out!</p>
            <div class="contact-buttons">
                <a href="{email_link}" class="contact-btn contact-btn-email">
                    <i class="fas fa-envelope"></i> {email_display}
                </a>
                <a href="{mobile_link}" class="contact-btn contact-btn-phone">
                    <i class="fas fa-phone"></i> {mobile_display}
                </a>
            </div>
            {f'<div class="social-links" style="margin-top:20px;">{social_links}</div>' if social_links else ''}
        </div>
    </section>
    
    <!-- Footer -->
    <footer class="footer">
        <p>&copy; {datetime.now().year} {user.full_name} | Powered by <strong>Here I am</strong></p>
    </footer>
    
    <script>
        // Navbar scroll effect
        window.addEventListener('scroll', function() {{
            document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 50);
        }});
        
        // Smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }});
        }});
    </script>
</body>
</html>'''
    
    return html


def build_social_links(user):
    """Build social links HTML"""
    links = ''
    if user.linkedin:
        links += f'<a href="{user.linkedin}" target="_blank" class="social-link linkedin" title="LinkedIn"><i class="fab fa-linkedin-in"></i></a>'
    if user.github:
        links += f'<a href="{user.github}" target="_blank" class="social-link github" title="GitHub"><i class="fab fa-github"></i></a>'
    if user.portfolio:
        links += f'<a href="{user.portfolio}" target="_blank" class="social-link website" title="Website"><i class="fas fa-globe"></i></a>'
    return links


def build_all_sections(user, skills, education, experience, projects, certifications, languages, achievements):
    """Build all content sections"""
    html = ''
    
    # About Section
    if user.summary:
        html += f'''
        <section class="section-card" id="about">
            <h2 class="section-title"><i class="fas fa-user"></i> About Me</h2>
            <div class="section-subtitle">{user.summary}</div>
        </section>'''
    
    # Skills Section
    if skills:
        mid = len(skills) // 2
        expert_skills = skills[:3]  # First 3 as expert
        advanced_skills = skills[3:6]  # Next 3 as advanced
        rest_skills = skills[6:] if len(skills) > 6 else []
        
        skills_html = ''
        for skill in expert_skills:
            skills_html += f'<span class="skill-item skill-level-expert"><i class="fas fa-star"></i> {skill}</span>'
        for skill in advanced_skills:
            skills_html += f'<span class="skill-item skill-level-advanced"><i class="fas fa-check-circle"></i> {skill}</span>'
        for skill in rest_skills:
            skills_html += f'<span class="skill-item">{skill}</span>'
        
html += f'''
        <section class="section-card" id="skills">
            <h2 class="section-title"><i class="fas fa-cogs"></i> Skills & Expertise</h2>
            <div class="skills-container">{skills_html}</div>
            <div style="margin-top:16px; display:flex; gap:16px; font-size:0.75rem; color:var(--secondary);">
                <span><span class="skill-item skill-level-expert" style="font-size:0.7rem; padding:4px 10px;"><i class="fas fa-star"></i></span> Expert</span>
                <span><span class="skill-item skill-level-advanced" style="font-size:0.7rem; padding:4px 10px;"><i class="fas fa-check-circle"></i></span> Advanced</span>
            </div>
        </section>'''
    
    # Experience Section
    if experience:
        exp_html = ''
        for i, exp in enumerate(experience):
            is_current = 'present' in exp.get('duration', '').lower()
            exp_html += f'''
            <div class="timeline-item">
                <div class="timeline-dot{' current' if is_current else ''}"></div>
                <div class="timeline-header">
                    <div>
                        <div class="timeline-title">{exp.get('title', '')}</div>
                        <div class="timeline-company">{exp.get('company', '')}</div>
                    </div>
                    <span class="timeline-duration{' current-duration' if is_current else ''}">{exp.get('duration', '')}</span>
                </div>
                <p class="timeline-description">{exp.get('description', '')}</p>
            </div>'''
        
        html += f'''
        <section class="section-card" id="experience">
            <h2 class="section-title"><i class="fas fa-briefcase"></i> Work Experience</h2>
            <div class="timeline">{exp_html}</div>
        </section>'''
    
    # Education Section
    if education:
        edu_html = ''
        for edu in education:
            edu_html += f'''
            <div class="education-item">
                <div class="education-icon"><i class="fas fa-graduation-cap"></i></div>
                <div class="education-info">
                    <div class="education-degree">{edu.get('degree', '')}</div>
                    <div class="education-institution">{edu.get('institution', '')}</div>
                    <span class="education-year">{edu.get('year', '')}</span>
                </div>
            </div>'''
        
        html += f'''
        <section class="section-card" id="education">
            <h2 class="section-title"><i class="fas fa-graduation-cap"></i> Education</h2>
            {edu_html}
        </section>'''
    
    # Projects Section
    if projects:
        proj_html = ''
        for proj in projects:
            tech_tags = ''
            if proj.get('technologies'):
                for tech in proj['technologies'].split(',')[:4]:
                    tech_tags += f'<span class="project-tech-tag">{tech.strip()}</span>'
            
            proj_html += f'''
            <div class="project-card">
                <div class="project-card-header">
                    <div class="project-icon"><i class="fas fa-code"></i></div>
                    <div class="project-name">{proj.get('name', '')}</div>
                </div>
                <p class="project-desc">{proj.get('description', '')}</p>
                {f'<div class="project-tech">{tech_tags}</div>' if tech_tags else ''}
            </div>'''
        
        html += f'''
        <section class="section-card" id="projects">
            <h2 class="section-title"><i class="fas fa-project-diagram"></i> Projects</h2>
            <div class="projects-grid">{proj_html}</div>
        </section>'''
    
    # Certifications Section
    if certifications:
        cert_html = ''
        for cert in certifications:
            cert_html += f'<span class="cert-item"><i class="fas fa-certificate"></i> {cert}</span>'
        
        html += f'''
        <section class="section-card" id="certifications">
            <h2 class="section-title"><i class="fas fa-certificate"></i> Certifications</h2>
            <div class="cert-list">{cert_html}</div>
        </section>'''
    
    # Languages Section
    if languages:
        lang_html = ''
        for lang in languages:
            lang_html += f'<span class="lang-item"><i class="fas fa-language me-1"></i> {lang}</span>'
        
        html += f'''
        <section class="section-card" id="languages">
            <h2 class="section-title"><i class="fas fa-language"></i> Languages</h2>
            <div class="lang-list">{lang_html}</div>
        </section>'''
    
    # Achievements Section
    if achievements:
        ach_html = ''
        for ach in achievements:
            ach_html += f'<div class="achievement-item"><i class="fas fa-trophy"></i> <span>{ach}</span></div>'
        
        html += f'''
        <section class="section-card" id="achievements">
            <h2 class="section-title"><i class="fas fa-trophy"></i> Achievements & Awards</h2>
            {ach_html}
        </section>'''
    
    return html