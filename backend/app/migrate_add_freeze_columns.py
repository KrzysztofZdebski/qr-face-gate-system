"""
Migration script to add freeze-related columns to users table.
Run this script if the automatic migration doesn't work.
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config.config import get_config
from db.db import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(get_config())

with app.app_context():
    db.init_app(app)
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Check if users table exists
        if 'users' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            missing_columns = []
            if 'is_frozen' not in columns:
                missing_columns.append('is_frozen')
            if 'frozen_until' not in columns:
                missing_columns.append('frozen_until')
            if 'freeze_reason' not in columns:
                missing_columns.append('freeze_reason')
            
            if missing_columns:
                print(f"Adding columns to users table: {', '.join(missing_columns)}...")
                with db.engine.connect() as conn:
                    if 'is_frozen' in missing_columns:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_frozen BOOLEAN DEFAULT FALSE NOT NULL"))
                        print("  ✓ Added is_frozen column")
                    
                    if 'frozen_until' in missing_columns:
                        conn.execute(text("ALTER TABLE users ADD COLUMN frozen_until TIMESTAMP"))
                        print("  ✓ Added frozen_until column")
                    
                    if 'freeze_reason' in missing_columns:
                        conn.execute(text("ALTER TABLE users ADD COLUMN freeze_reason VARCHAR(500)"))
                        print("  ✓ Added freeze_reason column")
                    
                    conn.commit()
                print("✓ Migration completed: All freeze-related columns added successfully!")
            else:
                print("✓ All freeze-related columns already exist. No migration needed.")
        else:
            print("⚠ users table doesn't exist yet. Run the app first to create tables.")
    except Exception as e:
        print(f"✗ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
