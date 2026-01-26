import pytest
import json
from io import BytesIO
from PIL import Image

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'QR Face Gate System' in response.data


def test_verify_route_success(client, mocker):
    # Setup: Create a user
    with client.application.app_context():
        from db.models import User
        from db.db import db
        user = User(name="Test", face_encoding=json.dumps([0.1, 0.2]), qr_code_data="1")
        db.session.add(user)
        db.session.commit()
    
    # Mock face recognition
    mocker.patch('face_recognition.load_image_file', return_value=Image.new('RGB', (100, 100)))
    mocker.patch('face_recognition.face_encodings', return_value=[[0.1, 0.2]])
    mocker.patch('face_recognition.face_distance', return_value=[0.3])
    
    data = {
        'qr_code_data': '1',
        'face_image': (BytesIO(b'fake image'), 'test.jpg')
    }
    response = client.post('/verify', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['match'] is True

def test_verify_route_failure(client, mocker):
    # Similar to success, but with high distance
    mocker.patch('face_recognition.face_distance', return_value=[0.8])
    data = {'qr_code_data': '1', 'face_image': (BytesIO(b'fake'), 'test.jpg')}
    response = client.post('/verify', data=data, content_type='multipart/form-data')
    json_data = json.loads(response.data)
    assert json_data['match'] is False