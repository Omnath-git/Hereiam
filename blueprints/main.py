# blueprints/main.py
from flask import Blueprint, render_template, request, send_from_directory, flash, redirect, url_for
from models import db, User, Job

main_bp = Blueprint('main', __name__)

# @main_bp.route('/')
# def index():
#     filter_domain = request.args.get('domain', '')
#     filter_state = request.args.get('state', '')
#     filter_city = request.args.get('city', '')
#     filter_salary = request.args.get('salary', '')
#     filter_notice = request.args.get('notice', '')
#     tab = request.args.get('tab', 'professionals')
    
#     professionals_query = User.query.filter_by(profile_complete=True, user_type='jobseeker')
#     if filter_domain:
#         professionals_query = professionals_query.filter_by(domain=filter_domain)
#     if filter_state:
#         professionals_query = professionals_query.filter_by(state=filter_state)
#     if filter_city:
#         professionals_query = professionals_query.filter_by(city=filter_city)
#     if filter_salary:
#         professionals_query = professionals_query.filter(User.expected_salary.contains(filter_salary))
#     if filter_notice:
#         professionals_query = professionals_query.filter_by(notice_period=filter_notice)
    
#     professionals = professionals_query.all()
    
#     jobs_query = Job.query.filter_by(is_active=True)
#     jobs = jobs_query.order_by(Job.posted_date.desc()).all()
    
#     domains = db.session.query(User.domain).filter(User.domain != '').distinct().all()
#     states = db.session.query(User.state).filter(User.state != '').distinct().all()
#     cities = db.session.query(User.city).filter(User.city != '').distinct().all()
    
#     salary_ranges = ['0-3 LPA', '3-6 LPA', '6-10 LPA', '10-15 LPA', '15-25 LPA', '25-50 LPA', '50+ LPA']
#     notice_periods = ['Immediate', '15 Days', '30 Days', '60 Days', '90 Days', '90+ Days']
    
#     return render_template('index.html',
#                          professionals=professionals, jobs=jobs,
#                          domains=domains, states=states, cities=cities,
#                          salary_ranges=salary_ranges, notice_periods=notice_periods,
#                          current_domain=filter_domain, current_state=filter_state,
#                          current_city=filter_city, current_salary=filter_salary,
#                          current_notice=filter_notice, active_tab=tab)

@main_bp.route('/profile/<path:filename>')
def view_profile(filename):
    from flask import current_app
    try:
        return send_from_directory(current_app.config['PROFILES_FOLDER'], filename)
    except Exception:
        flash('Profile not found!', 'error')
        return redirect(url_for('main.index'))
# blueprints/main.py

@main_bp.route('/')
def index():
    filter_domain = request.args.get('domain', '')
    filter_state = request.args.get('state', '')
    filter_city = request.args.get('city', '')
    filter_salary = request.args.get('salary', '')
    filter_notice = request.args.get('notice', '')
    filter_experience = request.args.get('experience', '')
    filter_job_type = request.args.get('job_type', '')
    tab = request.args.get('tab', 'professionals')
    
    # ⭐ GET DYNAMIC FILTER VALUES FROM DATABASE
    
    # For Professionals Tab
    professionals_query = User.query.filter_by(profile_complete=True, user_type='jobseeker')
    
    # Get unique values from actual data
    prof_domains = db.session.query(User.domain)\
        .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.domain != '')\
        .distinct().order_by(User.domain).all()
    
    prof_states = db.session.query(User.state)\
        .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.state != '')\
        .distinct().order_by(User.state).all()
    
    prof_cities = db.session.query(User.city)\
        .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.city != '')\
        .distinct().order_by(User.city).all()
    
    prof_salaries = db.session.query(User.expected_salary)\
        .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.expected_salary != '')\
        .distinct().order_by(User.expected_salary).all()
    
    prof_notices = db.session.query(User.notice_period)\
        .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.notice_period != '')\
        .distinct().order_by(User.notice_period).all()
    
    # For Jobs Tab
    jobs_query = Job.query.filter_by(is_active=True)
    
    job_domains = db.session.query(Job.title)\
        .filter(Job.is_active == True, Job.title != '')\
        .distinct().order_by(Job.title).all()
    
    job_states = db.session.query(Job.location)\
        .filter(Job.is_active == True, Job.location != '')\
        .distinct().order_by(Job.location).all()
    
    job_types = db.session.query(Job.job_type)\
        .filter(Job.is_active == True, Job.job_type != '')\
        .distinct().order_by(Job.job_type).all()
    
    job_experiences = db.session.query(Job.experience_required)\
        .filter(Job.is_active == True, Job.experience_required != '')\
        .distinct().order_by(Job.experience_required).all()
    
    # Apply filters for Professionals
    if filter_domain:
        professionals_query = professionals_query.filter_by(domain=filter_domain)
    if filter_state:
        professionals_query = professionals_query.filter_by(state=filter_state)
    if filter_city:
        professionals_query = professionals_query.filter_by(city=filter_city)
    if filter_salary:
        professionals_query = professionals_query.filter_by(expected_salary=filter_salary)
    if filter_notice:
        professionals_query = professionals_query.filter_by(notice_period=filter_notice)
    
    professionals = professionals_query.all()
    
    # Apply filters for Jobs
    if filter_domain:
        jobs_query = jobs_query.filter(Job.title.contains(filter_domain) | Job.skills_required.contains(filter_domain))
    if filter_state:
        jobs_query = jobs_query.filter(Job.location.contains(filter_state))
    if filter_city:
        jobs_query = jobs_query.filter(Job.location.contains(filter_city))
    if filter_job_type:
        jobs_query = jobs_query.filter_by(job_type=filter_job_type)
    if filter_experience:
        jobs_query = jobs_query.filter_by(experience_required=filter_experience)
    
    jobs = jobs_query.order_by(Job.posted_date.desc()).all()
    
    return render_template('index.html',
                         professionals=professionals,
                         jobs=jobs,
                         # ⭐ Dynamic filter values
                         prof_domains=prof_domains,
                         prof_states=prof_states,
                         prof_cities=prof_cities,
                         prof_salaries=prof_salaries,
                         prof_notices=prof_notices,
                         job_domains=job_domains,
                         job_states=job_states,
                         job_types=job_types,
                         job_experiences=job_experiences,
                         # Current filters
                         current_domain=filter_domain,
                         current_state=filter_state,
                         current_city=filter_city,
                         current_salary=filter_salary,
                         current_notice=filter_notice,
                         current_job_type=filter_job_type,
                         current_experience=filter_experience,
                         active_tab=tab)