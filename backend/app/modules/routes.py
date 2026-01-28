from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session, redirect, url_for
import io
import base64
import json
import numpy as np
import face_recognition
import os
import hashlib
import stat
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from db.db import db
from db.models import User, EntryAttempt
from  .controller import QRCodeController

# PDF generation for user reports
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import simpleSplit
except ImportError:
    A4 = None
    canvas = None
    pdfmetrics = None
    TTFont = None
    simpleSplit = None

qrCodeController = QRCodeController()
base_bp = Blueprint("base", __name__)

def require_admin():
    """Helper function to check if user is logged in as admin"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('base.admin_login'))
    return None

def save_failed_attempt_image(face_image, attempt_id):
    """Save the face image from a failed attempt with security measures"""
    try:
        # Get upload folder from app config (should already be absolute from app.py)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.isabs(upload_folder):
            # Make it absolute relative to the app root directory
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_folder = os.path.join(app_root, upload_folder)
        
        failed_attempts_folder = os.path.join(upload_folder, 'failed_attempts')
        os.makedirs(failed_attempts_folder, exist_ok=True)
        
        # Set secure directory permissions (owner read/write/execute only)
        try:
            os.chmod(failed_attempts_folder, stat.S_IRWXU)  # 0700 - owner only
        except Exception:
            pass  # May fail on Windows, that's okay
        
        # Read file content for hashing
        face_image.seek(0)
        file_content = face_image.read()
        face_image.seek(0)
        
        # Get file extension
        filename = getattr(face_image, 'filename', None)
        if filename:
            ext = os.path.splitext(filename)[1] or '.jpg'
        else:
            ext = '.jpg'
        
        # Create secure filename using hash (GDPR compliant - no predictable names)
        if current_app.config.get('SECURE_FILE_NAMING', True):
            # Use hash of content + attempt_id + timestamp for uniqueness and security
            hash_input = f"{attempt_id}_{datetime.utcnow().isoformat()}_{file_content[:1000]}"
            file_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]
            safe_filename = f"{file_hash}{ext}"
        else:
            # Fallback to timestamp-based (less secure)
            safe_filename = f"attempt_{attempt_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        filepath = os.path.join(failed_attempts_folder, safe_filename)
        
        # Save file
        if hasattr(face_image, 'save'):
            # It's a file upload object
            face_image.save(filepath)
        else:
            # It's a BytesIO or similar object
            with open(filepath, 'wb') as f:
                f.write(file_content)
        
        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)  # 0600 - owner read/write only
        except Exception:
            pass  # May fail on Windows, that's okay
        
        # Return relative path for database storage
        return os.path.join('failed_attempts', safe_filename)
    except Exception as e:
        print(f"Error saving failed attempt image: {e}")
        import traceback
        traceback.print_exc()
        return None

@base_bp.route('/')
def index():
    """Main page"""
    print("Index route")
    return render_template('index.html')


@base_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Add a new user with face and generate QR code"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
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


@base_bp.route('/failed_attempt_image/<int:attempt_id>')
def get_failed_attempt_image(attempt_id):
    """Get the image from a failed entry attempt (with access logging)"""
    attempt = EntryAttempt.query.get_or_404(attempt_id)
    
    if not attempt.image_path:
        return jsonify({'error': 'No image available for this attempt'}), 404
    
    # Log access for audit trail (GDPR compliance)
    if current_app.config.get('LOG_IMAGE_ACCESS', True):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        print(f"[IMAGE_ACCESS] Attempt ID: {attempt_id}, IP: {client_ip}, Time: {datetime.utcnow().isoformat()}")
    
    # Get upload folder from app config (should already be absolute from app.py)
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder):
        # Make it absolute relative to the app root directory
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_folder = os.path.join(app_root, upload_folder)
    
    image_path = os.path.join(upload_folder, attempt.image_path)
    
    if not os.path.exists(image_path):
        return jsonify({'error': 'Image file not found'}), 404
    
    return send_file(image_path)


@base_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify QR code and face match"""
    if request.method == 'GET':
        return render_template('verify.html')
    
    # Initialize variables for logging
    qr_code_data = None
    user = None
    face_distance = None
    failure_message = None
    success = False
    
    try:
        # Check if required fields are present
        if 'qr_code_data' not in request.form or 'face_image' not in request.files:
            failure_message = 'QR code data and face image are required'
            attempt = EntryAttempt(
                qr_code_data=None,
                user_id=None,
                user_name=None,
                success=False,
                failure_message=failure_message,
                face_distance=None,
                image_path=None
            )
            db.session.add(attempt)
            db.session.commit()
            return jsonify({'error': failure_message}), 400
        
        qr_code_data = request.form['qr_code_data']
        face_image = request.files['face_image']
        
        # Find user by QR code data
        user = User.query.filter_by(qr_code_data=qr_code_data).first()
        if not user:
            failure_message = 'User not found for this QR code'
            # Create attempt first to get ID, then save image
            attempt = EntryAttempt(
                qr_code_data=qr_code_data,
                user_id=None,
                user_name=None,
                success=False,
                failure_message=failure_message,
                face_distance=None,
                image_path=None
            )
            db.session.add(attempt)
            db.session.flush()  # Get the ID without committing
            # Save a copy of the file content before processing
            face_image.seek(0)
            file_content = face_image.read()
            from io import BytesIO
            temp_file = BytesIO(file_content)
            temp_file.filename = face_image.filename  # Preserve filename
            # Save the image
            image_path = save_failed_attempt_image(temp_file, attempt.id)
            attempt.image_path = image_path
            db.session.commit()
            return jsonify({'error': failure_message}), 404
        
        # Save a copy of the file content before processing (for potential failure logging)
        face_image.seek(0)
        file_content = face_image.read()
        face_image.seek(0)  # Reset for face_recognition
        
        # Load and process the face image
        image = face_recognition.load_image_file(face_image)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            failure_message = 'No face detected in the image'
            # Create attempt first to get ID, then save image
            attempt = EntryAttempt(
                qr_code_data=qr_code_data,
                user_id=user.id,
                user_name=user.name,
                success=False,
                failure_message=failure_message,
                face_distance=None,
                image_path=None
            )
            db.session.add(attempt)
            db.session.flush()  # Get the ID without committing
            # Save the image using the saved file content
            from io import BytesIO
            temp_file = BytesIO(file_content)
            temp_file.filename = face_image.filename  # Preserve filename
            image_path = save_failed_attempt_image(temp_file, attempt.id)
            attempt.image_path = image_path
            db.session.commit()
            return jsonify({'error': failure_message}), 400
        
        # Get the first face encoding
        captured_face_encoding = face_encodings[0]
        
        # Load the stored face encoding
        stored_face_encoding = np.array(json.loads(user.face_encoding))
        
        # Compare faces
        face_distance = face_recognition.face_distance([stored_face_encoding], captured_face_encoding)[0]
        match = face_distance < 0.6  # Threshold for face matching (lower = stricter)
        
        if match:
            success = True
            failure_message = None
            image_path = None
        else:
            success = False
            failure_message = f'Face mismatch: distance {face_distance:.4f} exceeds threshold 0.6'
            # Create attempt first to get ID, then save image
            attempt = EntryAttempt(
                qr_code_data=qr_code_data,
                user_id=user.id,
                user_name=user.name,
                success=False,
                failure_message=failure_message,
                face_distance=float(face_distance),
                image_path=None
            )
            db.session.add(attempt)
            db.session.flush()  # Get the ID without committing
            # Save the image using the saved file content
            from io import BytesIO
            temp_file = BytesIO(file_content)
            temp_file.filename = face_image.filename  # Preserve filename
            image_path = save_failed_attempt_image(temp_file, attempt.id)
            attempt.image_path = image_path
            db.session.commit()
            return jsonify({
                'match': False,
                'face_distance': float(face_distance),
                'user_name': user.name,
                'user_id': user.id,
                'threshold': 0.6
            })
        
        # Log successful attempt (no image saved)
        attempt = EntryAttempt(
            qr_code_data=qr_code_data,
            user_id=user.id,
            user_name=user.name,
            success=True,
            failure_message=None,
            face_distance=float(face_distance),
            image_path=None
        )
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify({
            'match': bool(match),
            'face_distance': float(face_distance),
            'user_name': user.name,
            'user_id': user.id,
            'threshold': 0.6
        })
    
    except Exception as e:
        # Log any unexpected errors
        failure_message = f'Unexpected error: {str(e)}'
        attempt = EntryAttempt(
            qr_code_data=qr_code_data,
            user_id=user.id if user else None,
            user_name=user.name if user else None,
            success=False,
            failure_message=failure_message,
            face_distance=face_distance,
            image_path=None
        )
        db.session.add(attempt)
        db.session.flush()  # Get the ID without committing
        # Try to save image if face_image is available
        if 'face_image' in request.files and request.files['face_image']:
            face_image = request.files['face_image']
            if face_image.filename:
                try:
                    face_image.seek(0)
                    file_content = face_image.read()
                    from io import BytesIO
                    temp_file = BytesIO(file_content)
                    temp_file.filename = face_image.filename
                    image_path = save_failed_attempt_image(temp_file, attempt.id)
                    attempt.image_path = image_path
                except Exception as img_error:
                    print(f"Error saving image in exception handler: {img_error}")
        db.session.commit()
        return jsonify({'error': failure_message}), 500


