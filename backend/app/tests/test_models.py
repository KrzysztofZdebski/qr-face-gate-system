import pytest
from db.models import User, EntryAttempt
from db.db import db
import json
from conftest import get_face_encoding_from_test_image

def test_user_creation(app):
    with app.app_context():
        face_encoding = get_face_encoding_from_test_image("Colin_Farrell")
        user = User(name="Test User", face_encoding=json.dumps(face_encoding), qr_code_data="123")
        db.session.add(user)
        db.session.commit()
        assert user.id is not None
        assert user.name == "Test User"

def test_entry_attempt_creation(app):
    with app.app_context():
        attempt = EntryAttempt(qr_code_data="123", success=True, face_distance=0.3)
        db.session.add(attempt)
        db.session.commit()
        assert attempt.id is not None
        assert attempt.success is True