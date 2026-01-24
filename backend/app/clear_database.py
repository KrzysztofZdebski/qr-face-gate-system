import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config.config import get_config
from db.db import db
from db.models import User, EntryAttempt

app = Flask(__name__)
app.config.from_object(get_config())

with app.app_context():
    db.init_app(app)
    
    # Clear all data
    EntryAttempt.query.delete()
    User.query.delete()
    db.session.commit()
    
    print("✓ Database cleared successfully!")