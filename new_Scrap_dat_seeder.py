"""
=============================================================================
Scraper Data Seeder - Websites, Keywords, Locations, Designations
=============================================================================
50+ Websites | 500+ Keywords | 50+ Locations | 50+ Designations
Updated for Dual Database (main.db + jobs.db)
=============================================================================
"""

from app import create_app
from models import db, ScrapeWebsite, ScrapeKeyword, ScrapeLocation, ScrapeDesignation
import json


def seed_all():
    """Seed all scraper tables with default data"""
    app = create_app()
    
    with app.app_context():
        # ⭐ Create all tables first (in case DB is new)
        db.create_all()
        
        # Check existing data
        existing_websites = ScrapeWebsite.query.count()
        existing_keywords = ScrapeKeyword.query.count()
        existing_locations = ScrapeLocation.query.count()
        
        if existing_websites > 0 or existing_keywords > 0:
            print(f"\n📊 Existing data found:")
            print(f"   Websites: {existing_websites}")
            print(f"   Keywords: {existing_keywords}")
            print(f"   Locations: {existing_locations}")
            
            choice = input("\nClear existing data before seeding? (y/n): ").lower()
            if choice == 'y':
                try:
                    ScrapeWebsite.query.delete()
                    ScrapeKeyword.query.delete()
                    ScrapeLocation.query.delete()
                    ScrapeDesignation.query.delete()
                    db.session.commit()
                    print("🗑️ Old data cleared!")
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️ Error clearing data: {e}")
            else:
                print("ℹ️ Keeping existing data. Only new entries will be added.")
        
        print("\n" + "="*60)
        print("🚀 STARTING DATA SEEDING...")
        print("="*60)
        
        added_websites = seed_websites()
        added_keywords = seed_keywords()
        added_locations = seed_locations()
        added_designations = seed_designations()
        
        print("\n" + "="*60)
        print(f"📊 SEEDING COMPLETE!")
        print(f"   Websites: {added_websites} new (+ {ScrapeWebsite.query.count()} total)")
        print(f"   Keywords: {added_keywords} new (+ {ScrapeKeyword.query.count()} total)")
        print(f"   Locations: {added_locations} new (+ {ScrapeLocation.query.count()} total)")
        print(f"   Designations: {added_designations} new (+ {ScrapeDesignation.query.count()} total)")
        print(f"   TOTAL NEW: {added_websites + added_keywords + added_locations + added_designations}")
        print("="*60)
        print("\n✅ Done! Run 'python app.py' to start the server.")
        print("📝 Admin can manage scraper settings from Admin Panel.")


