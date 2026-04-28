"""
=============================================================================
Professionals Data Bank - Bulk Professional Data Seeder
=============================================================================
हर डोमेन के 50 प्रोफेशनल्स बनाता है और उनके प्रोफाइल HTML पेज जनरेट करता है
=============================================================================
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User
from utils.profile_generator import generate_profile_html

# ============================================================
# DOMAINS & DATA
# ============================================================

# 20 अलग-अलग डोमेन
DOMAINS = [
    "Software Developer", "Full Stack Developer", "Frontend Developer",
    "Backend Developer", "DevOps Engineer", "Data Scientist",
    "Machine Learning Engineer", "AI Engineer", "Cloud Architect",
    "Cybersecurity Analyst", "Mobile App Developer", "UI/UX Designer",
    "Product Manager", "Project Manager", "Business Analyst",
    "Database Administrator", "Network Engineer", "QA Engineer",
    "Technical Lead", "System Administrator"
]

# भारतीय शहर और राज्य
CITIES_STATES = {
    "Mumbai": "Maharashtra", "Bangalore": "Karnataka",
    "Hyderabad": "Telangana", "Chennai": "Tamil Nadu",
    "Pune": "Maharashtra", "Delhi": "Delhi",
    "Kolkata": "West Bengal", "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan", "Lucknow": "Uttar Pradesh",
    "Noida": "Uttar Pradesh", "Gurgaon": "Haryana",
    "Indore": "Madhya Pradesh", "Kochi": "Kerala",
    "Coimbatore": "Tamil Nadu", "Chandigarh": "Punjab",
    "Nagpur": "Maharashtra", "Surat": "Gujarat",
    "Bhubaneswar": "Odisha", "Patna": "Bihar",
    "Visakhapatnam": "Andhra Pradesh", "Bhopal": "Madhya Pradesh",
    "Vadodara": "Gujarat", "Ludhiana": "Punjab",
    "Agra": "Uttar Pradesh", "Nashik": "Maharashtra",
    "Ranchi": "Jharkhand", "Guwahati": "Assam",
    "Dehradun": "Uttarakhand", "Thiruvananthapuram": "Kerala"
}

# भारतीय नाम
FIRST_NAMES_MALE = [
    "Aarav", "Vihaan", "Advik", "Kabir", "Reyansh", "Arjun", "Ishaan", "Rudra",
    "Ayaan", "Shaurya", "Dhruv", "Krishna", "Atharv", "Ved", "Rohan", "Siddharth",
    "Karan", "Rahul", "Amit", "Suresh", "Rajesh", "Deepak", "Vikram", "Sanjay",
    "Aditya", "Nitin", "Abhishek", "Manish", "Akash", "Ankit", "Vivek", "Pankaj",
    "Gaurav", "Sachin", "Naveen", "Tarun", "Harsh", "Kunal", "Sahil", "Mohit",
    "Prateek", "Yash", "Rishi", "Nikhil", "Pranav", "Shubham", "Tushar", "Varun"
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Pari", "Myra", "Kiara", "Anvi", "Prisha", "Shreya",
    "Neha", "Pooja", "Priya", "Meera", "Ritu", "Kavya", "Nisha", "Sunita",
    "Geeta", "Aaradhya", "Anaya", "Sai", "Ishita", "Aanya", "Sanya", "Tara",
    "Aditi", "Riya", "Jiya", "Khushi", "Palak", "Mansi", "Shruti", "Nikita",
    "Bhavna", "Shikha", "Rashmi", "Preeti", "Anjali", "Divya", "Richa", "Sneha",
    "Pallavi", "Monika", "Deepika", "Sapna", "Rekha", "Komal", "Swati", "Shivani"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Kumar", "Singh", "Gupta", "Joshi", "Mehta",
    "Shah", "Reddy", "Nair", "Menon", "Das", "Rao", "Malhotra", "Kapoor",
    "Chopra", "Saxena", "Srivastava", "Mishra", "Pandey", "Tiwari", "Dubey",
    "Thakur", "Yadav", "Jain", "Agarwal", "Sinha", "Prasad", "Chauhan",
    "Rawat", "Negi", "Rana", "Bisht", "Kashyap", "Bhatt", "Desai", "Kulkarni",
    "Patil", "Naik", "Shetty", "Hegde", "Pillai", "Iyer", "Choudhury", "Sen"
]

# डोमेन के अनुसार स्किल्स
DOMAIN_SKILLS = {
    "Software Developer": ["Python", "Java", "C++", "Git", "SQL", "Agile", "OOP", "Data Structures", "Algorithms", "REST API"],
    "Full Stack Developer": ["React", "Node.js", "MongoDB", "JavaScript", "TypeScript", "HTML", "CSS", "Docker", "AWS", "GraphQL"],
    "Frontend Developer": ["React", "JavaScript", "TypeScript", "HTML5", "CSS3", "Redux", "Tailwind", "Bootstrap", "Webpack", "Figma"],
    "Backend Developer": ["Python", "Django", "Flask", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Microservices", "CI/CD"],
    "DevOps Engineer": ["Docker", "Kubernetes", "Jenkins", "AWS", "Terraform", "Ansible", "Linux", "CI/CD", "Prometheus", "Bash"],
    "Data Scientist": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "SQL", "Statistics", "Pandas", "NumPy", "Tableau", "NLP"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "Deep Learning", "Computer Vision", "NLP", "MLOps", "Kubernetes", "AWS", "SQL"],
    "AI Engineer": ["Python", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "LLM", "RAG", "Vector DB", "MLOps"],
    "Cloud Architect": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Docker", "Microservices", "Security", "Networking", "CI/CD"],
    "Cybersecurity Analyst": ["Network Security", "Ethical Hacking", "SIEM", "Firewall", "Penetration Testing", "Python", "Linux", "Risk Assessment", "Compliance", "Incident Response"],
    "Mobile App Developer": ["React Native", "Flutter", "Swift", "Kotlin", "Android", "iOS", "Firebase", "REST API", "Git", "UI/UX"],
    "UI/UX Designer": ["Figma", "Adobe XD", "Sketch", "User Research", "Wireframing", "Prototyping", "HTML", "CSS", "Design Systems", "Usability Testing"],
    "Product Manager": ["Product Strategy", "Roadmapping", "JIRA", "Agile", "User Stories", "Market Research", "Data Analysis", "Stakeholder Management", "A/B Testing", "SQL"],
    "Project Manager": ["Project Planning", "Scrum", "JIRA", "Risk Management", "Budgeting", "Team Leadership", "Stakeholder Communication", "Agile", "MS Project", "Reporting"],
    "Business Analyst": ["Requirements Gathering", "Process Modeling", "SQL", "Excel", "Tableau", "JIRA", "Agile", "Stakeholder Management", "Documentation", "Data Analysis"],
    "Database Administrator": ["PostgreSQL", "MySQL", "Oracle", "MongoDB", "Performance Tuning", "Backup Recovery", "SQL", "Linux", "Shell Scripting", "Monitoring"],
    "Network Engineer": ["Cisco", "Routing", "Switching", "Firewall", "VPN", "LAN/WAN", "TCP/IP", "Network Security", "Troubleshooting", "Monitoring"],
    "QA Engineer": ["Selenium", "Manual Testing", "Automation", "JIRA", "Test Cases", "Regression Testing", "API Testing", "Python", "CI/CD", "Bug Tracking"],
    "Technical Lead": ["Python", "Java", "System Design", "Microservices", "Cloud", "Team Mentoring", "Code Review", "Agile", "Architecture", "DevOps"],
    "System Administrator": ["Linux", "Windows Server", "Active Directory", "VMware", "Shell Scripting", "Networking", "Backup", "Monitoring", "Security", "Troubleshooting"]
}

# अनुभव के स्तर
EXPERIENCE_LEVELS = ["1+ years", "2+ years", "3+ years", "5+ years", "8+ years", "10+ years", "12+ years", "15+ years"]

# सैलरी रेंज
SALARY_RANGES = ["3-6 LPA", "6-10 LPA", "10-15 LPA", "15-25 LPA", "25-50 LPA", "50+ LPA", "Negotiable"]

# नोटिस पीरियड
NOTICE_PERIODS = ["Immediate", "15 Days", "30 Days", "60 Days", "90 Days"]

# कंपनियां
COMPANIES = [
    "TCS", "Infosys", "Wipro", "HCL", "Tech Mahindra", "Cognizant", "Accenture",
    "IBM", "Microsoft", "Google", "Amazon", "Flipkart", "Paytm", "Zomato",
    "Swiggy", "Ola", "PhonePe", "Razorpay", "Freshworks", "Zerodha",
    "Oracle", "SAP", "Salesforce", "Adobe", "VMware", "Dell", "Cisco",
    "Intel", "Samsung", "Qualcomm", "Uber", "Ola Electric", "Dream11",
    "Byju's", "Unacademy", "UpGrad", "Cred", "Groww", "BharatPe"
]

# एजुकेशन
EDUCATIONS = [
    [{"degree": "B.Tech in Computer Science", "institution": "IIT Bombay", "year": "2018"}],
    [{"degree": "B.Tech in IT", "institution": "IIT Delhi", "year": "2019"}],
    [{"degree": "B.Tech in Computer Science", "institution": "NIT Trichy", "year": "2017"}],
    [{"degree": "B.Tech in Electronics", "institution": "NIT Surathkal", "year": "2020"}],
    [{"degree": "BCA", "institution": "Delhi University", "year": "2018"}, {"degree": "MCA", "institution": "IGNOU", "year": "2021"}],
    [{"degree": "B.Sc Computer Science", "institution": "Mumbai University", "year": "2019"}, {"degree": "M.Sc Data Science", "institution": "Pune University", "year": "2022"}],
    [{"degree": "B.Tech in CSE", "institution": "BITS Pilani", "year": "2018"}, {"degree": "M.Tech in AI", "institution": "IISc Bangalore", "year": "2021"}],
    [{"degree": "B.E. in IT", "institution": "VIT Vellore", "year": "2019"}],
    [{"degree": "B.Tech", "institution": "SRM University", "year": "2020"}],
    [{"degree": "BCA", "institution": "Christ University", "year": "2018"}, {"degree": "MBA", "institution": "Symbiosis", "year": "2021"}],
]

# सर्टिफिकेशन
CERTIFICATIONS_POOL = [
    ["AWS Certified Solutions Architect", "Scrum Master"],
    ["Google Cloud Professional", "Kubernetes Administrator"],
    ["Microsoft Azure Administrator", "PMP"],
    ["Certified Scrum Master", "AWS Developer"],
    ["Oracle Certified Professional", "CISSP"],
    ["CEH", "CompTIA Security+"],
    ["AWS DevOps Engineer", "Docker Certified"],
    ["Google Data Engineer", "TensorFlow Developer"],
    ["ISTQB", "Selenium Certified"],
    ["Cisco CCNA", "Red Hat Certified"],
]

# लैंग्वेज
LANGUAGES_POOL = [
    ["English", "Hindi"],
    ["English", "Hindi", "Marathi"],
    ["English", "Hindi", "Gujarati"],
    ["English", "Hindi", "Tamil"],
    ["English", "Hindi", "Telugu"],
    ["English", "Hindi", "Kannada"],
    ["English", "Hindi", "Malayalam"],
    ["English", "Hindi", "Bengali"],
    ["English", "Hindi", "Punjabi"],
    ["English", "Hindi", "Odia"],
]

# ============================================================
# JOB EXPERIENCE BUILDER
# ============================================================

def build_experience(domain, city):
    """Build realistic experience for a domain"""
    experiences = []
    num_jobs = random.randint(2, 4)
    
    for i in range(num_jobs):
        company = random.choice(COMPANIES)
        duration_years = random.randint(1, 4)
        start_year = 2024 - (num_jobs - i) * duration_years
        end_year = start_year + duration_years
        
        if i == num_jobs - 1:
            duration = f"{start_year} - Present"
        else:
            duration = f"{start_year} - {end_year}"
        
        titles = {
            "Software Developer": ["Junior Developer", "Software Developer", "Senior Developer", "Lead Developer"],
            "Full Stack Developer": ["Frontend Developer", "Full Stack Developer", "Senior Full Stack Developer", "Tech Lead"],
            "Frontend Developer": ["Junior Frontend Dev", "Frontend Developer", "Senior Frontend Dev", "UI Lead"],
            "Backend Developer": ["Backend Developer", "Senior Backend Dev", "Backend Lead", "Solutions Architect"],
            "DevOps Engineer": ["Junior DevOps", "DevOps Engineer", "Senior DevOps", "DevOps Lead"],
            "Data Scientist": ["Data Analyst", "Data Scientist", "Senior Data Scientist", "Lead Data Scientist"],
            "Machine Learning Engineer": ["ML Engineer", "Senior ML Engineer", "ML Lead", "AI Architect"],
            "AI Engineer": ["AI Developer", "AI Engineer", "Senior AI Engineer", "AI Lead"],
            "Cloud Architect": ["Cloud Engineer", "Cloud Architect", "Senior Cloud Architect", "Principal Architect"],
            "Cybersecurity Analyst": ["Security Analyst", "Cybersecurity Analyst", "Senior Security Analyst", "Security Lead"],
            "Mobile App Developer": ["App Developer", "Mobile Developer", "Senior Mobile Dev", "Mobile Lead"],
            "UI/UX Designer": ["UI Designer", "UX Designer", "Senior UX Designer", "Design Lead"],
            "Product Manager": ["Associate PM", "Product Manager", "Senior PM", "Director of Product"],
            "Project Manager": ["Project Coordinator", "Project Manager", "Senior PM", "Program Manager"],
            "Business Analyst": ["Junior BA", "Business Analyst", "Senior BA", "Lead BA"],
            "Database Administrator": ["Junior DBA", "Database Admin", "Senior DBA", "Database Architect"],
            "Network Engineer": ["Network Admin", "Network Engineer", "Senior Network Eng", "Network Architect"],
            "QA Engineer": ["QA Tester", "QA Engineer", "Senior QA", "QA Lead"],
            "Technical Lead": ["Software Engineer", "Senior Developer", "Technical Lead", "Engineering Manager"],
            "System Administrator": ["System Admin", "Senior Sys Admin", "IT Manager", "Infrastructure Lead"],
        }
        
        title_list = titles.get(domain, ["Developer", "Senior Developer", "Lead Developer", "Manager"])
        title = title_list[min(i, len(title_list)-1)]
        
        descriptions = [
            f"Led development of key features and mentored junior developers at {company}.",
            f"Designed and implemented scalable solutions improving system performance by {random.randint(30, 80)}%.",
            f"Managed cross-functional team of {random.randint(5, 20)} members for critical projects.",
            f"Reduced deployment time by {random.randint(40, 70)}% through automation and CI/CD implementation.",
            f"Implemented best practices resulting in {random.randint(20, 50)}% reduction in bugs.",
        ]
        
        experiences.append({
            "title": title,
            "company": company,
            "duration": duration,
            "description": random.choice(descriptions)
        })
    
    return experiences

def build_projects(domain):
    """Build sample projects"""
    projects = []
    num = random.randint(1, 3)
    project_names = {
        "Software Developer": ["E-commerce Platform", "Task Management System", "API Gateway"],
        "Full Stack Developer": ["Social Media Dashboard", "Real-time Chat App", "Blog Platform"],
        "Frontend Developer": ["Portfolio Website", "Admin Dashboard", "Landing Page Builder"],
        "Backend Developer": ["Microservices Framework", "Payment Gateway", "Data Pipeline"],
        "Data Scientist": ["Customer Segmentation", "Sales Forecasting", "Recommendation Engine"],
        "Mobile App Developer": ["Food Delivery App", "Fitness Tracker", "Expense Manager"],
        "UI/UX Designer": ["Banking App Redesign", "E-learning Platform", "Healthcare Portal"],
    }
    names = project_names.get(domain, ["Enterprise Application", "Automation Tool", "Analytics Dashboard"])
    
    techs = random.sample(DOMAIN_SKILLS.get(domain, ["Python", "SQL"]), 3)
    
    for i in range(num):
        projects.append({
            "name": random.choice(names),
            "description": f"Built {random.choice(names).lower()} with modern technologies and best practices.",
            "technologies": ", ".join(techs)
        })
    
    return projects


# ============================================================
# MAIN SEEDER FUNCTION
# ============================================================

def seed_professionals(professionals_per_domain=50):
    """Seed professionals for each domain"""
    
    app = create_app()
    
    with app.app_context():
        total_created = 0
        total_profiles_generated = 0
        
        print("\n" + "="*70)
        print(f"🚀 PROFESSIONALS DATA BANK - BULK SEEDER")
        print(f"📋 Domains: {len(DOMAINS)}")
        print(f"👤 Professionals per domain: {professionals_per_domain}")
        print(f"📊 Total to create: {len(DOMAINS) * professionals_per_domain}")
        print("="*70)
        
        for domain in DOMAINS:
            print(f"\n📂 Processing: {domain}")
            domain_count = 0
            
            for i in range(professionals_per_domain):
                try:
                    # Random gender
                    if random.random() > 0.5:
                        first_name = random.choice(FIRST_NAMES_MALE)
                    else:
                        first_name = random.choice(FIRST_NAMES_FEMALE)
                    
                    last_name = random.choice(LAST_NAMES)
                    full_name = f"{first_name} {last_name}"
                    
                    # Check if user already exists
                    existing = User.query.filter_by(full_name=full_name).first()
                    if existing:
                        continue
                    
                    # Random city/state
                    city = random.choice(list(CITIES_STATES.keys()))
                    state = CITIES_STATES[city]
                    
                    # Random attributes
                    skills = random.sample(DOMAIN_SKILLS.get(domain, ["Python", "SQL", "Git"]), 
                                           random.randint(5, 8))
                    experience_years = random.choice(EXPERIENCE_LEVELS)
                    salary = random.choice(SALARY_RANGES)
                    notice = random.choice(NOTICE_PERIODS)
                    education = random.choice(EDUCATIONS)
                    certifications = random.choice(CERTIFICATIONS_POOL)
                    languages = random.choice(LANGUAGES_POOL)
                    experience = build_experience(domain, city)
                    projects = build_projects(domain)
                    
                    # Generate email
                    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
                    mobile = f"9{random.randint(100000000, 999999999)}"
                    
                    # Create user
                    user = User(
                        email=email,
                        mobile=mobile,
                        password="password123",
                        full_name=full_name,
                        domain=domain,
                        city=city,
                        state=state,
                        profile_photo="uploads/profile_photos/avatar.png",
                        summary=f"Experienced {domain} with {experience_years} of expertise. "
                               f"Skilled in {', '.join(skills[:4])}. "
                               f"Passionate about delivering high-quality solutions.",
                        experience_years=experience_years,
                        skills=json.dumps(skills),
                        education=json.dumps(education),
                        experience=json.dumps(experience),
                        projects=json.dumps(projects),
                        certifications=json.dumps(certifications),
                        languages=json.dumps(languages),
                        achievements=json.dumps([f"Best Performer Award {random.randint(2019, 2024)}"]),
                        linkedin=f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
                        github=f"https://github.com/{first_name.lower()}{last_name.lower()}",
                        portfolio="",
                        expected_salary=salary,
                        notice_period=notice,
                        user_type='jobseeker',
                        email_verified=True,
                        mobile_verified=True,
                        profile_complete=True,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                    )
                    
                    db.session.add(user)
                    db.session.flush()  # Get user.id
                    
                    # ⭐ Generate profile HTML
                    filename = generate_profile_html(user, app)
                    if filename:
                        user.profile_url = filename
                        total_profiles_generated += 1
                    
                    db.session.commit()
                    domain_count += 1
                    total_created += 1
                    
                    # Progress indicator
                    if (i + 1) % 10 == 0:
                        print(f"  ✅ {i+1}/{professionals_per_domain} done...")
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ Error creating {full_name}: {str(e)[:100]}")
            
            print(f"  🎯 {domain}: {domain_count} professionals created")
        
        # ============================================================
        # FINAL REPORT
        # ============================================================
        print("\n" + "="*70)
        print(f"📊 SEEDING COMPLETE!")
        print(f"   Total professionals created: {total_created}")
        print(f"   Total profiles generated: {total_profiles_generated}")
        print(f"   Domains covered: {len(DOMAINS)}")
        
        # Verify counts
        total_in_db = User.query.filter_by(profile_complete=True, user_type='jobseeker').count()
        print(f"   Total in database: {total_in_db}")
        
        # Domain-wise count
        print(f"\n📋 DOMAIN-WISE BREAKDOWN:")
        for domain in DOMAINS:
            count = User.query.filter_by(domain=domain, profile_complete=True).count()
            bar = "█" * (count // 5)
            print(f"   {domain:<30} : {count:>4} {bar}")
        
        print("="*70)
        print("\n✅ Done! Run 'python app.py' to start the server.")
        print(f"🌐 Visit: http://127.0.0.1:5000")
        print("="*70)


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed professionals data')
    parser.add_argument('--count', type=int, default=50, 
                       help='Number of professionals per domain (default: 50)')
    parser.add_argument('--domain', type=str, default=None,
                       help='Seed only specific domain')
    
    args = parser.parse_args()
    
    if args.domain:
        # Seed only one domain
        
        if args.domain in DOMAINS:
            DOMAINS = [args.domain]
        else:
            print(f"❌ Domain '{args.domain}' not found!")
            print(f"Available domains: {', '.join(DOMAINS)}")
            sys.exit(1)
    
    seed_professionals(professionals_per_domain=args.count)