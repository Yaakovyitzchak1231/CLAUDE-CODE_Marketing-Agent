# Chroma Vector Database Initialization

This directory contains the initialization script for setting up Chroma vector collections.

## Collections Created

The script creates 4 core vector collections:

1. **user_profiles** - User and audience profile embeddings
2. **content_library** - Historical content embeddings for RAG and similarity search
3. **market_segments** - Audience segment embeddings for targeting
4. **competitor_content** - Competitor content embeddings for analysis

## Usage

### Option 1: Run as Docker container (Recommended)

```bash
# Make sure Chroma is running first
docker-compose up -d chroma

# Build and run the init container
docker build -t chroma-init ./chroma-init
docker run --network marketing_network chroma-init
```

### Option 2: Run locally with Python

```bash
# Install dependencies
cd chroma-init
pip install -r requirements.txt

# Run the script (make sure Chroma container is running)
python init_collections.py
```

## Configuration

The script connects to Chroma at `http://chroma:8000` (Docker network) or `http://localhost:8000` (local).

All collections use:
- **Distance metric**: Cosine similarity
- **Embedding function**: Default (can be customized in LangChain service)

## Verification

After running, you can verify collections were created:

```bash
# Using curl
curl http://localhost:8000/api/v1/collections

# Or check in the Chroma logs
docker logs chroma
```

## Notes

- The script is idempotent - it won't recreate collections that already exist
- Collections start empty and will be populated by the LangChain agents
- Each collection uses HNSW indexing for fast similarity search