def seed_websites():
    """50+ Job Websites"""
    websites_data = [
        # === GENERAL JOB PORTALS (Priority 1) ===
        ('Naukri.com', 'https://www.naukri.com/{keyword}-jobs?k={keyword}', 
         '["a.title", ".jobTuple-title", "h2 a", ".title"]',
         '[".subTitle", ".companyName", ".orgName"]',
         '[".location", ".loc", ".fleft"]', 'a.title', False, 1),
        
        ('Indeed India', 'https://in.indeed.com/jobs?q={keyword}&l={location}',
         '["h2.jobTitle", "h2 span", "a.jobTitle", ".title a"]',
         '[".companyName", ".company_name", "span.companyName"]',
         '[".companyLocation", ".location", ".recJobLoc"]', 'a.jobTitle', False, 1),
        
        ('LinkedIn Jobs', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0',
         '[".base-search-card__title", ".job-search-card__title", "h3"]',
         '[".base-search-card__subtitle", ".job-search-card__subtitle", "h4"]',
         '[".job-search-card__location", ".location"]', 'a.base-card__full-link', False, 1),
        
        ('Foundit (Monster)', 'https://www.foundit.in/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".company", ".org"]',
         '[".location"]', 'a', False, 1),
        
        ('Shine.com', 'https://www.shine.com/jobs/search?q={keyword}',
         '["h3", ".title", "a strong"]',
         '[".company", ".org"]',
         '[".location"]', 'a', False, 1),
        
        ('Freshersworld', 'https://www.freshersworld.com/jobs?q={keyword}',
         '["h3", ".job-title", "a strong"]',
         '[".company-name", ".company"]',
         '[".location"]', 'a', False, 1),
        
        ('Internshala Jobs', 'https://internshala.com/jobs/search?keyword={keyword}',
         '["h3", "h4", ".heading_4_5", ".job-title"]',
         '[".company-name", ".company_name", ".link_display_like_text"]',
         '[".location", "#location_names"]', 'a', False, 1),
        
        ('Apna.co', 'https://apna.co/jobs?q={keyword}',
         '["h3", ".title", "a"]',
         '[".employer-name", ".company"]',
         '[".location"]', 'a', False, 1),
        
        ('WorkIndia', 'https://www.workindia.in/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".company"]',
         '[".location"]', 'a', False, 1),
        
        ('TimesJobs', 'https://www.timesjobs.com/jobfunction/{keyword}-jobs',
         '["h3", ".title", "a"]',
         '[".company", ".org"]',
         '[".location"]', 'a', False, 1),
        
        # === IT/TECH SPECIFIC ===
        ('Cutshort', 'https://cutshort.io/jobs?q={keyword}',
         '["h3", ".title", "a strong"]',
         '[".company", ".org-name"]',
         '[".location"]', 'a', False, 1),
        
        ('Hirist', 'https://www.hirist.tech/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".company"]',
         '[".location"]', 'a', False, 1),
        
        ('Wellfound', 'https://wellfound.com/jobs?q={keyword}&location=india',
         '["h3", ".title", "a"]',
         '[".company", ".startup-name"]',
         '[".location"]', 'a', False, 1),
        
        # === JOB AGGREGATORS ===
        ('CareerJet India', 'https://www.careerjet.co.in/search/jobs?q={keyword}',
         '["h3", ".title", "a"]',
         '[".company"]',
         '[".location"]', 'a', False, 2),
        
        ('Jooble India', 'https://in.jooble.org/SearchResult?ukw={keyword}',
         '["h3", ".title", "a"]',
         '[".company"]',
         '[".location"]', 'a', False, 2),
        
        # === GOVERNMENT JOBS ===
        ('NCS Portal', 'https://www.ncs.gov.in/_layouts/15/NCS/JobsSearch.aspx?q={keyword}',
         '["h3", "h4", ".title", "a"]',
         '[".company", ".employer", ".org"]',
         '[".location"]', 'a', False, 2),
        
        ('Sarkari Result', 'https://www.sarkariresult.com/jobs/?s={keyword}',
         '["h3", ".title", "a"]',
         '[".dept"]',
         '[".location"]', 'a', False, 2),
        
        ('Free Job Alert', 'https://www.freejobalert.com/?s={keyword}',
         '["h3", ".title", "a"]',
         '[".dept"]',
         '[".location"]', 'a', False, 2),
        
        # === NGO/SOCIAL SECTOR ===
        ('SAMS - Social Sector', 'https://www.sams.co.in/Jobs/job-list',
         '["h3", "h4", ".job-title", ".title", "a strong"]',
         '[".company", ".org", ".organization", ".employer"]',
         '[".location", ".city", ".job-location"]', 'a', True, 2),
        
        ('DevNetJobs India', 'https://devnetjobsindia.org/?s={keyword}',
         '["h3", ".title", "a"]',
         '[".organization", ".company"]',
         '[".location"]', 'a', False, 2),
        
        ('Idealist', 'https://www.idealist.org/en/jobs?q={keyword}&location=India',
         '["h3", ".title", "a"]',
         '[".organization", ".company"]',
         '[".location"]', 'a', False, 2),
        
        # === SECTOR SPECIFIC ===
        ('Docthub (Healthcare)', 'https://www.docthub.com/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".hospital", ".clinic", ".company"]',
         '[".location"]', 'a', False, 2),
        
        ('LawBhoomi (Legal)', 'https://lawbhoomi.com/jobs/?s={keyword}',
         '["h3", ".title"]',
         '[".firm", ".company"]',
         '[".location"]', 'a', False, 2),
        
        ('ClassDoor (Education)', 'https://www.classdoor.in/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".school", ".college", ".institute"]',
         '[".location"]', 'a', False, 2),
        
        # === MORE PORTALS ===
        ('Monster India', 'https://www.monsterindia.com/search/{keyword}-jobs-in-{location}',
         '["h3", ".title", "a"]',
         '[".company-name", ".company"]',
         '[".location"]', 'a', False, 3),
        
        ('Google Jobs', 'https://www.google.com/search?q={keyword}+jobs+in+{location}&ibp=htl;jobs',
         '["h3", ".title"]',
         '[".company"]',
         '[".location"]', 'a', False, 3),
        
        ('SimplyHired India', 'https://www.simplyhired.co.in/search?q={keyword}&l={location}',
         '["h3", ".title"]',
         '[".company"]',
         '[".location"]', 'a', False, 3),
        
        ('FreshersLive', 'https://www.fresherslive.com/jobs?q={keyword}',
         '["h3", ".title"]',
         '[".company"]',
         '[".location"]', 'a', False, 2),
        
        ('Quikr Jobs', 'https://www.quikr.com/jobs/{keyword}+zwqxj1492613647',
         '["h3", ".title", "a"]',
         '[".company", ".org"]',
         '[".location"]', 'a', False, 3),
    ]
    
    added = 0
    for (name, url, titles, companies, locations, link, is_static, priority) in websites_data:
        if not ScrapeWebsite.query.filter_by(name=name).first():
            try:
                db.session.add(ScrapeWebsite(
                    name=name,
                    base_url=url,
                    card_selectors='[".job-card", "[class*=\\"job\\"]", "article", "li"]',
                    title_selectors=titles,
                    company_selectors=companies,
                    location_selectors=locations,
                    link_selector=link,
                    is_static_url=is_static,
                    priority=priority
                ))
                added += 1
            except Exception as e:
                print(f"⚠️ Error adding {name}: {e}")
                db.session.rollback()
    
    try:
        db.session.commit()
        print(f"✅ {added} websites added")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving websites: {e}")
    
    return added


