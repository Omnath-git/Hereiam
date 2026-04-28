# utils/cv_parser.py
import re
import json
from datetime import datetime
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def parse_cv(cv_text):
    """Advanced local CV parser - No API required"""
    if not cv_text or len(cv_text.strip()) < 50:
        return None
    
    lines = [l.strip() for l in cv_text.split('\n') if l.strip()]
    sections = split_cv_sections(cv_text, lines)
    
    return {
        "full_name": extract_name(lines, cv_text),
        "summary": extract_summary_text(sections, cv_text),
        "domain": extract_domain_text(sections, cv_text, lines),
        "skills": extract_skills_list(cv_text),
        "experience_years": extract_experience_years_text(cv_text),
        "education": extract_education_list(sections, cv_text),
        "experience": extract_experience_list(sections, cv_text),
        "projects": extract_projects_list(sections, cv_text),
        "certifications": extract_certifications_list(sections, cv_text),
        "languages": extract_languages_list(cv_text),
        "achievements": extract_achievements_list(sections, cv_text),
        "linkedin": extract_linkedin_url(cv_text),
        "github": extract_github_url(cv_text),
        "portfolio": extract_portfolio_url(cv_text),
        "city": extract_city_state(cv_text)[0],
        "state": extract_city_state(cv_text)[1]
    }

def split_cv_sections(text, lines):
    """Split CV into logical sections"""
    sections = {}
    current_section = "header"
    section_content = []
    
    section_keywords = {
        'summary': ['summary', 'profile', 'objective', 'about me'],
        'experience': ['experience', 'work experience', 'employment'],
        'education': ['education', 'academic', 'qualification'],
        'skills': ['skills', 'technical skills', 'expertise'],
        'projects': ['projects', 'project experience'],
        'certifications': ['certifications', 'certificates'],
        'achievements': ['achievements', 'awards'],
        'languages': ['languages', 'language proficiency'],
    }
    
    for line in lines:
        line_lower = line.lower().strip()
        is_header = False
        
        for section_name, keywords in section_keywords.items():
            for keyword in keywords:
                if line_lower == keyword or line_lower.startswith(keyword + ':') or line_lower.startswith(keyword + ' '):
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                    current_section = section_name
                    section_content = []
                    is_header = True
                    break
                elif len(line) < 40 and keyword in line_lower and not any(c.isdigit() for c in line):
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                    current_section = section_name
                    section_content = []
                    is_header = True
                    break
            if is_header:
                break
        
        if not is_header:
            section_content.append(line)
    
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content)
    
    if 'header' in sections and 'summary' not in sections:
        sections['summary'] = sections.get('header', '')
    
    return sections

def extract_name(lines, text):
    """Extract full name from CV"""
    for line in lines[:8]:
        line = line.strip()
        if re.search(r'[@:\/\d]', line):
            continue
        if re.search(r'(curriculum|resume|cv|profile|summary|experience|education|skills|contact)', line, re.IGNORECASE):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            capital_words = [w for w in words if w[0].isupper()]
            if len(capital_words) >= 2 and len(line) < 60:
                return line
    return "Professional"

def extract_summary_text(sections, text):
    """Extract professional summary"""
    if 'summary' in sections:
        summary = sections['summary']
        paragraphs = [p.strip() for p in summary.split('\n') if p.strip()]
        for para in paragraphs:
            if len(para) > 80:
                return para[:600]
        return paragraphs[0][:500] if paragraphs else ""
    
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    for para in paragraphs[:5]:
        if 80 < len(para) < 600 and not re.search(r'[@:]', para):
            return para[:500]
    return ""

def extract_domain_text(sections, text, lines):
    """Extract professional domain"""
    domains = [
        "Software Developer", "Software Engineer", "Full Stack Developer",
        "Frontend Developer", "Backend Developer", "Web Developer",
        "DevOps Engineer", "Data Scientist", "Data Analyst",
        "Machine Learning Engineer", "AI Engineer", "Cloud Architect",
        "Cybersecurity Analyst", "Mobile App Developer", "UI/UX Designer",
        "Product Manager", "Project Manager", "Business Analyst",
        "QA Engineer", "Technical Lead"
    ]
    
    first_text = text[:1500].lower()
    for domain in domains:
        if domain.lower() in first_text:
            return domain
    
    if 'experience' in sections:
        exp_lower = sections['experience'].lower()
        for domain in domains:
            if domain.lower() in exp_lower:
                return domain
    
    return "Software Developer"

def extract_skills_list(text):
    """Extract skills"""
    all_skills = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', '.NET',
        'Ruby', 'Go', 'Rust', 'PHP', 'Swift', 'Kotlin', 'React', 'Angular',
        'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot', 'Express.js',
        'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Docker', 'Kubernetes',
        'AWS', 'Azure', 'GCP', 'Git', 'Linux', 'Machine Learning', 'Deep Learning',
        'TensorFlow', 'PyTorch', 'Data Science', 'Agile', 'Scrum', 'CI/CD',
        'REST API', 'GraphQL', 'HTML', 'CSS', 'Bootstrap', 'Tailwind CSS',
        'React Native', 'Flutter', 'Tableau', 'Power BI', 'Figma', 'JIRA'
    ]
    
    found = []
    for skill in all_skills:
        skill_pattern = re.escape(skill).replace(r'\.', r'\.?')
        if re.search(r'\b' + skill_pattern + r'\b', text, re.IGNORECASE):
            if skill not in found:
                found.append(skill)
    
    return found[:20]