@base_bp.route('/users')
def list_users():
    """List all users"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    users = User.query.all()
    return render_template('users.html', users=users)


@base_bp.route('/reports')
def reports():
    """Display all entry attempts"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    attempts = EntryAttempt.query.order_by(EntryAttempt.attempted_at.desc()).all()
    
    # Calculate statistics
    total_attempts = len(attempts)
    successful_attempts = sum(1 for attempt in attempts if attempt.success)
    failed_attempts = total_attempts - successful_attempts
    
    return render_template('reports.html', 
                         attempts=attempts,
                         total_attempts=total_attempts,
                         successful_attempts=successful_attempts,
                         failed_attempts=failed_attempts)


@base_bp.route('/delete_attempt_image/<int:attempt_id>', methods=['POST'])
def delete_attempt_image(attempt_id):
    """Delete an attempt image (GDPR Right to be Forgotten)"""
    attempt = EntryAttempt.query.get_or_404(attempt_id)
    
    if not attempt.image_path:
        return jsonify({'error': 'No image associated with this attempt'}), 404
    
    # Get upload folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder):
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_folder = os.path.join(app_root, upload_folder)
    
    image_path = os.path.join(upload_folder, attempt.image_path)
    
    # Delete file if it exists
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            return jsonify({'error': f'Error deleting file: {str(e)}'}), 500
    
    # Clear database reference
    attempt.image_path = None
    db.session.commit()
    
    # Log deletion for audit trail
    print(f"[IMAGE_DELETION] Attempt ID: {attempt_id}, IP: {request.remote_addr}, Time: {datetime.utcnow().isoformat()}")
    
    return jsonify({'success': True, 'message': 'Image deleted successfully'})


