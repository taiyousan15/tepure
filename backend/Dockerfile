# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r tepure && useradd -r -g tepure tepure

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/tepure/.local

# Copy application code
COPY app/ ./app/
COPY gunicorn.conf.py .

# Set environment variables
ENV PATH=/home/tepure/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Change ownership
RUN chown -R tepure:tepure /app

# Switch to non-root user
USER tepure

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Expose port
EXPOSE 8080

# Start Gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
