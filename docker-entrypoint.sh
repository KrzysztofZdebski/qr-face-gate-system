#!/bin/bash
set -e

# Ensure directories exist (don't chmod mounted volumes - it won't work)
mkdir -p /app/uploads

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until python -c "import psycopg2; psycopg2.connect('postgresql://${POSTGRES_USER:-qrfaceuser}:${POSTGRES_PASSWORD:-qrfacepass}@${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-qrfacegate}')" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Execute the main command
exec "$@"

