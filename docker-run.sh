#!/bin/bash

# Docker helper script for QR Face Gate System

set -e

case "$1" in
    build)
        echo "Building Docker image..."
        docker build -t qr-face-gate-system .
        ;;
    run)
        echo "Starting container..."
        docker run -d \
            --name qr-face-gate \
            -p 5000:5000 \
            -v "$(pwd)/instance:/app/instance" \
            -v "$(pwd)/uploads:/app/uploads" \
            qr-face-gate-system
        echo "Container started. Access at http://localhost:5000"
        ;;
    stop)
        echo "Stopping container..."
        docker stop qr-face-gate || true
        docker rm qr-face-gate || true
        ;;
    logs)
        docker logs -f qr-face-gate
        ;;
    shell)
        docker exec -it qr-face-gate /bin/bash
        ;;
    restart)
        $0 stop
        $0 run
        ;;
    *)
        echo "Usage: $0 {build|run|stop|logs|shell|restart}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  run      - Run the container"
        echo "  stop     - Stop and remove the container"
        echo "  logs     - View container logs"
        echo "  shell    - Open a shell in the container"
        echo "  restart  - Restart the container"
        exit 1
        ;;
esac

