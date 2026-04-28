# utils/profile_generator.py
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.helpers import safe_json_loads

def generate_profile_html(user, app):
    """Generate beautiful HTML profile page"""
    try:
        skills = safe_json_loads(user.skills)
        education = safe_json_loads(user.education)
        experience = safe_json_loads(user.experience)
        projects = safe_json_loads(user.projects)
        certifications = safe_json_loads(user.certifications)
        languages = safe_json_loads(user.languages)
        achievements = safe_json_loads(user.achievements)
        
        # Create safe filename
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
                    print(f"Deleted old profile: {user.profile_url}")
                except:
                    pass
        
        # Profile photo
        profile_photo_url = f"../static/{user.profile_photo}" if user.profile_photo else "../static/uploads/profile_photos/avatar.png"
        
        # Build all HTML components
        skills_html = build_skills_html(skills)
        experience_html = build_experience_html(experience)
        education_html = build_education_html(education)
        certifications_html = build_certifications_html(certifications)
        projects_html = build_projects_html(projects)
        languages_html = build_languages_html(languages)
        achievements_html = build_achievements_html(achievements)
        social_links_html = build_social_links(user)
        
        # Build complete HTML
        html_content = build_complete_html(
            user, profile_photo_url,
            skills_html, experience_html, education_html,
            certifications_html, projects_html,
            languages_html, achievements_html, social_links_html
        )
        
        # Save file
        os.makedirs(app.config['PROFILES_FOLDER'], exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Profile generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error generating profile: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# HTML BUILDERS
# ============================================================

def build_skills_html(skills):
    if not skills:
        return ''
    return ''.join([f'<span class="skill-badge">{s}</span>' for s in skills])

def build_experience_html(experience):
    if not experience:
        return ''
    html = ''
    for exp in experience:
        title = exp.get('title', '')
        company = exp.get('company', '')
        duration = exp.get('duration', '')
        description = exp.get('description', '')
        html += f'''
        <div class="experience-card">
            <div class="exp-header">
                <div>
                    <h3 class="exp-title">{title}</h3>
                    <p class="exp-company">{company}</p>
                </div>
                <span class="exp-duration">{duration}</span>
            </div>
            <p class="exp-description">{description}</p>
        </div>'''
    return html

def build_education_html(education):
    if not education:
        return ''
    html = ''
    for edu in education:
        degree = edu.get('degree', '')
        institution = edu.get('institution', '')
        year = edu.get('year', '')
        html += f'''
        <div class="education-card">
            <h3 class="edu-degree">{degree}</h3>
            <p class="edu-institution">{institution} | {year}</p>
        </div>'''
    return html

def build_certifications_html(certifications):
    if not certifications:
        return ''
    html = ''
    for cert in certifications:
        html += f'<div class="cert-item"><i class="fas fa-certificate"></i> {cert}</div>'
    return html

def build_projects_html(projects):
    if not projects:
        return ''
    html = ''
    for proj in projects:
        name = proj.get('name', '')
        description = proj.get('description', '')
        tech = proj.get('technologies', '')
        tech_html = f'<span class="project-tech"><i class="fas fa-code"></i> {tech}</span>' if tech else ''
        html += f'''
        <div class="project-card">
            <div class="project-icon"><i class="fas fa-folder-open"></i></div>
            <div class="project-info">
                <h3>{name}</h3>
                <p>{description}</p>
                {tech_html}
            </div>
        </div>'''
    return html

def build_languages_html(languages):
    if not languages:
        return ''
    return ''.join([f'<span class="lang-badge">{l}</span>' for l in languages])

def build_achievements_html(achievements):
    if not achievements:
        return ''
    html = ''
    for ach in achievements:
        html += f'<div class="achievement-item"><i class="fas fa-star"></i><span>{ach}</span></div>'
    return html

def build_social_links(user):
    links = ''
    if user.linkedin:
        links += f'<a href="{user.linkedin}" target="_blank" class="social-link linkedin"><i class="fab fa-linkedin-in"></i></a>'
    if user.github:
        links += f'<a href="{user.github}" target="_blank" class="social-link github"><i class="fab fa-github"></i></a>'
    if user.portfolio:
        links += f'<a href="{user.portfolio}" target="_blank" class="social-link website"><i class="fas fa-globe"></i></a>'
    
    if links:
        return f'<div class="social-links" style="justify-content:center;margin-top:24px;">{links}</div>'
    return ''


# ============================================================
# COMPLETE HTML BUILDER
# ============================================================

def build_complete_html(user, photo_url, skills_html, exp_html, edu_html, 
                        certs_html, proj_html, langs_html, ach_html, social_html):
    """Build the complete HTML document"""
    # ⭐ Privacy: Email और Mobile को mask करें या दिखाएं
    if user.show_email:
        email_display = user.email
    else:
        # Mask email: example@gmail.com → exa***@gmail.com
        parts = user.email.split('@')
        if len(parts) == 2:
            email_display = parts[0][:3] + '***@' + parts[1]
        else:
            email_display = 'Hidden'
    
    if user.show_mobile:
        mobile_display = user.mobile
    else:
        # Mask mobile: 9876543210 → 987****210
        if len(user.mobile) >= 10:
            mobile_display = user.mobile[:3] + '****' + user.mobile[-3:]
        else:
            mobile_display = 'Hidden'
    
    # Contact section
    contact_section = f'''
    <section class="section" id="contact">
        <div class="contact-card">
            <h2>Get In Touch</h2>
            <p>Feel free to reach out for collaborations or opportunities</p>
            <div class="contact-info">
                <div class="contact-item">
                    <i class="fas fa-envelope fa-lg"></i>
                    <a href="{'mailto:' + user.email if user.show_email else '#'}">{email_display}</a>
                    {'' if user.show_email else '<small style="opacity:0.7">(hidden by user)</small>'}
                </div>
                <div class="contact-item">
                    <i class="fas fa-phone fa-lg"></i>
                    <a href="{'tel:' + user.mobile if user.show_mobile else '#'}">{mobile_display}</a>
                    {'' if user.show_mobile else '<small style="opacity:0.7">(hidden by user)</small>'}
                </div>
            </div>
            {social_html}
        </div>
    </section>'''
    # Build sections
    sections = []
    
    # About section
    if user.summary:
        sections.append(f'''
        <section class="section section-alt" id="about">
            <h2 class="section-title">About Me</h2>
            <p>{user.summary}</p>
        </section>''')
    
    # Skills section
    if skills_html:
        sections.append(f'''
        <section class="section" id="skills">
            <h2 class="section-title">Key Skills</h2>
            <div>{skills_html}</div>
        </section>''')
    
    # Experience section
    if exp_html:
        sections.append(f'''
        <section class="section section-alt" id="experience">
            <h2 class="section-title">Professional Experience</h2>
            {exp_html}
        </section>''')
    
    # Education & Certifications section
    if edu_html or certs_html:
        edu_section = ''
        if edu_html:
            edu_section += edu_html
        if certs_html:
            edu_section += f'<h3 style="margin-top:30px;margin-bottom:16px;font-size:1.2rem;font-weight:700;">Certifications</h3><div class="certs-list">{certs_html}</div>'
        sections.append(f'''
        <section class="section" id="education">
            <h2 class="section-title">Education & Certifications</h2>
            {edu_section}
        </section>''')
    
    # Projects section
    if proj_html:
        sections.append(f'''
        <section class="section section-alt" id="projects">
            <h2 class="section-title">Projects</h2>
            <div class="projects-grid">{proj_html}</div>
        </section>''')
    
    # Languages section
    if langs_html:
        sections.append(f'''
        <section class="section" id="languages">
            <h2 class="section-title">Languages</h2>
            <div>{langs_html}</div>
        </section>''')
    
    # Achievements section
    if ach_html:
        sections.append(f'''
        <section class="section section-alt" id="achievements">
            <h2 class="section-title">Achievements</h2>
            {ach_html}
        </section>''')
    
    # Contact section (always shown)
    contact_section = f'''
    <section class="section" id="contact">
        <div class="contact-card">
            <h2>Get In Touch</h2>
            <p>Feel free to reach out for collaborations or opportunities</p>
            <div class="contact-info">
                <div class="contact-item">
                    <i class="fas fa-envelope fa-lg"></i>
                    <a href="mailto:{user.email}">{user.email}</a>
                </div>
                <div class="contact-item">
                    <i class="fas fa-phone fa-lg"></i>
                    <a href="tel:{user.mobile}">{user.mobile}</a>
                </div>
            </div>
            {social_html}
        </div>
    </section>'''
    
    sections.append(contact_section)
    
    all_sections = '\n'.join(sections)
    
    # Complete HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{user.full_name} - Professional Profile | Professionals Data Bank</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #2563eb; --primary-dark: #1d4ed8; --secondary: #64748b; --dark: #0f172a; --light: #f8fafc; --white: #ffffff; --accent: #3b82f6; --accent-light: #dbeafe; --success: #10b981; --warning: #f59e0b; --gradient-1: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); --gradient-2: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); --gradient-hero: linear-gradient(135deg, #eff6ff 0%, #dbeafe 50%, #bfdbfe 100%); --shadow-sm: 0 1px 2px rgba(0,0,0,0.05); --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1); --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1); --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1); --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-xl: 24px; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--light); color: var(--dark); line-height: 1.7; -webkit-font-smoothing: antialiased; }}
        .navbar {{ background: var(--white); box-shadow: var(--shadow-sm); position: sticky; top: 0; z-index: 1000; padding: 16px 0; border-bottom: 1px solid #e2e8f0; }}
        .nav-container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; }}
        .nav-logo {{ font-size: 1.25rem; font-weight: 700; color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: 8px; }}
        .hero {{ background: var(--gradient-hero); padding: 80px 0 60px; position: relative; overflow: hidden; }}
        .hero-container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 60px; position: relative; z-index: 1; }}
        .hero-content {{ flex: 1; }}
        .hero-title {{ font-family: 'Playfair Display', serif; font-size: 3.5rem; font-weight: 800; color: var(--dark); line-height: 1.15; margin-bottom: 12px; }}
        .hero-subtitle {{ font-size: 1.1rem; color: var(--secondary); margin-bottom: 24px; font-weight: 400; line-height: 1.6; }}
        .hero-tags {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 28px; }}
        .hero-tag {{ background: var(--white); color: var(--primary); padding: 8px 18px; border-radius: 50px; font-size: 0.85rem; font-weight: 600; box-shadow: var(--shadow-sm); border: 1px solid #e2e8f0; }}
        .hero-photo {{ flex-shrink: 0; width: 280px; height: 280px; border-radius: 50%; overflow: hidden; border: 6px solid var(--white); box-shadow: var(--shadow-xl); }}
        .hero-photo img {{ width: 100%; height: 100%; object-fit: cover; }}
        .section {{ padding: 70px 0; max-width: 1200px; margin: 0 auto; padding-left: 24px; padding-right: 24px; }}
        .section-alt {{ background: var(--white); max-width: 100%; padding-left: calc((100% - 1200px)/2 + 24px); padding-right: calc((100% - 1200px)/2 + 24px); }}
        .section-title {{ font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 700; color: var(--dark); margin-bottom: 40px; position: relative; padding-bottom: 16px; }}
        .section-title::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 60px; height: 3px; background: var(--gradient-1); border-radius: 3px; }}
        .skill-badge {{ display: inline-block; background: var(--accent-light); color: var(--primary-dark); padding: 10px 20px; border-radius: 50px; margin: 5px; font-size: 0.9rem; font-weight: 500; transition: all 0.3s; border: 1px solid transparent; }}
        .skill-badge:hover {{ background: var(--primary); color: var(--white); transform: translateY(-2px); box-shadow: var(--shadow-md); }}
        .experience-card {{ background: var(--white); border-radius: var(--radius-lg); padding: 28px; margin-bottom: 20px; box-shadow: var(--shadow-sm); border: 1px solid #e2e8f0; transition: all 0.3s; }}
        .experience-card:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-2px); }}
        .exp-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; flex-wrap: wrap; gap: 12px; }}
        .exp-title {{ font-size: 1.15rem; font-weight: 700; color: var(--dark); margin: 0; }}
        .exp-company {{ color: var(--primary); font-weight: 600; font-size: 0.95rem; margin: 4px 0 0; }}
        .exp-duration {{ background: var(--accent-light); color: var(--primary-dark); padding: 6px 14px; border-radius: 50px; font-size: 0.8rem; font-weight: 600; white-space: nowrap; }}
        .exp-description {{ color: var(--secondary); font-size: 0.9rem; margin: 0; line-height: 1.8; }}
        .education-card {{ background: var(--white); border-left: 4px solid var(--primary); padding: 20px 24px; margin-bottom: 16px; border-radius: 0 var(--radius-md) var(--radius-md) 0; box-shadow: var(--shadow-sm); }}
        .edu-degree {{ font-size: 1.05rem; font-weight: 700; color: var(--dark); margin: 0 0 4px; }}
        .edu-institution {{ color: var(--secondary); font-size: 0.9rem; margin: 0; }}
        .projects-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .project-card {{ background: var(--white); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-sm); border: 1px solid #e2e8f0; transition: all 0.3s; display: flex; gap: 16px; align-items: flex-start; }}
        .project-card:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-4px); border-color: var(--primary); }}
        .project-icon {{ width: 48px; height: 48px; background: var(--gradient-1); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem; flex-shrink: 0; }}
        .project-info h3 {{ font-size: 1rem; font-weight: 700; margin: 0 0 8px; }}
        .project-info p {{ color: var(--secondary); font-size: 0.85rem; margin: 0 0 8px; line-height: 1.6; }}
        .project-tech {{ font-size: 0.8rem; color: var(--primary); font-weight: 600; }}
        .certs-list {{ display: flex; flex-wrap: wrap; gap: 12px; }}
        .cert-item {{ background: var(--white); padding: 12px 20px; border-radius: var(--radius-md); font-weight: 500; box-shadow: var(--shadow-sm); border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 10px; }}
        .cert-item i {{ color: var(--warning); font-size: 1.1rem; }}
        .lang-badge {{ display: inline-block; background: var(--gradient-1); color: white; padding: 8px 18px; border-radius: 50px; margin: 5px; font-size: 0.85rem; font-weight: 500; }}
        .achievement-item {{ display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px; padding: 16px; background: var(--white); border-radius: var(--radius-md); box-shadow: var(--shadow-sm); }}
        .achievement-item i {{ color: var(--warning); font-size: 1.2rem; margin-top: 3px; flex-shrink: 0; }}
        .achievement-item span {{ color: var(--dark); font-weight: 500; }}
        .social-links {{ display: flex; gap: 12px; }}
        .social-link {{ width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: white; font-size: 1.1rem; transition: all 0.3s; text-decoration: none; }}
        .social-link:hover {{ transform: translateY(-4px); box-shadow: var(--shadow-lg); color: white; }}
        .social-link.linkedin {{ background: #0077b5; }}
        .social-link.github {{ background: #333; }}
        .social-link.website {{ background: var(--success); }}
        .contact-card {{ background: var(--gradient-2); color: white; border-radius: var(--radius-xl); padding: 50px; text-align: center; }}
        .contact-card h2 {{ font-family: 'Playfair Display', serif; font-size: 2rem; margin-bottom: 16px; }}
        .contact-info {{ display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 24px; }}
        .contact-item {{ display: flex; align-items: center; gap: 10px; font-size: 1rem; }}
        .contact-item i {{ opacity: 0.8; }}
        .contact-item a {{ color: white; text-decoration: none; }}
        .footer {{ text-align: center; padding: 30px; color: var(--secondary); font-size: 0.85rem; border-top: 1px solid #e2e8f0; }}
        .footer a {{ color: var(--primary); text-decoration: none; }}
        @media (max-width: 768px) {{
            .hero-container {{ flex-direction: column-reverse; text-align: center; gap: 30px; }}
            .hero-title {{ font-size: 2.2rem; }}
            .hero-photo {{ width: 180px; height: 180px; }}
            .hero-tags {{ justify-content: center; }}
            .section-title {{ font-size: 1.6rem; }}
            .section {{ padding: 40px 0; }}
            .exp-header {{ flex-direction: column; }}
            .contact-info {{ flex-direction: column; gap: 16px; align-items: center; }}
            .projects-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="#" class="nav-logo"><i class="fas fa-database"></i> Professionals Data Bank</a>
            <div class="nav-links">
                <a href="#about">About</a>
                <a href="#skills">Skills</a>
                <a href="#experience">Experience</a>
                <a href="#education">Education</a>
                <a href="#projects">Projects</a>
                <a href="#contact">Contact</a>
            </div>
        </div>
    </nav>
    
    <section class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <h1 class="hero-title">{user.full_name}</h1>
                <p class="hero-subtitle">{user.summary or ''}</p>
                <div class="hero-tags">
                    <span class="hero-tag"><i class="fas fa-briefcase"></i> {user.domain}</span>
                    <span class="hero-tag"><i class="fas fa-clock"></i> {user.experience_years or 'Fresher'}</span>
                    <span class="hero-tag"><i class="fas fa-map-marker-alt"></i> {user.city}, {user.state}</span>
                </div>
            </div>
            <div class="hero-photo">
                <img src="{photo_url}" alt="{user.full_name}" onerror="this.src='../static/uploads/profile_photos/avatar.png'">
            </div>
        </div>
    </section>
    
    {all_sections}
    
    <footer class="footer">
        <p>&copy; {datetime.now().year} {user.full_name} | Powered by <a href="#">Professionals Data Bank</a></p>
    </footer>
</body>
</html>'''
    
    return html