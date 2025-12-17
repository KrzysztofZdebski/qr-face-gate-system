# Docker Setup for QR Face Gate System

This guide explains how to run the QR Face Gate System in a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. Build and start the container:
```bash
docker-compose up -d
```

2. Access the application at: http://localhost:5000

3. View logs:
```bash
docker-compose logs -f
```

4. Stop the container:
```bash
docker-compose down
```

### Option 2: Using Docker directly

1. Build the image:
```bash
docker build -t qr-face-gate-system .
```

2. Run the container:
```bash
docker run -d \
  --name qr-face-gate \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  qr-face-gate-system
```

3. Access the application at: http://localhost:5000

4. View logs:
```bash
docker logs -f qr-face-gate
```

5. Stop the container:
```bash
docker stop qr-face-gate
docker rm qr-face-gate
```

## Data Persistence

The Docker setup uses volumes to persist data:
- `./instance` - Contains the SQLite database (`users.db`)
- `./uploads` - Contains uploaded files (if any)

These directories are created automatically if they don't exist.

## Building for Different Architectures

### Build for ARM64 (Apple Silicon, Raspberry Pi):
```bash
docker buildx build --platform linux/arm64 -t qr-face-gate-system .
```

### Build for AMD64:
```bash
docker buildx build --platform linux/amd64 -t qr-face-gate-system .
```

## Environment Variables

You can customize the application using environment variables:

```bash
docker run -d \
  --name qr-face-gate \
  -p 5000:5000 \
  -e FLASK_ENV=development \
  -e FLASK_DEBUG=1 \
  qr-face-gate-system
```

## Troubleshooting

### Container won't start
Check logs:
```bash
docker-compose logs
# or
docker logs qr-face-gate
```

### Port already in use
Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead of 5000
```

### Permission issues
If you encounter permission issues with volumes:
```bash
sudo chown -R $USER:$USER instance uploads
```

### Rebuild after code changes
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production, consider:

1. **Use a reverse proxy** (nginx, Traefik):
```yaml
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - qr-face-gate
```

2. **Use environment-specific configs**:
```bash
docker run -d \
  --env-file .env.production \
  qr-face-gate-system
```

3. **Use a production WSGI server** (gunicorn, uWSGI):
Update Dockerfile CMD to:
```dockerfile
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Development Mode

For development with hot-reload:

```bash
docker run -d \
  --name qr-face-gate-dev \
  -p 5000:5000 \
  -v $(pwd):/app \
  -e FLASK_ENV=development \
  -e FLASK_DEBUG=1 \
  qr-face-gate-system
```

Note: Hot-reload requires mounting the source code as a volume.

