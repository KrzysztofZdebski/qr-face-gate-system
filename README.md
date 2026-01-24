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