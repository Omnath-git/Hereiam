# blueprints/locations.py
from flask import Blueprint, jsonify, request
from models import db, District

locations_bp = Blueprint('locations', __name__)


@locations_bp.route('/api/states')
def get_states():
    """Get all unique states"""
    states = db.session.query(District.state_name)\
        .distinct()\
        .order_by(District.state_name)\
        .all()
    
    return jsonify({
        'states': [s[0] for s in states]
    })


@locations_bp.route('/api/districts/<state>')
def get_districts(state):
    """Get districts for a specific state"""
    districts = District.query\
        .filter_by(state_name=state)\
        .order_by(District.district_name)\
        .all()
    
    return jsonify({
        'state': state,
        'districts': [d.district_name for d in districts]
    })


@locations_bp.route('/api/all-states-districts')
def get_all_states_districts():
    """Get all states with their districts"""
    from collections import defaultdict
    
    data = defaultdict(list)
    districts = District.query.order_by(District.state_name, District.district_name).all()
    
    for d in districts:
        data[d.state_name].append(d.district_name)
    
    return jsonify(dict(data))