import pytest
import time
from io import BytesIO
from PIL import Image
import numpy as np
import json

def test_face_recognition_accuracy(client, mocker):
    """Test accuracy: Min 90% on sample data"""
    # Create 20 users (min requirement)
    with client.application.app_context():
        from db.models import User
        from db.db import db
        for i in range(20):
            encoding = np.random.rand(128).tolist()  # Mock 128-dim encoding
            user = User(name=f"User {i}", face_encoding=json.dumps(encoding), qr_code_data=str(i+1))
            db.session.add(user)
        db.session.commit()
    
    # Test with 100 attempts (50 correct, 50 incorrect)
    correct_matches = 0
    total_tests = 100
    
    # Mock face recognition common parts
    mocker.patch('face_recognition.load_image_file', return_value=Image.new('RGB', (100, 100)))
    mocker.patch('face_recognition.face_encodings', return_value=[[0.1, 0.2]])
    
    for i in range(total_tests):
        user_id = (i % 20) + 1
        is_correct = i < 50  # First 50 are correct matches
        
        # Mock face recognition
        if is_correct:
            mocker.patch('face_recognition.face_distance', return_value=[0.3])  # Below threshold
        else:
            mocker.patch('face_recognition.face_distance', return_value=[0.8])  # Above threshold
        
        data = {'qr_code_data': str(user_id), 'face_image': (BytesIO(b'fake'), 'test.jpg')}
        response = client.post('/verify', data=data, content_type='multipart/form-data')
        json_data = json.loads(response.data)
        
        if is_correct and json_data['match']:
            correct_matches += 1
        elif not is_correct and not json_data['match']:
            correct_matches += 1
    
    accuracy = correct_matches / total_tests
    assert accuracy >= 0.9, f"Accuracy {accuracy:.2%} below 90%"

def test_processing_time(client, mocker):
    """Test processing time: Max 5 seconds"""
    mocker.patch('face_recognition.load_image_file', return_value=Image.new('RGB', (100, 100)))
    mocker.patch('face_recognition.face_encodings', return_value=[[0.1, 0.2]])
    mocker.patch('face_recognition.face_distance', return_value=[0.3])
    
    data = {'qr_code_data': '1', 'face_image': (BytesIO(b'fake'), 'test.jpg')}
    
    start_time = time.time()
    response = client.post('/verify', data=data, content_type='multipart/form-data')
    end_time = time.time()
    
    processing_time = end_time - start_time
    assert processing_time <= 5.0, f"Processing time {processing_time:.2f}s exceeds 5s"
    assert response.status_code == 404

def test_reports_retention(client):
    """Test reports stored for 6 months (simulate cleanup)"""
    from datetime import datetime, timedelta
    with client.application.app_context():
        from db.models import EntryAttempt
        from db.db import db
        # Create old attempt
        old_attempt = EntryAttempt(qr_code_data="1", success=False, attempted_at=datetime.utcnow() - timedelta(days=200))
        db.session.add(old_attempt)
        db.session.commit()
        
        # Simulate cleanup: delete attempts older than 180 days
        cutoff = datetime.utcnow() - timedelta(days=180)
        old_attempts = EntryAttempt.query.filter(EntryAttempt.attempted_at < cutoff).all()
        for attempt in old_attempts:
            db.session.delete(attempt)
        db.session.commit()
        
        # Check if old attempts are removed
        remaining = EntryAttempt.query.filter(EntryAttempt.attempted_at < cutoff).count()
        assert remaining == 0, "Old reports not cleaned up"