def extract_experience_years_text(text):
    """Extract experience years"""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
        r'experience\s*(?:of)?\s*(\d+)\+?\s*years?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}+ years"
    
    dates = re.findall(r'(20\d{2})\s*[-–to]+\s*(20\d{2}|[Pp]resent|[Cc]urrent|[Nn]ow)', text)
    if dates:
        total = 0
        for start, end in dates:
            s = int(start)
            e = 2024 if end.lower() in ['present', 'current', 'now'] else int(end)
            total += max(0, e - s)
        if total > 0:
            return f"{total}+ years"
    
    return "Fresher"

def extract_education_list(sections, text):
    """Extract education"""
    education = []
    edu_text = sections.get('education', text)
    degree_pattern = r'(B\.?Tech|B\.?E|B\.?Sc|B\.?A|M\.?Tech|M\.?E|M\.?Sc|MCA|MBA|PhD|Diploma)[^,\n]{0,80}'
    matches = re.findall(degree_pattern, edu_text, re.IGNORECASE)
    for match in matches[:4]:
        degree = match.strip()
        if len(degree) > 5:
            education.append({"degree": degree[:100], "institution": "Not specified", "year": ""})
    return education

def extract_experience_list(sections, text):
    """Extract work experience"""
    experience = []
    exp_text = sections.get('experience', '')
    if not exp_text:
        return experience
    
    entries = re.split(r'\n\s*\n', exp_text)
    for entry in entries[:5]:
        lines = entry.strip().split('\n')
        if not lines or len(lines[0]) < 10:
            continue
        title = lines[0].strip()[:100]
        company = lines[1].strip()[:100] if len(lines) > 1 else ""
        duration = ""
        description = ""
        dur_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*?\d{4})\s*[-–to]+\s*(.*?\d{4}|[Pp]resent)', entry)
        if dur_match:
            duration = dur_match.group()
        desc_lines = [l.strip() for l in lines[2:5] if len(l.strip()) > 20]
        if desc_lines:
            description = ' '.join(desc_lines)[:300]
        experience.append({"title": title, "company": company or "Not specified", "duration": duration, "description": description})
    return experience

def extract_projects_list(sections, text):
    """Extract projects"""
    projects = []
    proj_text = sections.get('projects', '')
    if not proj_text:
        return projects
    entries = re.split(r'\n\s*\n', proj_text)
    for entry in entries[:4]:
        lines = entry.strip().split('\n')
        if not lines:
            continue
        name = lines[0].strip()[:100]
        description = ' '.join([l.strip() for l in lines[1:3] if l.strip()])[:300]
        tech_match = re.search(r'(?:technolog|tech|tools?|built with|using)\s*:?\s*([^.\n]{0,100})', entry, re.IGNORECASE)
        technologies = tech_match.group(1).strip() if tech_match else ""
        if name and len(name) > 5:
            projects.append({"name": name, "description": description, "technologies": technologies})
    return projects

def extract_certifications_list(sections, text):
    """Extract certifications"""
    certs = []
    cert_text = sections.get('certifications', '')
    if cert_text:
        lines = cert_text.split('\n')
        for line in lines:
            line = re.sub(r'^[\s•\-\*\d\.]+\s*', '', line).strip()
            if line and len(line) > 5:
                certs.append(line[:150])
    common = ["AWS Certified", "Microsoft Certified", "Google Cloud", "PMP", "Scrum Master", "CISSP", "CEH"]
    for c in common:
        match = re.search(r'\b' + re.escape(c) + r'[^.\n]{0,80}', text, re.IGNORECASE)
        if match and match.group().strip() not in certs:
            certs.append(match.group().strip())
    return certs[:6]

def extract_languages_list(text):
    """Extract languages"""
    languages = []
    common_langs = ["English", "Hindi", "Marathi", "Gujarati", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Punjabi", "Spanish", "French", "German"]
    for lang in common_langs:
        if re.search(r'\b' + re.escape(lang) + r'\b', text, re.IGNORECASE):
            languages.append(lang)
    return languages if languages else ["English"]

def extract_achievements_list(sections, text):
    """Extract achievements"""
    achievements = []
    ach_text = sections.get('achievements', '')
    if ach_text:
        lines = ach_text.split('\n')
        for line in lines:
            line = re.sub(r'^[\s•\-\*\d\.]+\s*', '', line).strip()
            if line and len(line) > 10:
                achievements.append(line[:200])
    return achievements[:5]

def extract_linkedin_url(text):
    match = re.search(r'(?:linkedin\.com/in/|linkedin\.com/)[\w\-]+', text, re.IGNORECASE)
    if match:
        url = match.group()
        return 'https://www.' + url if not url.startswith('http') else url
    return ""

def extract_github_url(text):
    match = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
    if match:
        url = match.group()
        return 'https://' + url if not url.startswith('http') else url
    return ""

def extract_portfolio_url(text):
    patterns = [r'(?:portfolio|website|web|site)\s*:?\s*(https?://[^\s]+)', r'https?://(?!linkedin|github)[^\s]+\.[a-z]{2,}[^\s]*']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(1) if match.lastindex else match.group()
            if 'linkedin' not in url.lower() and 'github' not in url.lower():
                return url
    return ""

def extract_city_state(text):
    city_state_map = {
        "Mumbai": "Maharashtra", "Delhi": "Delhi", "Bangalore": "Karnataka",
        "Hyderabad": "Telangana", "Chennai": "Tamil Nadu", "Pune": "Maharashtra",
        "Kolkata": "West Bengal", "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan",
        "Lucknow": "Uttar Pradesh", "Noida": "Uttar Pradesh", "Gurgaon": "Haryana",
        "Indore": "Madhya Pradesh", "Kochi": "Kerala", "Patna": "Bihar"
    }
    for city, state in city_state_map.items():
        if re.search(r'\b' + re.escape(city) + r'\b', text, re.IGNORECASE):
            return city, state
    return "Mumbai", "Maharashtra"