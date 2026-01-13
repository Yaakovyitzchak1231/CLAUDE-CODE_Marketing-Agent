#!/usr/bin/env python3
"""
Chroma Vector Database Initialization Script
Creates the 4 core collections for the B2B Marketing Automation Platform
"""

import chromadb
from chromadb.config import Settings
import time
import sys

def wait_for_chroma(client, max_retries=30, delay=2):
    """Wait for Chroma to be ready"""
    for i in range(max_retries):
        try:
            client.heartbeat()
            print(f"✓ Chroma is ready!")
            return True
        except Exception as e:
            print(f"Waiting for Chroma... ({i+1}/{max_retries})")
            time.sleep(delay)
    return False

def create_collections(client):
    """Create the 4 core vector collections"""

    collections = [
        {
            "name": "user_profiles",
            "metadata": {
                "description": "User and audience profile embeddings",
                "hnsw:space": "cosine"
            }
        },
        {
            "name": "content_library",
            "metadata": {
                "description": "Historical content embeddings for RAG and similarity search",
                "hnsw:space": "cosine"
            }
        },
        {
            "name": "market_segments",
            "metadata": {
                "description": "Audience segment embeddings for targeting",
                "hnsw:space": "cosine"
            }
        },
        {
            "name": "competitor_content",
            "metadata": {
                "description": "Competitor content embeddings for analysis",
                "hnsw:space": "cosine"
            }
        }
    ]

    created_count = 0

    for coll_config in collections:
        try:
            # Check if collection already exists
            existing_collections = [c.name for c in client.list_collections()]

            if coll_config["name"] in existing_collections:
                print(f"⚠ Collection '{coll_config['name']}' already exists, skipping...")
                continue

            # Create collection
            collection = client.create_collection(
                name=coll_config["name"],
                metadata=coll_config["metadata"]
            )
            print(f"✓ Created collection: {coll_config['name']}")
            print(f"  Description: {coll_config['metadata']['description']}")
            created_count += 1

        except Exception as e:
            print(f"✗ Error creating collection '{coll_config['name']}': {e}")

    return created_count

def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("Chroma Vector Database Initialization")
    print("="*60 + "\n")

    # Connect to Chroma (running in Docker on port 8000)
    try:
        client = chromadb.HttpClient(
            host="chroma",
            port=8000,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        print("✓ Connected to Chroma client")
    except Exception as e:
        print(f"✗ Failed to connect to Chroma: {e}")
        print("Make sure Chroma container is running: docker-compose up -d chroma")
        sys.exit(1)

    # Wait for Chroma to be ready
    if not wait_for_chroma(client):
        print("✗ Chroma did not become ready in time")
        sys.exit(1)

    # Create collections
    print("\nCreating vector collections...\n")
    created = create_collections(client)

    # Summary
    print("\n" + "="*60)
    print(f"Initialization complete!")
    print(f"Collections created: {created}")
    print("="*60 + "\n")

    # List all collections
    print("Current collections:")
    for collection in client.list_collections():
        print(f"  - {collection.name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
