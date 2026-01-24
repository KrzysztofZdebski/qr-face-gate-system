"""
Script to automatically delete old failed attempt images based on retention policy.
This ensures GDPR compliance by automatically removing personal data after retention period.

Run this script periodically (e.g., via cron job) or call it from your application.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config.config import get_config
from db.db import db
from db.models import EntryAttempt

app = Flask(__name__)
app.config.from_object(get_config())

# Make upload folder absolute
if not os.path.isabs(app.config['UPLOAD_FOLDER']):
    app_root = os.path.dirname(os.path.abspath(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(app_root, app.config['UPLOAD_FOLDER'])

with app.app_context():
    db.init_app(app)
    
    retention_days = app.config.get('IMAGE_RETENTION_DAYS', 90)
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    print(f"Cleaning up images older than {retention_days} days (before {cutoff_date.strftime('%Y-%m-%d')})")
    print()
    
    # Get upload folder
    upload_folder = app.config['UPLOAD_FOLDER']
    failed_attempts_folder = os.path.join(upload_folder, 'failed_attempts')
    
    if not os.path.exists(failed_attempts_folder):
        print("No failed_attempts folder found. Nothing to clean up.")
        sys.exit(0)
    
    # Find old attempts
    old_attempts = EntryAttempt.query.filter(
        EntryAttempt.attempted_at < cutoff_date,
        EntryAttempt.image_path.isnot(None)
    ).all()
    
    if not old_attempts:
        print("No old images to delete.")
        sys.exit(0)
    
    print(f"Found {len(old_attempts)} old attempts with images")
    print()
    
    deleted_count = 0
    not_found_count = 0
    error_count = 0
    
    for attempt in old_attempts:
        if not attempt.image_path:
            continue
        
        image_path = os.path.join(upload_folder, attempt.image_path)
        
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                # Clear image_path in database
                attempt.image_path = None
                db.session.commit()
                deleted_count += 1
                print(f"✓ Deleted: {os.path.basename(image_path)} (Attempt ID: {attempt.id}, Date: {attempt.attempted_at.strftime('%Y-%m-%d')})")
            except Exception as e:
                print(f"✗ Error deleting {image_path}: {e}")
                error_count += 1
        else:
            # File doesn't exist, but clear database reference
            attempt.image_path = None
            db.session.commit()
            not_found_count += 1
    
    print()
    print("=" * 50)
    print(f"Summary:")
    print(f"  Images deleted: {deleted_count}")
    print(f"  Database references cleared: {deleted_count + not_found_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total processed: {len(old_attempts)}")
    print()
    print(f"✓ Cleanup completed. Images older than {retention_days} days have been removed.")
