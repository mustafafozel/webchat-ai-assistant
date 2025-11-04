# Multi-stage build for cross-platform compatibility
FROM python:3.11-slim-bullseye

# Set build arguments for multi-platform
ARG TARGETPLATFORM
ARG BUILDPLATFORM

LABEL maintainer="mustafafozel@example.com"
LABEL description="WebChat AI Assistant - Cross-Platform Compatible"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1000 webchat \
    && useradd --uid 1000 --gid webchat --shell /bin/bash --create-home webchat

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    curl \
    netcat \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==23.3.1 \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=webchat:webchat . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R webchat:webchat /app/logs /app/data

# Switch to non-root user
USER webchat

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Entry point
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]