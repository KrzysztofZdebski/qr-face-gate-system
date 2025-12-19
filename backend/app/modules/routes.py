from flask import Blueprint, render_template, request, jsonify, send_file
import io
import base64
import json
import numpy as np
import face_recognition
from app.db.db import db
from app.db.models import User
from  .controller import QRCodeController

qrCodeController = QRCodeController()
base_bp = Blueprint = Blueprint("base", __name__)

@base_bp.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@base_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Add a new user with face and generate QR code"""
    if request.method == 'GET':
        return render_template('add_user.html')
    
    if 'name' not in request.form or 'face_image' not in request.files:
        return jsonify({'error': 'Name and face image are required'}), 400
    
    name = request.form['name']
    face_image = request.files['face_image']
    
    if face_image.filename == '':
        return jsonify({'error': 'No image file provided'}), 400
    
    # Read and process the image
    image = face_recognition.load_image_file(face_image)
    face_encodings = face_recognition.face_encodings(image)
    
    if len(face_encodings) == 0:
        return jsonify({'error': 'No face detected in the image'}), 400
    
    if len(face_encodings) > 1:
        return jsonify({'error': 'Multiple faces detected. Please provide an image with only one face'}), 400
    
    # Get the first (and only) face encoding
    face_encoding = face_encodings[0]
    
    # Create new user with temporary qr_code_data
    # We'll update it with the actual ID after we get it
    new_user = User(
        name=name, 
        face_encoding=json.dumps(face_encoding.tolist()),
        qr_code_data="temp"  # Temporary value, will be updated below
    )
    db.session.add(new_user)
    db.session.flush()  # Get the user ID
    
    # Generate QR code with user ID
    new_user.qr_code_data = str(new_user.id)
    db.session.commit()
    
    # Generate QR code image
    qr_img = qrCodeController.generate_qr_code(new_user.id)
    
    # Convert QR code to base64 for display
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'user_id': new_user.id,
        'name': new_user.name,
        'qr_code': f'data:image/png;base64,{qr_base64}'
    })


@base_bp.route('/qr_code/<int:user_id>')
def get_qr_code(user_id):
    """Get QR code image for a user"""
    user = User.query.get_or_404(user_id)
    qr_img = qrCodeController.generate_qr_code(user.id)
    
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return send_file(img_buffer, mimetype='image/png')


@base_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify QR code and face match"""
    if request.method == 'GET':
        return render_template('verify.html')
    
    if 'qr_code_data' not in request.form or 'face_image' not in request.files:
        return jsonify({'error': 'QR code data and face image are required'}), 400
    
    qr_code_data = request.form['qr_code_data']
    face_image = request.files['face_image']
    
    # Find user by QR code data
    user = User.query.filter_by(qr_code_data=qr_code_data).first()
    if not user:
        return jsonify({'error': 'User not found for this QR code'}), 404
    
    # Load and process the face image
    image = face_recognition.load_image_file(face_image)
    face_encodings = face_recognition.face_encodings(image)
    
    if len(face_encodings) == 0:
        return jsonify({'error': 'No face detected in the image'}), 400
    
    # Get the first face encoding
    captured_face_encoding = face_encodings[0]
    
    # Load the stored face encoding
    stored_face_encoding = np.array(json.loads(user.face_encoding))
    
    # Compare faces
    face_distance = face_recognition.face_distance([stored_face_encoding], captured_face_encoding)[0]
    match = face_distance < 0.6  # Threshold for face matching (lower = stricter)
    
    return jsonify({
        'match': bool(match),
        'face_distance': float(face_distance),
        'user_name': user.name,
        'user_id': user.id,
        'threshold': 0.6
    })


@base_bp.route('/users')
def list_users():
    """List all users"""
    users = User.query.all()
    return render_template('users.html', users=users)

