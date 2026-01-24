from datetime import datetime
from .db import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)  # JSON string of face encoding
    qr_code_data = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.name}>'


class EntryAttempt(db.Model):
    __tablename__ = 'entry_attempts'
    id = db.Column(db.Integer, primary_key=True)
    qr_code_data = db.Column(db.String(200), nullable=True)  # QR code data used in attempt
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User if found
    user_name = db.Column(db.String(100), nullable=True)  # User name if found
    success = db.Column(db.Boolean, nullable=False)  # Whether access was granted
    failure_message = db.Column(db.Text, nullable=True)  # Error message if failed
    face_distance = db.Column(db.Float, nullable=True)  # Face distance if face was detected
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to User
    user = db.relationship('User', backref='entry_attempts')

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f'<EntryAttempt {self.id} - {status} - {self.attempted_at}>'