@base_bp.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'admin123')
        if password == admin_password:
            session['admin_logged_in'] = True
            return redirect(url_for('base.admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid password')
    return render_template('admin_login.html')


@base_bp.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Get statistics using EntryAttempt model
    total_users = User.query.count()
    total_access_attempts = EntryAttempt.query.count()
    successful_accesses = EntryAttempt.query.filter_by(success=True).count()
    
    # Get all attempts (like reports page)
    attempts = EntryAttempt.query.order_by(EntryAttempt.attempted_at.desc()).all()
    
    # Calculate statistics
    successful_attempts = sum(1 for attempt in attempts if attempt.success)
    failed_attempts = total_access_attempts - successful_attempts
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         total_access_attempts=total_access_attempts,
                         successful_accesses=successful_accesses,
                         attempts=attempts,
                         successful_attempts=successful_attempts,
                         failed_attempts=failed_attempts)


@base_bp.route('/admin/user/<int:user_id>/report')
def user_report(user_id):
    """Show all entry attempts for a specific user"""
    admin_check = require_admin()
    if admin_check:
        return admin_check

    user = User.query.get_or_404(user_id)
    attempts = (
        EntryAttempt.query
        .filter_by(user_id=user_id)
        .order_by(EntryAttempt.attempted_at.desc())
        .all()
    )

    total_attempts = len(attempts)
    successful_attempts = sum(1 for a in attempts if a.success)
    failed_attempts = total_attempts - successful_attempts

    return render_template(
        'user_report.html',
        user=user,
        attempts=attempts,
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        failed_attempts=failed_attempts,
    )


