from flask import Flask

def initialize_db(app: Flask):
    from db.db import db
    from db.models import User, EntryAttempt  # Import EntryAttempt to ensure it's registered
    with app.app_context():
        try:
            
            db.init_app(app)
            db.create_all()
            print("Sukces! Tabele utworzone.")
            
            # Check and add image_path column if it doesn't exist (migration)
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                
                # Check if entry_attempts table exists
                if 'entry_attempts' in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns('entry_attempts')]
                    
                    if 'image_path' not in columns:
                        print("Adding image_path column to entry_attempts table...")
                        with db.engine.connect() as conn:
                            conn.execute(text("ALTER TABLE entry_attempts ADD COLUMN image_path VARCHAR(500)"))
                            conn.commit()
                        print("Migration completed: image_path column added.")
                    else:
                        print("Migration check: image_path column already exists.")
            except Exception as migration_error:
                print(f"Migration check/execution error (may be harmless if column already exists): {migration_error}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"Error creating database: {e}")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'N/A'}")
            import time
            print("Waiting for database to be ready...")
            time.sleep(2)
            # Retry once
            try:
                db.create_all()
                # Try migration again after retry
                try:
                    from sqlalchemy import inspect, text
                    inspector = inspect(db.engine)
                    
                    # Check if entry_attempts table exists
                    if 'entry_attempts' in inspector.get_table_names():
                        columns = [col['name'] for col in inspector.get_columns('entry_attempts')]
                        
                        if 'image_path' not in columns:
                            print("Adding image_path column to entry_attempts table...")
                            with db.engine.connect() as conn:
                                conn.execute(text("ALTER TABLE entry_attempts ADD COLUMN image_path VARCHAR(500)"))
                                conn.commit()
                            print("Migration completed: image_path column added.")
                        else:
                            print("Migration check: image_path column already exists.")
                except Exception as migration_error:
                    print(f"Migration check/execution error (may be harmless if column already exists): {migration_error}")
                    import traceback
                    traceback.print_exc()
            except Exception as e2:
                print(f"Retry failed: {e2}")
                raise
def initialize_route(app:Flask):
    from modules.routes import base_bp
    app.register_blueprint(base_bp)