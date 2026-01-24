import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
db_user = os.getenv('POSTGRES_USER', 'qrfaceuser')
db_password = os.getenv('POSTGRES_PASSWORD', 'qrfacepass')
db_name = os.getenv('POSTGRES_DB', 'qrfacegate')
db_host = os.getenv('POSTGRES_HOST', 'localhost')
db_port = os.getenv('POSTGRES_PORT', '5432')

class BaseConfig:
    """Base configuration."""
    SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    # SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?client_encoding=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Data Protection Settings
    IMAGE_RETENTION_DAYS = int(os.getenv('IMAGE_RETENTION_DAYS', '90'))  # Default: 90 days (GDPR compliant)
    SECURE_FILE_NAMING = True  # Use hash-based filenames instead of predictable names
    LOG_IMAGE_ACCESS = True  # Log when images are accessed (for audit trail)
def get_config():
    print("--- TEST ENV ---")
    print(f"User: {os.getenv('POSTGRES_USER')}")
    print(f"Pass: {os.getenv('POSTGRES_PASSWORD')}")
    print("----------------")
    return BaseConfig()