#!/usr/bin/env python3
"""
Direct test of the MilvusAdapter with simplified vectors

This script combines our successful minimal connector test with the MilvusAdapter
interface to verify integration between them.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db.vector_db import get_vector_db_client

# Constants
TEST_COLLECTION = "adapter_test_collection"
VECTOR_DIM = 8  # Small dimension for simplicity

def test_connection():
    """Test connection to Milvus via adapter."""
    print("\n=== Testing Connection ===")
    client = get_vector_db_client()
    print(f"Client type: {type(client).__name__}")
    
    result = client.connect()
    if result:
        print("✅ Successfully connected to Milvus")
        return client
    else:
        print("❌ Failed to connect to Milvus")
        return None

def cleanup_collection(client):
    """Ensure test collection is dropped if it exists."""
    print(f"\n=== Cleaning Up Collection: {TEST_COLLECTION} ===")
    collections = client.list_collections()
    if TEST_COLLECTION in collections:
        print(f"Collection {TEST_COLLECTION} exists, dropping it...")
        result = client.drop_collection(TEST_COLLECTION)
        if result:
            print(f"✅ Successfully dropped collection")
        else:
            print(f"❌ Failed to drop collection")
    else:
        print(f"Collection {TEST_COLLECTION} does not exist, no cleanup needed")

def create_collection(client):
    """Create a new test collection."""
    print(f"\n=== Creating Collection: {TEST_COLLECTION} ===")
    result = client.create_collection(
        TEST_COLLECTION, 
        VECTOR_DIM, 
        with_metadata=True,
        skip_loading=True
    )
    
    if result:
        print(f"✅ Successfully created collection")
        return True
    else:
        print(f"❌ Failed to create collection")
        return False

def insert_vectors(client):
    """Insert simple vectors into collection."""
    print("\n=== Inserting Vectors ===")
    
    # Define some very simple vectors with explicit Python floats
    vectors = [
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    ]
    print(f"Created {len(vectors)} simple test vectors with dimension {len(vectors[0])}")
    
    # Define simple string metadata
    metadata = [
        '{"source": "test", "id": 1}',
        '{"source": "test", "id": 2}'
    ]
    print(f"Created {len(metadata)} metadata entries")
    
    # Insert the vectors
    result = client.insert(TEST_COLLECTION, vectors, metadata)
    
    if result and len(result) > 0:
        print(f"✅ Successfully inserted vectors with IDs: {result}")
        return True
    else:
        print(f"❌ Failed to insert vectors")
        return False

def search_vectors(client):
    """Search for similar vectors."""
    print("\n=== Searching Vectors ===")
    
    # Use a simple query vector
    query = [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]]
    print(f"Created query vector with dimension {len(query[0])}")
    
    # Search
    results = client.search(TEST_COLLECTION, query, top_k=2)
    
    if results and len(results) > 0:
        print(f"✅ Search returned {len(results[0])} results")
        for i, item in enumerate(results[0]):
            print(f"  Result {i+1}: ID={item.get('id')}, Score={item.get('score')}")
        return True
    else:
        print(f"❌ Search returned no results")
        return False

def main():
    """Run the adapter test."""
    print("===== MilvusAdapter Integration Test =====")
    
    # Connect to Milvus
    client = test_connection()
    if not client:
        print("Exiting due to connection failure")
        return
    
    # Clean up existing collection
    cleanup_collection(client)
    
    # Create collection
    if not create_collection(client):
        print("Exiting due to collection creation failure")
        return
    
    # Insert vectors
    if not insert_vectors(client):
        print("Exiting due to insertion failure")
        return
    
    # Search vectors
    search_vectors(client)
    
    print("\n===== MilvusAdapter Test Complete =====")

if __name__ == "__main__":
    main()