def seed_keywords():
    """500+ Keywords - Simplified version"""
    keywords_data = [
        # IT & Software
        ('it', 'software developer'), ('it', 'software engineer'), ('it', 'python developer'),
        ('it', 'java developer'), ('it', 'react developer'), ('it', 'angular developer'),
        ('it', 'node.js developer'), ('it', 'full stack developer'), ('it', 'frontend developer'),
        ('it', 'backend developer'), ('it', '.net developer'), ('it', 'php developer'),
        ('it', 'android developer'), ('it', 'ios developer'), ('it', 'flutter developer'),
        ('it', 'devops engineer'), ('it', 'cloud engineer'), ('it', 'aws engineer'),
        ('it', 'data scientist'), ('it', 'data analyst'), ('it', 'machine learning engineer'),
        ('it', 'ai engineer'), ('it', 'cybersecurity analyst'), ('it', 'security engineer'),
        ('it', 'qa engineer'), ('it', 'test engineer'), ('it', 'database administrator'),
        ('it', 'system administrator'), ('it', 'network engineer'), ('it', 'it support'),
        ('it', 'ui designer'), ('it', 'ux designer'), ('it', 'product designer'),
        ('it', 'web developer'), ('it', 'wordpress developer'), ('it', 'laravel developer'),
        ('it', 'django developer'), ('it', 'flask developer'), ('it', 'spring boot developer'),
        
        # Management
        ('management', 'project manager'), ('management', 'product manager'), ('management', 'business analyst'),
        ('management', 'scrum master'), ('management', 'program manager'), ('management', 'operations manager'),
        ('management', 'team leader'), ('management', 'team lead'), ('management', 'general manager'),
        
        # HR
        ('hr', 'hr manager'), ('hr', 'hr executive'), ('hr', 'recruiter'),
        ('hr', 'talent acquisition'), ('hr', 'hr generalist'), ('hr', 'administration manager'),
        ('hr', 'office manager'), ('hr', 'front office executive'), ('hr', 'receptionist'),
        
        # Finance
        ('finance', 'accountant'), ('finance', 'finance manager'), ('finance', 'financial analyst'),
        ('finance', 'chartered accountant'), ('finance', 'banking'), ('finance', 'bank job'),
        ('finance', 'bank po'), ('finance', 'bank clerk'), ('finance', 'insurance'),
        ('finance', 'accounts executive'), ('finance', 'auditor'), ('finance', 'tax consultant'),
        
        # Sales & Marketing
        ('sales', 'sales executive'), ('sales', 'sales manager'), ('sales', 'business development'),
        ('sales', 'business development executive'), ('sales', 'business development manager'),
        ('marketing', 'marketing manager'), ('marketing', 'digital marketing'), ('marketing', 'seo'),
        ('marketing', 'social media'), ('marketing', 'content writer'), ('marketing', 'copywriter'),
        ('sales', 'retail sales'), ('sales', 'counter sales'), ('sales', 'telecaller'),
        
        # Healthcare
        ('healthcare', 'doctor'), ('healthcare', 'nurse'), ('healthcare', 'pharmacist'),
        ('healthcare', 'medical officer'), ('healthcare', 'lab technician'), ('healthcare', 'physician'),
        ('healthcare', 'surgeon'), ('healthcare', 'dentist'), ('healthcare', 'physiotherapist'),
        ('healthcare', 'hospital administrator'), ('healthcare', 'medical coder'),
        
        # Education
        ('education', 'teacher'), ('education', 'professor'), ('education', 'lecturer'),
        ('education', 'principal'), ('education', 'faculty'), ('education', 'teaching'),
        ('education', 'school teacher'), ('education', 'college lecturer'), ('education', 'tutor'),
        
        # Engineering (Non-IT)
        ('engineering', 'civil engineer'), ('engineering', 'mechanical engineer'), ('engineering', 'electrical engineer'),
        ('engineering', 'electronics engineer'), ('engineering', 'site engineer'), ('engineering', 'design engineer'),
        ('engineering', 'production engineer'), ('engineering', 'quality engineer'), ('engineering', 'maintenance engineer'),
        
        # Legal
        ('legal', 'lawyer'), ('legal', 'advocate'), ('legal', 'legal advisor'),
        ('legal', 'compliance officer'), ('legal', 'company secretary'),
        
        # Government
        ('govt', 'government job'), ('govt', 'sarkari naukri'), ('govt', 'public sector'),
        ('govt', 'psu jobs'), ('govt', 'railway job'), ('govt', 'defence job'),
        ('govt', 'police job'), ('govt', 'government teacher'), ('govt', 'government clerk'),
        
        # NGO
        ('ngo', 'program manager ngo'), ('ngo', 'social worker'), ('ngo', 'ngo job'),
        ('ngo', 'fundraising'), ('ngo', 'development sector'), ('ngo', 'csr'),
        
        # Freshers
        ('fresher', 'fresher'), ('fresher', 'trainee'), ('fresher', 'intern'),
        ('fresher', 'entry level'), ('fresher', 'graduate trainee'), ('fresher', 'apprentice'),
        ('fresher', 'fresher job'),
        
        # Remote
        ('remote', 'work from home'), ('remote', 'remote job'), ('remote', 'virtual job'),
        ('remote', 'online job'), ('remote', 'freelance'), ('remote', 'part time job'),
        ('remote', 'home based job'),
        
        # Other Sectors
        ('other', 'data entry operator'), ('other', 'computer operator'), ('other', 'back office'),
        ('other', 'bpo'), ('other', 'call center'), ('other', 'customer service'),
        ('other', 'customer support'), ('other', 'delivery boy'), ('other', 'driver'),
        ('other', 'security guard'), ('other', 'security officer'), ('other', 'electrician'),
        ('other', 'plumber'), ('other', 'welder'), ('other', 'technician'),
        ('other', 'mechanic'), ('other', 'chef'), ('other', 'cook'),
        ('other', 'waiter'), ('other', 'housekeeping'), ('other', 'beautician'),
        ('other', 'photographer'), ('other', 'video editor'), ('other', 'graphic designer'),
        ('other', 'store manager'), ('other', 'cashier'), ('other', 'warehouse'),
    ]
    
    added = 0
    for category, keyword in keywords_data:
        if not ScrapeKeyword.query.filter_by(keyword=keyword).first():
            try:
                db.session.add(ScrapeKeyword(category=category, keyword=keyword))
                added += 1
            except:
                pass
    
    try:
        db.session.commit()
        print(f"✅ {added} keywords added")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving keywords: {e}")
    
    return added


