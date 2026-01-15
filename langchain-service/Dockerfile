FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install font packages that Playwright needs (replaced packages in newer Debian)
RUN apt-get update && \
    apt-get install -y fonts-unifont fonts-ubuntu || true

# Install Playwright and system dependencies
RUN pip install playwright==1.40.0 && \
    playwright install-deps chromium

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models and cache
RUN mkdir -p /app/models /app/cache /app/logs

# Copy application code
COPY . .

# Install Playwright browsers (after copying code, before starting app)
RUN playwright install chromium

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
