import sys
sys.path.insert(0, '/app')
import pytest
from flask import Flask
from db.db import db
import face_recognition
from pathlib import Path
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