@base_bp.route('/admin/user/<int:user_id>/report/pdf')
def user_report_pdf(user_id):
    """Download PDF report with all entry attempts for a specific user"""
    admin_check = require_admin()
    if admin_check:
        return admin_check

    user = User.query.get_or_404(user_id)
    attempts = (
        EntryAttempt.query
        .filter_by(user_id=user_id)
        .order_by(EntryAttempt.attempted_at.desc())
        .all()
    )

    # If reportlab is not installed, return a clear error
    if canvas is None or A4 is None:
        return jsonify({
            'error': 'PDF generation library (reportlab) is not installed. '
                     'Install it with: pip install reportlab'
        }), 500

    buffer = io.BytesIO()

    # Choose font that supports Polish characters (Windows Arial as default)
    base_font = "Helvetica"
    if pdfmetrics is not None and TTFont is not None:
        try:
            # This path should exist on standard Windows installations
            arial_path = r"C:\Windows\Fonts\arial.ttf"
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont("ArialPL", arial_path))
                base_font = "ArialPL"
        except Exception as font_err:
            print(f"Could not register Arial font for PDF: {font_err}")

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    y = height - 50
    pdf.setFont(base_font, 16)
    pdf.drawString(50, y, f"Raport wejść - {user.name} (ID: {user.id})")
    y -= 25
    pdf.setFont(base_font, 10)
    pdf.drawString(50, y, f"Data wygenerowania: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    y -= 25

    # Summary
    total_attempts = len(attempts)
    successful_attempts = sum(1 for a in attempts if a.success)
    failed_attempts = total_attempts - successful_attempts

    pdf.drawString(50, y, f"Liczba wszystkich wejść: {total_attempts}")
    y -= 15
    pdf.drawString(50, y, f"Udane wejścia: {successful_attempts}")
    y -= 15
    pdf.drawString(50, y, f"Nieudane wejścia: {failed_attempts}")
    y -= 25

    pdf.setFont(base_font, 10)

    margin_left = 50
    margin_right = width - 50
    margin_bottom = 60

    def draw_header():
        nonlocal y
        pdf.setFont(base_font, 14)
        pdf.drawString(margin_left, y, f"Raport wejść - {user.name} (ID: {user.id})")
        y -= 25
        pdf.setFont(base_font, 10)

    # Raport ograniczony do jednej strony PDF – priorytet najnowszych wejść
    # (pętla urywa się, gdy zabraknie miejsca na kolejne wpisy)

    # Rows (one block per attempt: date + status, message)
    for attempt in attempts:
        # Jeśli brakuje miejsca na kolejny blok, kończymy (tylko jedna strona)
        if y < margin_bottom + 60:
            break

        timestamp = attempt.attempted_at.strftime('%Y-%m-%d %H:%M:%S')
        status = "SUKCES" if attempt.success else "BŁĄD"
        message = attempt.failure_message or ""

        # First line: date + status
        pdf.setFont(base_font, 10)
        pdf.drawString(margin_left, y, f"Data i godzina: {timestamp}")
        pdf.drawString(margin_left + 260, y, f"Status: {status}")
        y -= 14

        # Message (wrapped)
        if message:
            pdf.setFont(base_font, 9)
            available_width = margin_right - margin_left
            if simpleSplit is not None:
                lines = simpleSplit(message, base_font, 9, available_width)
            else:
                # Fallback: naive wrapping by chunks
                max_chars = 90
                lines = [message[i:i + max_chars] for i in range(0, len(message), max_chars)]

            for line in lines:
                if y < margin_bottom:
                    new_page()
                    pdf.setFont(base_font, 9)
                pdf.drawString(margin_left, y, f"Komunikat: {line}" if line == lines[0] else f"           {line}")
                y -= 12
        else:
            if y < margin_bottom:
                new_page()
            pdf.setFont(base_font, 9)
            pdf.drawString(margin_left, y, "Komunikat: —")
            y -= 12

        # Spacer między próbami
        y -= 10

    pdf.save()
    buffer.seek(0)

    filename = f"raport_uzytkownik_{user.id}.pdf"
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@base_bp.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('base.index'))


@base_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user (admin only)"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    user = User.query.get_or_404(user_id)
    
    # Delete associated entry attempts first
    EntryAttempt.query.filter_by(user_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'User {user.name} deleted successfully'})

