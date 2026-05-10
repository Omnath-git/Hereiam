"""
=============================================================================
District Data Seeder - Import from district_list.csv
=============================================================================
"""

import csv
import os
from app import create_app
from models import db, District

def seed_districts():
    """CSV से districts import करें"""
    app = create_app()
    
    csv_path = 'district_list.csv'
    
    if not os.path.exists(csv_path):
        print(f"❌ {csv_path} not found!")
        print("Please place district_list.csv in the project folder.")
        return
    
    with app.app_context():
        # Create table if not exists
        db.create_all()
        
        # Clear existing data
        District.query.delete()
        db.session.commit()
        
        added = 0
        errors = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                district_name = row.get('District Names', '').strip()
                state_name = row.get('State UT', '').strip()
                
                if district_name and state_name:
                    try:
                        db.session.add(District(
                            district_name=district_name,
                            state_name=state_name
                        ))
                        added += 1
                    except Exception as e:
                        errors += 1
                        print(f"⚠️ Error: {district_name} - {e}")
        
        db.session.commit()
        
        # Show stats
        states = db.session.query(District.state_name).distinct().count()
        districts = District.query.count()
        
        print("\n" + "="*50)
        print(f"✅ DISTRICTS IMPORTED!")
        print(f"   States/UTs: {states}")
        print(f"   Districts: {districts}")
        print(f"   Errors: {errors}")
        print("="*50)


if __name__ == '__main__':
    seed_districts()