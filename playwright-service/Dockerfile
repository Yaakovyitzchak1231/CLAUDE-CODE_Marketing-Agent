# Playwright Service Dockerfile
# Multi-stage build for optimized image size

FROM python:3.11-slim-bookworm as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install font packages that Playwright needs (replaced packages in newer Debian)
RUN apt-get update && \
    apt-get install -y fonts-unifont fonts-ubuntu || true

# Install Playwright system dependencies
RUN playwright install-deps chromium

# Create non-root user
RUN useradd -m -u 1000 playwright && \
    chown -R playwright:playwright /app

# Copy application code
COPY . .
RUN chown -R playwright:playwright /app

# Switch to non-root user
USER playwright

# Install Playwright browsers as the non-root user
RUN playwright install chromium

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')" || exit 1

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
