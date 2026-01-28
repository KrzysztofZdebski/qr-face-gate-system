import pytest
import json
from io import BytesIO
from pathlib import Path
from conftest import get_face_encoding_from_test_image

TEST_IMAGES_DIR = Path(__file__).parent / "test_images"

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'QR Face Gate System' in response.data


def test_verify_route_success(client):
    # Setup: Create a user with real face encoding
    with client.application.app_context():
        from db.models import User
        from db.db import db
        face_encoding = get_face_encoding_from_test_image("Colin_Farrell")
        user = User(name="Test", face_encoding=json.dumps(face_encoding), qr_code_data="1")
        db.session.add(user)
        db.session.commit()
    
    # Use real face image from test_images
    image_path = TEST_IMAGES_DIR / "Colin_Farrell" / "Colin_Farrell_0001.jpg"
    
    with open(image_path, 'rb') as f:
        data = {
            'qr_code_data': '1',
            'face_image': (BytesIO(f.read()), 'test.jpg')
        }
        response = client.post('/verify', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['match'] is True