import sys
sys.path.insert(0, '/app')
import pytest
from flask import Flask
from db.db import db

@pytest.fixture
def app():
    app = Flask('app', template_folder='/app/templates', static_folder='/app/static')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    from initialize_functions import initialize_db, initialize_route
    from db.db import db
    try:
        db.engine.dispose()
        db.session.close()
    except:
        pass
    initialize_db(app)
    initialize_route(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()