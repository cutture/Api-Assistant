#!/bin/sh
set -e

# Railway-compatible Docker entrypoint script
# Ensures proper port binding and provides startup logging

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

echo "=========================================="
echo "API Integration Assistant Starting"
echo "=========================================="
echo "Port: $PORT"
echo "Host: 0.0.0.0"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "=========================================="

# Check if required directories exist
if [ ! -d "/app/data" ]; then
    echo "ERROR: /app/data directory not found"
    exit 1
fi

# List contents for debugging
echo "Directory contents:"
ls -la /app

echo "Data directory contents:"
ls -la /app/data || echo "Cannot list /app/data"

# Start uvicorn with explicit port from environment
echo "Starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn src.api.app:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info \
    --access-log
