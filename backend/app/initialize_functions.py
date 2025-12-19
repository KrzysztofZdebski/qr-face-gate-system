from flask import Flask
from db.db import db

def initialize_db(app: Flask):
    with app.app_context():
        try:
            db.init_app(app)
            db.create_all()
            print("Sukces! Tabele utworzone.")
        except Exception as e:
            print(f"Error creating database: {e}")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'N/A'}")
            import time
            print("Waiting for database to be ready...")
            time.sleep(2)
            # Retry once
            try:
                db.create_all()
            except Exception as e2:
                print(f"Retry failed: {e2}")
                raise
