"""
=============================================================================
Scraper Data Seeder - Websites, Keywords, Locations, Designations
=============================================================================
50+ Websites | 500+ Keywords | 50+ Locations | 50+ Designations
=============================================================================
"""

from app import create_app
from models import db, ScrapeWebsite, ScrapeKeyword, ScrapeLocation, ScrapeDesignation
import json

def seed_all():
    app = create_app()
    
    with app.app_context():
        # पुराना डेटा क्लियर करें (optional)
        if input("Clear existing data? (y/n): ").lower() == 'y':
            ScrapeWebsite.query.delete()
            ScrapeKeyword.query.delete()
            ScrapeLocation.query.delete()
            ScrapeDesignation.query.delete()
            db.session.commit()
            print("🗑️ Old data cleared!")
        
        added_websites = seed_websites()
        added_keywords = seed_keywords()
        added_locations = seed_locations()
        added_designations = seed_designations()
        
        db.session.commit()
        
        print("\n" + "="*60)
        print(f"📊 SEEDING COMPLETE!")
        print(f"   Websites: {added_websites}")
        print(f"   Keywords: {added_keywords}")
        print(f"   Locations: {added_locations}")
        print(f"   Designations: {added_designations}")
        print(f"   TOTAL: {added_websites + added_keywords + added_locations + added_designations}")
        print("="*60)


