# migrate_db.py - V5 फोल्डर में सेव करें और रन करें
import sqlite3
import os

DB_PATH = 'instance//database.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("❌ database.db not found!")
        return
    
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    
    # मौजूदा कॉलम्स चेक करें
    cursor.execute("PRAGMA table_info(user)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    print(f"📋 Existing columns: {len(existing_columns)}")
    
    # ⭐ नए कॉलम्स
    new_columns = [
        ("show_email", "BOOLEAN", "0"),
        ("show_mobile", "BOOLEAN", "0"),
    ]
    
    for col_name, col_type, default_val in new_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
                print(f"✅ Added: {col_name}")
            except Exception as e:
                print(f"⚠️ Error adding {col_name}: {e}")
        else:
            print(f"⏭️ Already exists: {col_name}")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete! Run: python app.py")

if __name__ == '__main__':
    migrate()