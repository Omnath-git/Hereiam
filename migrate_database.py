"""
=============================================================================
Database Migration Script
=============================================================================
Migrates data from old database.db to new main.db + jobs.db
=============================================================================
"""

import sqlite3
import os
import shutil
from datetime import datetime

# Database paths
OLD_DB = 'instance/database.db'  # पुराना single database
NEW_MAIN_DB = 'instance/main.db'  # नया main database (users, admin, donations, scraper config)
NEW_JOBS_DB = 'instance/jobs.db'  # नया jobs database


def backup_old_database():
    """पुराने database का backup बनाएं"""
    if os.path.exists(OLD_DB):
        backup_name = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(OLD_DB, backup_name)
        print(f"✅ Backup created: {backup_name}")
        return True
    return False


def get_table_columns(cursor, table_name):
    """टेबल के columns की लिस्ट प्राप्त करें"""
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    return [col[1] for col in cursor.fetchall()]


def migrate_table(old_cursor, new_cursor, table_name, skip_tables=None):
    """एक टेबल का डेटा माइग्रेट करें"""
    if skip_tables and table_name in skip_tables:
        return 0
    
    try:
        # Check if table exists in old DB
        old_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not old_cursor.fetchone():
            print(f"  ⏭️ Table '{table_name}' not found in old DB, skipping...")
            return 0
        
        # Get all data from old table
        old_cursor.execute(f"SELECT * FROM '{table_name}'")
        rows = old_cursor.fetchall()
        
        if not rows:
            print(f"  ℹ️ Table '{table_name}' is empty, skipping...")
            return 0
        
        # Get column names
        columns = get_table_columns(old_cursor, table_name)
        
        # Check if table exists in new DB, create if not
        new_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not new_cursor.fetchone():
            # Create table with same structure
            old_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = old_cursor.fetchone()[0]
            new_cursor.execute(create_sql)
            print(f"  📝 Created table '{table_name}' in new DB")
        
        # Get new table columns
        new_columns = get_table_columns(new_cursor, table_name)
        
        # Find common columns
        common_columns = [col for col in columns if col in new_columns]
        
        if not common_columns:
            print(f"  ⚠️ No common columns for '{table_name}'")
            return 0
        
        # Insert data
        placeholders = ','.join(['?' for _ in common_columns])
        cols_str = ','.join(common_columns)
        
        inserted = 0
        skipped = 0
        
        for row in rows:
            try:
                # Get values for common columns
                values = [row[columns.index(col)] for col in common_columns]
                
                # Check for duplicate (by first column usually id)
                if 'id' in common_columns:
                    id_idx = common_columns.index('id')
                    new_cursor.execute(f"SELECT id FROM '{table_name}' WHERE id = ?", (values[id_idx],))
                    if new_cursor.fetchone():
                        skipped += 1
                        continue
                
                new_cursor.execute(f"INSERT INTO '{table_name}' ({cols_str}) VALUES ({placeholders})", values)
                inserted += 1
            except Exception as e:
                skipped += 1
        
        print(f"  ✅ '{table_name}': {inserted} inserted, {skipped} skipped, {len(rows)} total")
        return inserted
        
    except Exception as e:
        print(f"  ❌ Error migrating '{table_name}': {str(e)[:100]}")
        return 0


