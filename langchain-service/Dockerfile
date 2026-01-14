FROM python:3.11-slim

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

# Install Playwright browsers
RUN pip install playwright==1.40.0 && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for models and cache
RUN mkdir -p /app/models /app/cache /app/logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