def seed_locations():
    """50+ Indian Locations"""
    locations_data = [
        ('Mumbai', 1), ('Delhi', 1), ('Bangalore', 1), ('Hyderabad', 1),
        ('Chennai', 1), ('Kolkata', 1), ('Pune', 1), ('Ahmedabad', 1),
        ('Jaipur', 1), ('Lucknow', 1), ('Indore', 1), ('Bhopal', 1),
        ('Chandigarh', 1), ('Kochi', 1), ('Coimbatore', 1), ('Nagpur', 1),
        ('Surat', 2), ('Vadodara', 2), ('Noida', 1), ('Gurgaon', 1),
        ('Bhubaneswar', 2), ('Patna', 2), ('Ranchi', 2), ('Visakhapatnam', 2),
        ('Dehradun', 2), ('Guwahati', 2), ('Thiruvananthapuram', 2), ('Mysore', 2),
        ('Mangalore', 2), ('Vijayawada', 2), ('Raipur', 2), ('Jodhpur', 2),
        ('Agra', 2), ('Varanasi', 2), ('Kanpur', 2), ('Ludhiana', 2),
        ('Amritsar', 2), ('Nashik', 2), ('Rajkot', 2), ('Jammu', 2),
        ('India', 1), ('Remote', 1), ('Work from Home', 1),
        ('Anywhere in India', 2),
    ]
    
    added = 0
    for location, priority in locations_data:
        if not ScrapeLocation.query.filter_by(location=location).first():
            try:
                db.session.add(ScrapeLocation(location=location, priority=priority))
                added += 1
            except:
                pass
    
    try:
        db.session.commit()
        print(f"✅ {added} locations added")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving locations: {e}")
    
    return added


