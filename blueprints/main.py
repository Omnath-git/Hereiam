# blueprints/main.py

from flask import Blueprint, render_template, request, send_from_directory, flash, redirect, url_for
from models import db, User, Job, District

main_bp = Blueprint('main', __name__)


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
    
    try:
        # ⭐ DYNAMIC FILTER VALUES
        professionals_query = User.query.filter_by(profile_complete=True, user_type='jobseeker')
        
        prof_domains = db.session.query(User.domain)\
            .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.domain != '')\
            .distinct().order_by(User.domain).all()
        
        prof_salaries = db.session.query(User.expected_salary)\
            .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.expected_salary != '')\
            .distinct().order_by(User.expected_salary).all()
        
        prof_notices = db.session.query(User.notice_period)\
            .filter(User.profile_complete == True, User.user_type == 'jobseeker', User.notice_period != '')\
            .distinct().order_by(User.notice_period).all()
        
        # States from District table
        prof_states = db.session.query(District.state_name)\
            .distinct().order_by(District.state_name).all()
        
        # Cities
        if filter_state:
            prof_cities = db.session.query(District.district_name)\
                .filter(District.state_name == filter_state)\
                .order_by(District.district_name).all()
        else:
            prof_cities = db.session.query(District.district_name)\
                .distinct().order_by(District.district_name).all()
        
        # Jobs
        jobs_query = Job.query.filter_by(is_active=True)
        
        job_domains = db.session.query(Job.title)\
            .filter(Job.is_active == True, Job.title != '')\
            .distinct().order_by(Job.title).all()
        
        job_types = db.session.query(Job.job_type)\
            .filter(Job.is_active == True, Job.job_type != '')\
            .distinct().order_by(Job.job_type).all()
        
        job_experiences = db.session.query(Job.experience_required)\
            .filter(Job.is_active == True, Job.experience_required != '')\
            .distinct().order_by(Job.experience_required).all()
        
        # Apply filters
        if filter_domain:
            professionals_query = professionals_query.filter_by(domain=filter_domain)
        if filter_state:
            professionals_query = professionals_query.filter(User.state == filter_state)
        if filter_city:
            professionals_query = professionals_query.filter(User.city == filter_city)
        if filter_salary:
            professionals_query = professionals_query.filter_by(expected_salary=filter_salary)
        if filter_notice:
            professionals_query = professionals_query.filter_by(notice_period=filter_notice)
        
        professionals = professionals_query.all()
        
        if filter_domain:
            jobs_query = jobs_query.filter(
                (Job.title.ilike(f'%{filter_domain}%')) | 
                (Job.skills_required.ilike(f'%{filter_domain}%'))
            )
        if filter_state:
            jobs_query = jobs_query.filter(Job.location.ilike(f'%{filter_state}%'))
        if filter_city:
            jobs_query = jobs_query.filter(Job.location.ilike(f'%{filter_city}%'))
        if filter_job_type:
            jobs_query = jobs_query.filter_by(job_type=filter_job_type)
        if filter_experience:
            jobs_query = jobs_query.filter_by(experience_required=filter_experience)
        
        jobs = jobs_query.order_by(Job.posted_date.desc()).all()
        
        return render_template('index.html',
                             professionals=professionals,
                             jobs=jobs,
                             prof_domains=prof_domains,
                             prof_states=prof_states,
                             prof_cities=prof_cities,
                             prof_salaries=prof_salaries,
                             prof_notices=prof_notices,
                             job_domains=job_domains,
                             job_types=job_types,
                             job_experiences=job_experiences,
                             current_domain=filter_domain,
                             current_state=filter_state,
                             current_city=filter_city,
                             current_salary=filter_salary,
                             current_notice=filter_notice,
                             current_job_type=filter_job_type,
                             current_experience=filter_experience,
                             active_tab=tab)
    
    except Exception as e:
        print(f"❌ Index error: {e}")
        import traceback
        traceback.print_exc()
        flash('Something went wrong. Please try again.', 'error')
        return render_template('index.html',
                             professionals=[],
                             jobs=[],
                             prof_domains=[],
                             prof_states=[],
                             prof_cities=[],
                             prof_salaries=[],
                             prof_notices=[],
                             job_domains=[],
                             job_types=[],
                             job_experiences=[],
                             current_domain='',
                             current_state='',
                             current_city='',
                             current_salary='',
                             current_notice='',
                             current_job_type='',
                             current_experience='',
                             active_tab='professionals')


@main_bp.route('/profile/<path:filename>')
def view_profile(filename):
    from flask import current_app
    try:
        return send_from_directory(current_app.config['PROFILES_FOLDER'], filename)
    except Exception:
        flash('Profile not found!', 'error')
        return redirect(url_for('main.index'))