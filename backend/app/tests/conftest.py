import sys
from pathlib import Path

# Ensure imports work when running tests locally (not in container).
# Add the `backend/app` directory to sys.path so modules like `db.db`
# and `modules.routes` can be imported the same way as in production.
APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import pytest
from flask import Flask
from db.db import db
import face_recognition
import json

# Path to test images
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"

def get_face_encoding_from_test_image(person_name: str = "Colin_Farrell"):
    """
    Load a real face encoding from test images.
    Returns face encoding as a list, or None if image not found.
    """
    person_dir = TEST_IMAGES_DIR / person_name
    if person_dir.exists():
        images = list(person_dir.glob("*.jpg"))
        if images:
            image_path = images[0]
            image = face_recognition.load_image_file(str(image_path))
            face_encodings = face_recognition.face_encodings(image)
            if len(face_encodings) > 0:
                return face_encodings[0].tolist()
    return [0.1, 0.2]  # Fallback

@pytest.fixture
def app():
    # Project root (two levels up from `backend/app/tests`)
    PROJECT_ROOT = Path(__file__).resolve().parents[3]

    # Use local template/static folders so tests run outside container
    templates_folder = str(PROJECT_ROOT / 'templates')
    static_folder = str(PROJECT_ROOT / 'static')

    app = Flask('app', template_folder=templates_folder, static_folder=static_folder)
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