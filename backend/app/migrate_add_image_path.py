"""
Migration script to add image_path column to entry_attempts table.
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
        
        # Check if entry_attempts table exists
        if 'entry_attempts' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('entry_attempts')]
            
            if 'image_path' not in columns:
                print("Adding image_path column to entry_attempts table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE entry_attempts ADD COLUMN image_path VARCHAR(500)"))
                    conn.commit()
                print("✓ Migration completed: image_path column added successfully!")
            else:
                print("✓ image_path column already exists. No migration needed.")
        else:
            print("⚠ entry_attempts table doesn't exist yet. Run the app first to create tables.")
    except Exception as e:
        print(f"✗ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