def seed_websites():
    """50+ Job Websites"""
    websites_data = [
        # === GENERAL JOB PORTALS (Priority 1) ===
        ('Naukri.com', 'https://www.naukri.com/{keyword}-jobs?k={keyword}', '[".jobTuple", "[class*=\\"jobTuple\\"]", ".list-item", "article"]', '["a.title", ".jobTuple-title", "h2 a", ".title"]', '[".subTitle", ".companyName", ".orgName"]', '[".location", ".loc", ".fleft"]', 'a.title', 1),
        ('Indeed India', 'https://in.indeed.com/jobs?q={keyword}&l={location}', '[".job_seen_beacon", ".cardOutline", ".resultContent"]', '["h2.jobTitle", "h2 span", "a.jobTitle", ".title a"]', '[".companyName", ".company_name", "span.companyName"]', '[".companyLocation", ".location", ".recJobLoc"]', 'a.jobTitle', 1),
        ('LinkedIn Jobs', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0', '[".base-card", ".job-search-card", "li"]', '[".base-search-card__title", ".job-search-card__title", "h3"]', '[".base-search-card__subtitle", ".job-search-card__subtitle", "h4"]', '[".job-search-card__location", ".location"]', 'a.base-card__full-link', 1),
        ('Foundit (Monster)', 'https://www.foundit.in/jobs?q={keyword}', '[".jobCard", "[class*=\\"job\\"]", ".card"]', '["h3", ".title", "[class*=\\"title\\"]"]', '[".company", ".org", "[class*=\\"company\\"]"]', '[".location", "[class*=\\"location\\"]"]', 'a', 1),
        ('Shine.com', 'https://www.shine.com/jobs/search?q={keyword}', '[".jobCard", ".resultCard", "[class*=\\"job\\"]"]', '["h3", ".title", "a strong"]', '[".company", ".org"]', '[".location"]', 'a', 1),
        ('Freshersworld', 'https://www.freshersworld.com/jobs?q={keyword}', '[".job-container", ".job-list", "[class*=\\"job\\"]"]', '["h3", ".job-title", "a strong"]', '[".company-name", ".company"]', '[".location"]', 'a', 1),
        ('Internshala Jobs', 'https://internshala.com/jobs/search?keyword={keyword}', '[".individual_internship", "[class*=\\"individual\\"]"]', '["h3", "h4", ".heading_4_5", ".job-title"]', '[".company-name", ".company_name", ".link_display_like_text"]', '[".location", "#location_names"]', 'a', 1),
        ('Apna.co', 'https://apna.co/jobs?q={keyword}', '[".job-card", "[class*=\\"job\\"]"]', '["h3", ".title", "a"]', '[".employer-name", ".company"]', '[".location"]', 'a', 1),
        ('WorkIndia', 'https://www.workindia.in/jobs?q={keyword}', '[".job-card", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 1),
        ('TimesJobs', 'https://www.timesjobs.com/jobfunction/{keyword}-jobs', '[".job-listing", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".company", ".org"]', '[".location"]', 'a', 1),
        
        # === IT/TECH SPECIFIC (Priority 1) ===
        ('Cutshort', 'https://cutshort.io/jobs?q={keyword}', '[".job-card", "[class*=\\"job\\"]"]', '["h3", ".title", "a strong"]', '[".company", ".org-name"]', '[".location"]', 'a', 1),
        ('Hirist', 'https://www.hirist.tech/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 1),
        ('Wellfound (AngelList)', 'https://wellfound.com/jobs?q={keyword}&location=india', '[".job-listing", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".company", ".startup-name"]', '[".location"]', 'a', 1),
        ('Instahyre', 'https://www.instahyre.com/search-jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".card"]', '["h3", ".title", "a"]', '[".company", ".employer"]', '[".location"]', 'a', 1),
        ('Turing', 'https://www.turing.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 1),
        
        # === JOB AGGREGATORS (Priority 2) ===
        ('CareerJet India', 'https://www.careerjet.co.in/search/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 2),
        ('JobRapido India', 'https://in.jobrapido.com/?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 2),
        ('Neuvoo India', 'https://in.neuvoo.com/jobs/?k={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 2),
        ('Jooble India', 'https://in.jooble.org/SearchResult?ukw={keyword}', '[".result-card", "[class*=\\"result\\"]", ".job-card"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 2),
        ('Jora India', 'https://in.jora.com/{keyword}-jobs-in-{location}', '[".job-card", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 2),
        ('Adzuna India', 'https://www.adzuna.in/search?q={keyword}&w={location}', '[".job-card", "[class*=\\"job\\"]", ".a"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 2),
        ('ZipRecruiter India', 'https://www.ziprecruiter.in/candidate/search?search={keyword}&location={location}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 2),
        
        # === GOVERNMENT JOBS (Priority 2) ===
        ('NCS Portal', 'https://www.ncs.gov.in/_layouts/15/NCS/JobsSearch.aspx?q={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".card", ".result"]', '["h3", "h4", ".title", "a"]', '[".company", ".employer", ".org"]', '[".location"]', 'a', 2),
        ('Sarkari Result', 'https://www.sarkariresult.com/jobs/?s={keyword}', '[".job-listing", "[class*=\\"job\\"]", "li"]', '["h3", ".title", "a"]', '[".dept"]', '[".location"]', 'a', 2),
        ('Free Job Alert', 'https://www.freejobalert.com/?s={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".post"]', '["h3", ".title", "a"]', '[".dept"]', '[".location"]', 'a', 2),
        ('Rojgar Samachar', 'https://www.rojgarsamachar.in/?s={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".dept"]', '[".location"]', 'a', 2),
        ('Govt Jobs Alert', 'https://www.govtjobsalert.in/search?q={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".post"]', '["h3", ".title", "a"]', '[".dept", ".org"]', '[".location"]', 'a', 2),
        
        # === NGO/SOCIAL SECTOR (Priority 2) ===
        ('SAMS - Social Sector', 'https://www.sams.co.in/Jobs/job-list', '[".job-listing", ".job-item", "[class*=\\"job\\"]", "article", ".listing-item"]', '["h3", "h4", ".job-title", ".title", "a strong"]', '[".company", ".org", ".organization", ".employer"]', '[".location", ".city", ".job-location"]', 'a', 2),
        ('DevNetJobs India', 'https://devnetjobsindia.org/?s={keyword}', '[".job-listing", "[class*=\\"job\\"]", ".post"]', '["h3", ".title", "a"]', '[".organization", ".company"]', '[".location"]', 'a', 2),
        ('Arthan Careers', 'https://arthancareers.com/job-listing/?search={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".organization", ".company"]', '[".location"]', 'a', 2),
        ('Idealist', 'https://www.idealist.org/en/jobs?q={keyword}&location=India', '[".job-listing", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".organization", ".company"]', '[".location"]', 'a', 2),
        ('ReliefWeb', 'https://reliefweb.int/jobs?search={keyword}&country=India', '[".job-listing", "[class*=\\"job\\"]", "article"]', '["h3", "h4", ".title a"]', '[".company", ".source", ".organization"]', '[".location", ".country"]', 'a', 2),
        ('Impactpool', 'https://www.impactpool.org/?q={keyword}&location=India', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title", "a"]', '[".organization", ".company"]', '[".location"]', 'a', 2),
        ('Devex', 'https://www.devex.com/jobs/search?filter%5Bkeywords%5D={keyword}&filter%5Blocations%5D=India', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".organization", ".company"]', '[".location"]', 'a', 2),
        ('UN Job Net', 'https://www.unjobnet.org/?q={keyword}&location=India', '[".job-listing", "[class*=\\"job\\"]", ".vacancy"]', '["h3", ".title", "a"]', '[".organization", ".agency"]', '[".location", ".country"]', 'a', 2),
        
        # === SECTOR SPECIFIC (Priority 2) ===
        ('Docthub (Healthcare)', 'https://www.docthub.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".hospital", ".clinic", ".company"]', '[".location"]', 'a', 2),
        ('LawBhoomi (Legal)', 'https://lawbhoomi.com/jobs/?s={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".firm", ".company"]', '[".location"]', 'a', 2),
        ('ClassDoor (Education)', 'https://www.classdoor.in/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".school", ".college", ".institute"]', '[".location"]', 'a', 2),
        ('HerKey (Women)', 'https://www.herkey.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 2),
        ('FreshersLive', 'https://www.fresherslive.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 2),
        
        # === MORE PORTALS (Priority 3) ===
        ('Quikr Jobs', 'https://www.quikr.com/jobs/{keyword}+zwqxj1492613647', '[".job-card", "[class*=\\"job\\"]", ".result"]', '["h3", ".title", "a"]', '[".company", ".org"]', '[".location"]', 'a', 3),
        ('ClickIndia Jobs', 'https://www.clickindia.com/jobs/{keyword}-jobs', '[".job-listing", "[class*=\\"job\\"]", ".card"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 3),
        ('PostJobFree India', 'https://www.postjobfree.com/jobs?q={keyword}&l=India', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title", "a"]', '[".company"]', '[".location"]', 'a', 3),
        ('Jobitus', 'https://www.jobitus.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
        ('Wisdom Jobs', 'https://www.wisdomjobs.com/search-jobs?keyword={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
        ('Hirect', 'https://www.hirect.in/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
        ('JobYoda', 'https://www.jobyoda.com/jobs?q={keyword}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
        ('Monster India', 'https://www.monsterindia.com/search/{keyword}-jobs-in-{location}', '[".job-tuple", ".card-wrapper"]', '["h3", ".title", "a"]', '[".company-name", ".company"]', '[".location"]', 'a', 3),
        ('Google Jobs', 'https://www.google.com/search?q={keyword}+jobs+in+{location}&ibp=htl;jobs', '["[class*=\\"job\\"]", ".g-card"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
        ('SimplyHired India', 'https://www.simplyhired.co.in/search?q={keyword}&l={location}', '[".job-listing", "[class*=\\"job\\"]"]', '["h3", ".title"]', '[".company"]', '[".location"]', 'a', 3),
    ]
    
    added = 0
    for name, url, cards, titles, companies, locations, link, priority in websites_data:
        if not ScrapeWebsite.query.filter_by(name=name).first():
            db.session.add(ScrapeWebsite(
                name=name, base_url=url,
                card_selectors=cards, title_selectors=titles,
                company_selectors=companies, location_selectors=locations,
                link_selector=link, priority=priority, is_static_url=('{keyword}' not in url)
            ))
            added += 1
    
    db.session.commit()
    print(f"✅ {added} websites added")
    return added


def seed_keywords():
    """500+ Keywords for all sectors"""
    keywords_data = [
        # === IT & SOFTWARE (70+) ===
        ('it_software', 'software developer'), ('it_software', 'software engineer'), ('it_software', 'programmer'),
        ('it_software', 'web developer'), ('it_software', 'full stack developer'), ('it_software', 'frontend developer'),
        ('it_software', 'backend developer'), ('it_software', 'application developer'), ('it_software', 'senior software engineer'),
        ('it_python', 'python developer'), ('it_python', 'django developer'), ('it_python', 'flask developer'),
        ('it_python', 'python engineer'), ('it_python', 'python backend'), ('it_python', 'python full stack'),
        ('it_java', 'java developer'), ('it_java', 'java engineer'), ('it_java', 'spring boot developer'),
        ('it_java', 'j2ee developer'), ('it_java', 'core java developer'), ('it_java', 'java architect'),
        ('it_js', 'react developer'), ('it_js', 'angular developer'), ('it_js', 'vue.js developer'),
        ('it_js', 'node.js developer'), ('it_js', 'javascript developer'), ('it_js', 'typescript developer'),
        ('it_js', 'frontend engineer'), ('it_js', 'next.js developer'), ('it_js', 'mean stack developer'), ('it_js', 'mern stack developer'),
        ('it_dotnet', '.net developer'), ('it_dotnet', 'c# developer'), ('it_dotnet', 'asp.net developer'), ('it_dotnet', '.net core developer'),
        ('it_php', 'php developer'), ('it_php', 'laravel developer'), ('it_php', 'wordpress developer'), ('it_php', 'php engineer'),
        ('it_mobile', 'android developer'), ('it_mobile', 'ios developer'), ('it_mobile', 'react native developer'),
        ('it_mobile', 'flutter developer'), ('it_mobile', 'mobile app developer'), ('it_mobile', 'swift developer'), ('it_mobile', 'kotlin developer'),
        ('it_devops', 'devops engineer'), ('it_devops', 'cloud engineer'), ('it_devops', 'aws engineer'),
        ('it_devops', 'azure engineer'), ('it_devops', 'gcp engineer'), ('it_devops', 'kubernetes engineer'), ('it_devops', 'docker engineer'),
        ('it_devops', 'site reliability engineer'), ('it_devops', 'platform engineer'), ('it_devops', 'jenkins engineer'),
        ('it_data', 'data scientist'), ('it_data', 'data analyst'), ('it_data', 'data engineer'),
        ('it_data', 'machine learning engineer'), ('it_data', 'ai engineer'), ('it_data', 'nlp engineer'),
        ('it_data', 'computer vision engineer'), ('it_data', 'deep learning engineer'), ('it_data', 'business intelligence analyst'),
        ('it_security', 'cybersecurity analyst'), ('it_security', 'security engineer'), ('it_security', 'ethical hacker'),
        ('it_security', 'penetration tester'), ('it_security', 'security consultant'), ('it_security', 'information security analyst'),
        ('it_qa', 'qa engineer'), ('it_qa', 'test engineer'), ('it_qa', 'automation tester'),
        ('it_qa', 'quality analyst'), ('it_qa', 'sdet'), ('it_qa', 'manual tester'), ('it_qa', 'performance tester'),
        ('it_db', 'database administrator'), ('it_db', 'sql developer'), ('it_db', 'oracle dba'),
        ('it_db', 'mysql dba'), ('it_db', 'postgresql developer'), ('it_db', 'mongodb developer'),
        ('it_support', 'system administrator'), ('it_support', 'network engineer'), ('it_support', 'it support engineer'),
        ('it_support', 'helpdesk technician'), ('it_support', 'technical support engineer'), ('it_support', 'desktop support engineer'),
        ('it_ui', 'ui designer'), ('it_ui', 'ux designer'), ('it_ui', 'product designer'),
        ('it_ui', 'graphic designer'), ('it_ui', 'visual designer'), ('it_ui', 'web designer'),
        ('it_ui', 'figma designer'), ('it_ui', 'motion designer'),
        
        # === MANAGEMENT (40+) ===
        ('mgmt_project', 'project manager'), ('mgmt_project', 'program manager'), ('mgmt_project', 'scrum master'),
        ('mgmt_project', 'agile coach'), ('mgmt_project', 'delivery manager'), ('mgmt_project', 'technical project manager'),
        ('mgmt_product', 'product manager'), ('mgmt_product', 'product owner'), ('mgmt_product', 'business analyst'),
        ('mgmt_product', 'product analyst'), ('mgmt_product', 'associate product manager'), ('mgmt_product', 'senior product manager'),
        ('mgmt_general', 'operations manager'), ('mgmt_general', 'general manager'), ('mgmt_general', 'branch manager'),
        ('mgmt_general', 'team leader'), ('mgmt_general', 'team lead'), ('mgmt_general', 'department head'),
        ('mgmt_general', 'assistant manager'), ('mgmt_general', 'deputy manager'), ('mgmt_general', 'management trainee'),
        ('mgmt_executive', 'ceo'), ('mgmt_executive', 'cto'), ('mgmt_executive', 'coo'),
        ('mgmt_executive', 'director'), ('mgmt_executive', 'vp engineering'), ('mgmt_executive', 'head of department'),
        
        # === HR & RECRUITMENT (25+) ===
        ('hr', 'hr manager'), ('hr', 'hr executive'), ('hr', 'hr generalist'),
        ('hr', 'recruiter'), ('hr', 'talent acquisition'), ('hr', 'hr coordinator'),
        ('hr', 'hr business partner'), ('hr', 'recruitment consultant'), ('hr', 'sourcing specialist'),
        ('hr', 'payroll executive'), ('hr', 'training manager'), ('hr', 'l&d manager'),
        ('hr', 'hr intern'), ('hr', 'hr assistant'), ('hr', 'administration manager'),
        ('hr', 'office manager'), ('hr', 'front office executive'), ('hr', 'receptionist'),
        ('hr', 'admin executive'), ('hr', 'facility manager'), ('hr', 'company secretary'),
        
        # === FINANCE & ACCOUNTING (40+) ===
        ('finance', 'accountant'), ('finance', 'senior accountant'), ('finance', 'junior accountant'),
        ('finance', 'finance manager'), ('finance', 'financial analyst'), ('finance', 'chartered accountant'),
        ('finance', 'cost accountant'), ('finance', 'tax consultant'), ('finance', 'auditor'),
        ('finance', 'internal auditor'), ('finance', 'accounts executive'), ('finance', 'accounts manager'),
        ('finance', 'billing executive'), ('finance', 'collection executive'), ('finance', 'credit manager'),
        ('finance', 'investment banker'), ('finance', 'wealth manager'), ('finance', 'financial advisor'),
        ('finance', 'insurance advisor'), ('finance', 'loan officer'), ('finance', 'banking officer'),
        ('finance', 'bank po'), ('finance', 'bank clerk'), ('finance', 'relationship manager'),
        ('finance', 'mutual fund advisor'), ('finance', 'stock broker'), ('finance', 'equity analyst'),
        ('finance', 'risk analyst'), ('finance', 'compliance officer'), ('finance', 'gst practitioner'),
        ('finance', 'tally operator'), ('finance', 'bookkeeper'), ('finance', 'data entry operator'),
        
        # === SALES & MARKETING (50+) ===
        ('sales', 'sales executive'), ('sales', 'sales manager'), ('sales', 'business development executive'),
        ('sales', 'business development manager'), ('sales', 'area sales manager'), ('sales', 'regional sales manager'),
        ('sales', 'sales officer'), ('sales', 'sales representative'), ('sales', 'territory sales manager'),
        ('sales', 'key account manager'), ('sales', 'client relationship manager'), ('sales', 'presales consultant'),
        ('sales', 'inside sales'), ('sales', 'field sales'), ('sales', 'retail sales'),
        ('sales', 'counter sales'), ('sales', 'showroom sales'), ('sales', 'sales coordinator'),
        ('sales', 'telecaller'), ('sales', 'telesales'), ('sales', 'customer support'),
        ('marketing', 'marketing manager'), ('marketing', 'digital marketing executive'), ('marketing', 'digital marketing manager'),
        ('marketing', 'seo specialist'), ('marketing', 'sem specialist'), ('marketing', 'social media manager'),
        ('marketing', 'content writer'), ('marketing', 'content strategist'), ('marketing', 'copywriter'),
        ('marketing', 'brand manager'), ('marketing', 'marketing coordinator'), ('marketing', 'market research analyst'),
        ('marketing', 'email marketing'), ('marketing', 'affiliate marketing'), ('marketing', 'google ads specialist'),
        ('marketing', 'facebook ads specialist'), ('marketing', 'ppc specialist'), ('marketing', 'growth hacker'),
        ('marketing', 'public relations'), ('marketing', 'corporate communication'), ('marketing', 'event manager'),
        
        # === HEALTHCARE (35+) ===
        ('healthcare', 'doctor'), ('healthcare', 'physician'), ('healthcare', 'surgeon'),
        ('healthcare', 'medical officer'), ('healthcare', 'general practitioner'), ('healthcare', 'specialist doctor'),
        ('healthcare', 'nurse'), ('healthcare', 'staff nurse'), ('healthcare', 'nursing officer'),
        ('healthcare', 'pharmacist'), ('healthcare', 'pharmacy assistant'), ('healthcare', 'medical representative'),
        ('healthcare', 'lab technician'), ('healthcare', 'medical lab technologist'), ('healthcare', 'pathology technician'),
        ('healthcare', 'radiology technician'), ('healthcare', 'x-ray technician'), ('healthcare', 'ot technician'),
        ('healthcare', 'dentist'), ('healthcare', 'physiotherapist'), ('healthcare', 'dietitian'),
        ('healthcare', 'hospital administrator'), ('healthcare', 'healthcare manager'), ('healthcare', 'medical coder'),
        ('healthcare', 'medical biller'), ('healthcare', 'clinical research'), ('healthcare', 'drug safety associate'),
        ('healthcare', 'homeopathic doctor'), ('healthcare', 'ayurveda doctor'), ('healthcare', 'veterinary doctor'),
        ('healthcare', 'optometrist'), ('healthcare', 'psychologist'), ('healthcare', 'counselor'),
        
        # === EDUCATION (25+) ===
        ('education', 'teacher'), ('education', 'professor'), ('education', 'lecturer'),
        ('education', 'faculty'), ('education', 'assistant professor'), ('education', 'associate professor'),
        ('education', 'teaching assistant'), ('education', 'primary teacher'), ('education', 'secondary teacher'),
        ('education', 'high school teacher'), ('education', 'college lecturer'), ('education', 'university professor'),
        ('education', 'principal'), ('education', 'vice principal'), ('education', 'school administrator'),
        ('education', 'academic coordinator'), ('education', 'education counselor'), ('education', 'admission counselor'),
        ('education', 'librarian'), ('education', 'lab assistant'), ('education', 'sports teacher'),
        ('education', 'music teacher'), ('education', 'dance teacher'), ('education', 'art teacher'),
        ('education', 'special educator'), ('education', 'montessori teacher'), ('education', 'preschool teacher'),
        
        # === ENGINEERING (NON-IT) (25+) ===
        ('engineering', 'civil engineer'), ('engineering', 'structural engineer'), ('engineering', 'site engineer'),
        ('engineering', 'construction engineer'), ('engineering', 'project engineer'), ('engineering', 'planning engineer'),
        ('engineering', 'mechanical engineer'), ('engineering', 'design engineer'), ('engineering', 'production engineer'),
        ('engineering', 'quality engineer'), ('engineering', 'maintenance engineer'), ('engineering', 'automobile engineer'),
        ('engineering', 'electrical engineer'), ('engineering', 'electronics engineer'), ('engineering', 'instrumentation engineer'),
        ('engineering', 'chemical engineer'), ('engineering', 'process engineer'), ('engineering', 'safety engineer'),
        ('engineering', 'environmental engineer'), ('engineering', 'mining engineer'), ('engineering', 'textile engineer'),
        ('engineering', 'biomedical engineer'), ('engineering', 'aerospace engineer'), ('engineering', 'marine engineer'),
        
        # === LEGAL (15+) ===
        ('legal', 'lawyer'), ('legal', 'advocate'), ('legal', 'attorney'),
        ('legal', 'legal advisor'), ('legal', 'legal counsel'), ('legal', 'corporate lawyer'),
        ('legal', 'legal officer'), ('legal', 'compliance officer'), ('legal', 'company secretary'),
        ('legal', 'legal assistant'), ('legal', 'paralegal'), ('legal', 'legal intern'),
        ('legal', 'patent attorney'), ('legal', 'tax lawyer'), ('legal', 'litigation lawyer'),
        
        # === GOVERNMENT & PUBLIC SECTOR (20+) ===
        ('govt', 'government job'), ('govt', 'sarkari naukri'), ('govt', 'public sector'),
        ('govt', 'psu jobs'), ('govt', 'bank job'), ('govt', 'bank po'),
        ('govt', 'bank clerk'), ('govt', 'railway job'), ('govt', 'defence job'),
        ('govt', 'police job'), ('govt', 'teacher government'), ('govt', 'nurse government'),
        ('govt', 'clerk government'), ('govt', 'stenographer'), ('govt', 'data entry government'),
        ('govt', 'peon'), ('govt', 'driver government'), ('govt', 'sweeper government'),
        ('govt', 'forest guard'), ('govt', 'patwari'), ('govt', 'lec'),
        
        # === NGO & SOCIAL SECTOR (20+) ===
        ('ngo', 'program manager ngo'), ('ngo', 'program officer'), ('ngo', 'project coordinator ngo'),
        ('ngo', 'social worker'), ('ngo', 'community development'), ('ngo', 'csr manager'),
        ('ngo', 'fundraising manager'), ('ngo', 'partnerships manager'), ('ngo', 'resource mobilization'),
        ('ngo', 'humanitarian worker'), ('ngo', 'relief worker'), ('ngo', 'disaster management'),
        ('ngo', 'public health'), ('ngo', 'community health worker'), ('ngo', 'field officer ngo'),
        ('ngo', 'monitoring and evaluation'), ('ngo', 'research associate ngo'), ('ngo', 'advocacy officer'),
        
        # === ENTRY LEVEL & FRESHERS (30+) ===
        ('fresher', 'fresher'), ('fresher', 'trainee'), ('fresher', 'intern'),
        ('fresher', 'entry level'), ('fresher', 'graduate trainee'), ('fresher', 'apprentice'),
        ('fresher', 'management trainee'), ('fresher', 'junior engineer'), ('fresher', 'junior developer'),
        ('fresher', 'fresher teacher'), ('fresher', 'fresher accountant'), ('fresher', 'fresher nurse'),
        ('fresher', 'fresher sales'), ('fresher', 'fresher marketing'), ('fresher', 'fresher hr'),
        ('fresher', 'fresher bpo'), ('fresher', 'fresher data entry'), ('fresher', 'fresher receptionist'),
        ('remote', 'work from home'), ('remote', 'remote job'), ('remote', 'virtual job'),
        ('remote', 'online job'), ('remote', 'freelance'), ('remote', 'part time job'),
        ('remote', 'home based job'), ('remote', 'telecommute'), ('remote', 'online teaching'),
        ('remote', 'remote developer'), ('remote', 'remote data entry'), ('remote', 'remote customer service'),
        
        # === OTHER SECTORS (70+) ===
        ('other_data', 'data entry operator'), ('other_data', 'computer operator'), ('other_data', 'back office executive'),
        ('other_bpo', 'bpo'), ('other_bpo', 'call center'), ('other_bpo', 'customer service'),
        ('other_bpo', 'customer support'), ('other_bpo', 'voice process'), ('other_bpo', 'non voice process'),
        ('other_bpo', 'chat support'), ('other_bpo', 'email support'), ('other_bpo', 'technical support'),
        ('other_logistics', 'delivery boy'), ('other_logistics', 'delivery executive'), ('other_logistics', 'driver'),
        ('other_logistics', 'rider'), ('other_logistics', 'warehouse executive'), ('other_logistics', 'supply chain'),
        ('other_logistics', 'logistics coordinator'), ('other_logistics', 'fleet manager'), ('other_logistics', 'courier boy'),
        ('other_retail', 'store manager'), ('other_retail', 'retail sales'), ('other_retail', 'merchandiser'),
        ('other_retail', 'cashier'), ('other_retail', 'billing executive'), ('other_retail', 'shop assistant'),
        ('other_retail', 'visual merchandiser'), ('other_retail', 'store keeper'), ('other_retail', 'inventory manager'),
        ('other_hospitality', 'chef'), ('other_hospitality', 'cook'), ('other_hospitality', 'kitchen helper'),
        ('other_hospitality', 'waiter'), ('other_hospitality', 'housekeeping'), ('other_hospitality', 'room attendant'),
        ('other_hospitality', 'front desk'), ('other_hospitality', 'hotel manager'), ('other_hospitality', 'restaurant manager'),
        ('other_security', 'security guard'), ('other_security', 'security officer'), ('other_security', 'security supervisor'),
        ('other_security', 'cctv operator'), ('other_security', 'safety officer'), ('other_security', 'fire safety'),
        ('other_trades', 'electrician'), ('other_trades', 'plumber'), ('other_trades', 'carpenter'),
        ('other_trades', 'welder'), ('other_trades', 'fitter'), ('other_trades', 'machinist'),
        ('other_trades', 'technician'), ('other_trades', 'mechanic'), ('other_trades', 'painter'),
        ('other_trades', 'mason'), ('other_trades', 'ac technician'), ('other_trades', 'refrigeration technician'),
        ('other_beauty', 'beautician'), ('other_beauty', 'hair stylist'), ('other_beauty', 'makeup artist'),
        ('other_beauty', 'nail technician'), ('other_beauty', 'spa therapist'), ('other_beauty', 'massage therapist'),
        ('other_media', 'photographer'), ('other_media', 'videographer'), ('other_media', 'video editor'),
        ('other_media', 'graphic designer'), ('other_media', 'animator'), ('other_media', 'journalist'),
        ('other_media', 'news anchor'), ('other_media', 'content creator'), ('other_media', 'youtuber'),
        ('other_agriculture', 'agriculture'), ('other_agriculture', 'farming'), ('other_agriculture', 'horticulture'),
        ('other_agriculture', 'food technology'), ('other_agriculture', 'dairy technology'), ('other_agriculture', 'fisheries'),
    ]
    
    added = 0
    for category, keyword in keywords_data:
        if not ScrapeKeyword.query.filter_by(keyword=keyword).first():
            db.session.add(ScrapeKeyword(category=category, keyword=keyword))
            added += 1
    
    db.session.commit()
    print(f"✅ {added} keywords added")
    return added


def seed_locations():
    """50+ Indian Locations"""
    locations_data = [
        # Metro Cities
        ('Mumbai', 1), ('Delhi', 1), ('Bangalore', 1), ('Hyderabad', 1),
        ('Chennai', 1), ('Kolkata', 1), ('Pune', 1), ('Ahmedabad', 1),
        # Tier 1 Cities
        ('Jaipur', 1), ('Lucknow', 1), ('Indore', 1), ('Bhopal', 1),
        ('Chandigarh', 1), ('Kochi', 1), ('Coimbatore', 1), ('Nagpur', 1),
        ('Surat', 2), ('Vadodara', 2), ('Noida', 1), ('Gurgaon', 1),
        ('Bhubaneswar', 2), ('Patna', 2), ('Ranchi', 2), ('Visakhapatnam', 2),
        # Tier 2 Cities
        ('Dehradun', 2), ('Guwahati', 2), ('Thiruvananthapuram', 2), ('Mysore', 2),
        ('Mangalore', 2), ('Madurai', 2), ('Vijayawada', 2), ('Raipur', 2),
        ('Jodhpur', 2), ('Agra', 2), ('Varanasi', 2), ('Allahabad', 2),
        ('Kanpur', 2), ('Meerut', 2), ('Ludhiana', 2), ('Amritsar', 2),
        ('Aurangabad', 2), ('Nashik', 2), ('Rajkot', 2), ('Jabalpur', 2),
        ('Gwalior', 2), ('Udaipur', 2), ('Jammu', 2), ('Shimla', 2),
        # Special
        ('India', 1), ('Remote', 1), ('Work from Home', 1),
        ('Anywhere in India', 2), ('Multiple Locations', 3),
    ]
    
    added = 0
    for location, priority in locations_data:
        if not ScrapeLocation.query.filter_by(location=location).first():
            db.session.add(ScrapeLocation(location=location, priority=priority))
            added += 1
    
    db.session.commit()
    print(f"✅ {added} locations added")
    return added


def seed_designations():
    """50+ Common Designations"""
    designations_data = [
        # IT Designations
        ('it', 'Software Developer'), ('it', 'Senior Software Engineer'), ('it', 'Tech Lead'),
        ('it', 'Full Stack Developer'), ('it', 'Frontend Developer'), ('it', 'Backend Developer'),
        ('it', 'DevOps Engineer'), ('it', 'Cloud Architect'), ('it', 'Data Scientist'),
        ('it', 'Machine Learning Engineer'), ('it', 'AI Engineer'), ('it', 'Cybersecurity Analyst'),
        ('it', 'QA Engineer'), ('it', 'Database Administrator'), ('it', 'System Administrator'),
        ('it', 'Network Engineer'), ('it', 'IT Support Engineer'), ('it', 'Mobile App Developer'),
        ('it', 'UI Designer'), ('it', 'UX Designer'),
        # Management
        ('management', 'Project Manager'), ('management', 'Product Manager'), ('management', 'Business Analyst'),
        ('management', 'Scrum Master'), ('management', 'Program Manager'), ('management', 'Operations Manager'),
        # HR
        ('hr', 'HR Manager'), ('hr', 'Recruiter'), ('hr', 'Talent Acquisition Specialist'),
        # Finance
        ('finance', 'Accountant'), ('finance', 'Finance Manager'), ('finance', 'Financial Analyst'),
        ('finance', 'Chartered Accountant'), ('finance', 'Banking Officer'),
        # Sales & Marketing
        ('sales', 'Sales Executive'), ('sales', 'Business Development Manager'), ('sales', 'Area Sales Manager'),
        ('marketing', 'Marketing Manager'), ('marketing', 'Digital Marketing Specialist'), ('marketing', 'Content Writer'),
        # Healthcare
        ('healthcare', 'Doctor'), ('healthcare', 'Nurse'), ('healthcare', 'Pharmacist'),
        ('healthcare', 'Medical Officer'), ('healthcare', 'Lab Technician'),
        # Education
        ('education', 'Teacher'), ('education', 'Professor'), ('education', 'Principal'),
        # Engineering
        ('engineering', 'Civil Engineer'), ('engineering', 'Mechanical Engineer'), ('engineering', 'Electrical Engineer'),
        # Other
        ('other', 'Data Entry Operator'), ('other', 'Customer Service Representative'), ('other', 'Delivery Executive'),
        ('other', 'Security Guard'), ('other', 'Electrician'), ('other', 'Beautician'),
    ]
    
    added = 0
    for category, designation in designations_data:
        if not ScrapeDesignation.query.filter_by(designation=designation).first():
            db.session.add(ScrapeDesignation(category=category, designation=designation))
            added += 1
    
    db.session.commit()
    print(f"✅ {added} designations added")
    return added


if __name__ == '__main__':
    seed_all()