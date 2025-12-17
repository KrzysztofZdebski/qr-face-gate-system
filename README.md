# QR Face Gate System

## Installation

### Option 1: Docker (Recommended)

1. Build and run with Docker Compose:
```bash
docker-compose up -d
# Windows users with Docker Desktop 4.x+: use "docker compose" (no hyphen)
```

2. Access the application at: http://localhost:5000

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

**Note:** On Windows with Docker Desktop 4.x+, use `docker compose` instead of `docker-compose`.

### Option 2: Local Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install git+https://github.com/ageitgey/face_recognition_models
```

2. Start PostgreSQL database:
```bash
docker-compose up -d db
# Windows users with Docker Desktop 4.x+: use "docker compose" (no hyphen)
```

3. Run the application:
```bash
python backend/app/app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Adding a User

1. Click "Add New User" on the home page
2. Enter the user's full name
3. Upload a clear photo of the user's face (JPG/PNG format)
4. Click "Generate QR Code"
5. The system will:
   - Detect and encode the face
   - Create a user record
   - Generate a unique QR code
   - Display the QR code for saving

### Verifying Access

1. Click "Verify Access" on the home page
2. Enter the User ID from the QR code (or scan the QR code to get the ID)
3. Upload or capture a photo of the person's face
4. Click "Verify"
5. The system will:
   - Find the user associated with the QR code
   - Compare the captured face with the stored face encoding
   - Display whether access is granted or denied

### Viewing All Users

1. Click "View All Users" on the home page
2. See a list of all registered users with their QR codes

## Technical Details

- **Database**: SQLite database (`users.db`) stores user information and face encodings
- **Face Recognition**: Uses the `face_recognition` library (dlib-based)
- **QR Codes**: Generated using the `qrcode` library
- **Face Matching**: Uses Euclidean distance with a threshold of 0.6 (lower = stricter matching)

## API Endpoints

- `GET /` - Home page
- `GET /add_user` - Add user form
- `POST /add_user` - Create new user with face and QR code
- `GET /verify` - Verification form
- `POST /verify` - Verify QR code and face match
- `GET /users` - List all users
- `GET /qr_code/<user_id>` - Get QR code image for a user

## Notes

- Face images should contain only one face for best results
- Good lighting and clear images improve recognition accuracy
- The face matching threshold can be adjusted in `app.py` (currently 0.6)
- QR codes are long-term and tied to user IDs in the database
