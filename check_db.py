import sqlite3
import os

databases = [
    'backend.db',
    'backend_backup_pre_neon.db',
    'backend_qa.db'
]

for db_file in databases:
    print(f"\n=== {db_file} ===")
    if os.path.exists(db_file):
        size_kb = os.path.getsize(db_file) / 1024
        print(f"Size: {size_kb:.1f}KB")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Check for product/products table
            for table_name in ['product', 'products', 'Product']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name}: {count} records")
                    break
                except:
                    pass
            
            conn.close()
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print("NOT FOUND")