def migrate_all():
    """पूरा माइग्रेशन प्रोसेस"""
    print("\n" + "="*70)
    print("🔄 DATABASE MIGRATION: database.db → main.db + jobs.db")
    print("="*70)
    
    # Check if old database exists
    if not os.path.exists(OLD_DB):
        print(f"\n❌ Old database '{OLD_DB}' not found!")
        print("   Nothing to migrate. Run 'python app.py' to create new databases.")
        return
    
    # Backup old database
    print("\n📦 Step 1: Backing up old database...")
    backup_old_database()
    
    # Connect to old database
    print("\n📂 Step 2: Connecting to old database...")
    old_conn = sqlite3.connect(OLD_DB)
    old_cursor = old_conn.cursor()
    
    # Get list of all tables in old DB
    old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    old_tables = [t[0] for t in old_cursor.fetchall()]
    print(f"   Tables found: {', '.join(old_tables)}")
    
    # Connect to new main database
    print("\n📂 Step 3: Connecting to new main database...")
    main_conn = sqlite3.connect(NEW_MAIN_DB)
    main_cursor = main_conn.cursor()
    
    # Connect to new jobs database
    print("\n📂 Step 4: Connecting to new jobs database...")
    jobs_conn = sqlite3.connect(NEW_JOBS_DB)
    jobs_cursor = jobs_conn.cursor()
    
    # ⭐ Define which tables go to which database
    MAIN_TABLES = ['user', 'admin', 'donation', 'scrape_website', 'scrape_keyword', 'scrape_location', 'scrape_designation']
    JOBS_TABLES = ['job']
    
    total_migrated = 0
    
    # Migrate to main.db
    print("\n" + "="*50)
    print("📤 Migrating to main.db...")
    print("="*50)
    for table in MAIN_TABLES:
        count = migrate_table(old_cursor, main_cursor, table)
        total_migrated += count
    
    # Migrate to jobs.db
    print("\n" + "="*50)
    print("📤 Migrating to jobs.db...")
    print("="*50)
    for table in JOBS_TABLES:
        count = migrate_table(old_cursor, jobs_cursor, table)
        total_migrated += count
    
    # Migrate any remaining tables to main.db
    print("\n" + "="*50)
    print("📤 Migrating remaining tables to main.db...")
    print("="*50)
    for table in old_tables:
        if table not in MAIN_TABLES and table not in JOBS_TABLES and table != 'sqlite_sequence':
            count = migrate_table(old_cursor, main_cursor, table)
            total_migrated += count
    
    # Commit and close
    main_conn.commit()
    jobs_conn.commit()
    old_conn.close()
    main_conn.close()
    jobs_conn.close()
    
    print("\n" + "="*70)
    print(f"✅ MIGRATION COMPLETE!")
    print(f"   Total records migrated: {total_migrated}")
    print(f"   Main database: {NEW_MAIN_DB}")
    print(f"   Jobs database: {NEW_JOBS_DB}")
    print(f"   Old database preserved: {OLD_DB}")
    print("="*70)
    print("\n🚀 Now run: python app.py")


def show_old_stats():
    """पुराने database के आंकड़े दिखाएं"""
    if not os.path.exists(OLD_DB):
        print(f"❌ {OLD_DB} not found!")
        return
    
    conn = sqlite3.connect(OLD_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("\n📊 OLD DATABASE STATISTICS:")
    print("-"*40)
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
            count = cursor.fetchone()[0]
            print(f"  {table:<30} : {count:>6} records")
        except:
            print(f"  {table:<30} : (error)")
    
    conn.close()


def show_new_stats():
    """नए databases के आंकड़े दिखाएं"""
    print("\n📊 NEW DATABASES STATISTICS:")
    
    for db_name, db_file in [('main.db', NEW_MAIN_DB), ('jobs.db', NEW_JOBS_DB)]:
        if os.path.exists(db_file):
            print(f"\n  {db_name}:")
            print("  " + "-"*35)
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                    count = cursor.fetchone()[0]
                    print(f"    {table:<28} : {count:>6} records")
                except:
                    print(f"    {table:<28} : (error)")
            conn.close()
        else:
            print(f"\n  {db_name}: (not created yet)")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats-old':
            show_old_stats()
        elif sys.argv[1] == '--stats-new':
            show_new_stats()
        elif sys.argv[1] == '--stats':
            show_old_stats()
            show_new_stats()
        else:
            print("Usage:")
            print("  python migrate_database.py           # Run migration")
            print("  python migrate_database.py --stats   # Show statistics")
    else:
        # Show stats first
        show_old_stats()
        
        print("\n" + "="*70)
        choice = input("\nStart migration? (y/n): ").lower()
        if choice == 'y':
            migrate_all()
            print("\n📊 After migration:")
            show_new_stats()
        else:
            print("Migration cancelled.")


# ============================================================
# USAGE:
# ============================================================
# python migrate_database.py           # Full migration
# python migrate_database.py --stats   # Show old and new stats
# python migrate_database.py --stats-old  # Show old DB stats only
# python migrate_database.py --stats-new  # Show new DB stats only