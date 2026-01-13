FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy initialization script
COPY init_collections.py .

# Make script executable
RUN chmod +x init_collections.py

CMD ["python", "init_collections.py"]
