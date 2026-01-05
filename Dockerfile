# ============================================================================
# Multi-stage Dockerfile for API Integration Assistant
# Optimized for production deployment with minimal image size
# ============================================================================

# ----- Stage 1: Builder -----
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ----- Stage 2: Runtime -----
FROM python:3.11-slim

# Set metadata
LABEL maintainer="API Integration Assistant Team"
LABEL description="AI-powered API integration assistant with RAG and code generation"
LABEL version="0.2.0"

# Set environment variables (no hardcoded PORT - let Railway set it dynamically)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy entrypoint script first (before changing ownership)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/chroma_db /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Switch to non-root user
USER appuser

# Expose port (Railway will set $PORT dynamically)
EXPOSE 8000

# Health check (Railway will check the /health endpoint on the dynamically assigned PORT)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use entrypoint script for better logging and port handling
CMD ["/usr/local/bin/docker-entrypoint.sh"]