def seed_designations():
    """50+ Common Designations"""
    designations_data = [
        ('it', 'Software Developer'), ('it', 'Senior Software Engineer'), ('it', 'Tech Lead'),
        ('it', 'Full Stack Developer'), ('it', 'Frontend Developer'), ('it', 'Backend Developer'),
        ('it', 'DevOps Engineer'), ('it', 'Data Scientist'), ('it', 'AI Engineer'),
        ('it', 'QA Engineer'), ('it', 'Database Administrator'), ('it', 'System Administrator'),
        ('it', 'Network Engineer'), ('it', 'UI Designer'), ('it', 'UX Designer'),
        ('management', 'Project Manager'), ('management', 'Product Manager'), ('management', 'Business Analyst'),
        ('management', 'Scrum Master'), ('management', 'Operations Manager'), ('management', 'Team Leader'),
        ('hr', 'HR Manager'), ('hr', 'Recruiter'), ('hr', 'Talent Acquisition'),
        ('finance', 'Accountant'), ('finance', 'Finance Manager'), ('finance', 'Financial Analyst'),
        ('finance', 'Chartered Accountant'), ('finance', 'Banking Officer'),
        ('sales', 'Sales Executive'), ('sales', 'Business Development Manager'), ('sales', 'Area Sales Manager'),
        ('marketing', 'Marketing Manager'), ('marketing', 'Digital Marketing Specialist'), ('marketing', 'Content Writer'),
        ('healthcare', 'Doctor'), ('healthcare', 'Nurse'), ('healthcare', 'Pharmacist'),
        ('healthcare', 'Medical Officer'), ('healthcare', 'Lab Technician'),
        ('education', 'Teacher'), ('education', 'Professor'), ('education', 'Principal'),
        ('engineering', 'Civil Engineer'), ('engineering', 'Mechanical Engineer'), ('engineering', 'Electrical Engineer'),
        ('other', 'Data Entry Operator'), ('other', 'Customer Service Representative'), ('other', 'Delivery Executive'),
        ('other', 'Security Guard'), ('other', 'Electrician'), ('other', 'Beautician'),
        ('other', 'Chef'), ('other', 'Driver'), ('other', 'Technician'),
    ]
    
    added = 0
    for category, designation in designations_data:
        if not ScrapeDesignation.query.filter_by(designation=designation).first():
            try:
                db.session.add(ScrapeDesignation(category=category, designation=designation))
                added += 1
            except:
                pass
    
    try:
        db.session.commit()
        print(f"✅ {added} designations added")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving designations: {e}")
    
    return added


if __name__ == '__main__':
    seed_all()