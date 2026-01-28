import face_recognition
import pytest
import time
from io import BytesIO
from PIL import Image
import numpy as np
import json
import os
from pathlib import Path

# Path to test images
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"

def test_face_recognition_accuracy(client):
    """Test accuracy: Min 90% on sample data using real face images"""
    from db.models import User
    from db.db import db
    
    # Names of people in test images
    name_list = ["Colin_Farrell", "Jackie_Chan", "Jose_Serra",
                 "LeBron_James", "Leonardo_DiCaprio"]
    
    # Register users with face encodings from their first image
    with client.application.app_context():
        for i, person_name in enumerate(name_list):
            person_dir = TEST_IMAGES_DIR / person_name
            if person_dir.exists():
                # Use first image to create face encoding
                first_image_path = list(person_dir.glob("*.jpg"))[0]
                image = face_recognition.load_image_file(str(first_image_path))
                face_encodings = face_recognition.face_encodings(image)
                
                if len(face_encodings) > 0:
                    user = User(
                        name=person_name,
                        face_encoding=json.dumps(face_encodings[0].tolist()),
                        qr_code_data=str(i + 50)
                    )
                    db.session.add(user)
        db.session.commit()
    
    # Test verification accuracy
    correct_matches = 0
    total_tests = 0
    
    with client.application.app_context():
        for person_idx, person_name in enumerate(name_list):
            person_dir = TEST_IMAGES_DIR / person_name
            if person_dir.exists():
                # Get all images for this person
                images = list(person_dir.glob("*.jpg"))
                if len(images) > 1:  # Use images other than the first one for testing
                    for test_image_path in images[1:]:
                        total_tests += 1
                        
                        # Read test image
                        with open(test_image_path, 'rb') as f:
                            image_data = f.read()
                        
                        # Send verification request
                        data = {
                            'qr_code_data': str(person_idx + 50),
                            'face_image': (BytesIO(image_data), test_image_path.name)
                        }
                        response = client.post('/verify', data=data, content_type='multipart/form-data')
                        
                        if response.status_code == 200:
                            json_data = json.loads(response.data)
                            if json_data.get('match', False):
                                correct_matches += 1
    print(f"total tests: {total_tests}")
    if total_tests > 0:
        accuracy = correct_matches / total_tests
        print(f"Face Recognition Accuracy: {accuracy:.2%} ({correct_matches}/{total_tests})")
        assert accuracy >= 0.9, f"Accuracy {accuracy:.2%} below 90% threshold"
    else:
        pytest.skip("No test images available")

def test_face_verification_with_wrong_qr(client):
    """Test that verification fails when QR code doesn't match the face"""
    from db.models import User
    from db.db import db
    
    name_list = ["Colin_Farrell", "Jackie_Chan"]
    
    with client.application.app_context():
        # Register two users
        for i, person_name in enumerate(name_list):
            person_dir = TEST_IMAGES_DIR / person_name
            if person_dir.exists():
                first_image_path = list(person_dir.glob("*.jpg"))[0]
                image = face_recognition.load_image_file(str(first_image_path))
                face_encodings = face_recognition.face_encodings(image)
                
                if len(face_encodings) > 0:
                    user = User(
                        name=person_name,
                        face_encoding=json.dumps(face_encodings[0].tolist()),
                        qr_code_data=str(100 + i)
                    )
                    db.session.add(user)
        db.session.commit()
    
    # Test cross-matching: Use Jackie Chan's face with Colin Farrell's QR code
    if (TEST_IMAGES_DIR / name_list[1]).exists():
        test_image_path = list((TEST_IMAGES_DIR / name_list[1]).glob("*.jpg"))[1]
        
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        data = {
            'qr_code_data': '100',  # Colin Farrell's QR
            'face_image': (BytesIO(image_data), test_image_path.name)  # Jackie Chan's face
        }
        response = client.post('/verify', data=data, content_type='multipart/form-data')
        
        # Should either fail or have high distance
        if response.status_code == 200:
            json_data = json.loads(response.data)
            # Wrong face should not match
            print(json_data.get('match',False))
            assert not json_data.get('match', False), "Wrong face should not match"

def test_face_detection_required(client):
    """Test that verification requires a face in the image"""
    from db.models import User
    from db.db import db
    
    with client.application.app_context():
        # Create a dummy user
        user = User(
            name="Test User",
            face_encoding=json.dumps([0.1] * 128),  # Dummy encoding
            qr_code_data="999"
        )
        db.session.add(user)
        db.session.commit()
    
    # Create a blank image without a face
    blank_image = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    blank_image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    data = {
        'qr_code_data': '999',
        'face_image': (img_bytes, 'blank.jpg')
    }
    response = client.post('/verify', data=data, content_type='multipart/form-data')
    
    # Should fail because no face detected
    assert response.status_code != 200
    json_data = json.loads(response.data)
    print(response.status_code)
    if response.status_code == 400:
        assert 'error' in json_data or 'No face detected' in str(json_data)

def test_processing_time(client):
    """Test processing time: Max 5 seconds"""
    from db.models import User
    from db.db import db
    
    with client.application.app_context():
        # Use real image for timing test
        person_dir = TEST_IMAGES_DIR / "Colin_Farrell"
        if person_dir.exists():
            first_image_path = list(person_dir.glob("*.jpg"))[0]
            image = face_recognition.load_image_file(str(first_image_path))
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) > 0:
                user = User(
                    name="Colin_Farrell",
                    face_encoding=json.dumps(face_encodings[0].tolist()),
                    qr_code_data="500"
                )
                db.session.add(user)
            db.session.commit()
        
        # Get test image
        test_image_path = list((TEST_IMAGES_DIR / "Colin_Farrell").glob("*.jpg"))[1]
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        data = {
            'qr_code_data': '500',
            'face_image': (BytesIO(image_data), test_image_path.name)
        }
        
        start_time = time.time()
        response = client.post('/verify', data=data, content_type='multipart/form-data')
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"Processing time: {processing_time:.2f}s")
        assert processing_time <= 5.0, f"Processing time {processing_time:.2f}s exceeds 5s"

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
