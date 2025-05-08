#!/usr/bin/env python3
"""
Simplified Milvus Integration Test for Videntify

This script performs basic operations with Milvus in a more
controlled and resilient way to debug connection issues.
"""

import os
import sys
import time
import json
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db.vector_db import get_vector_db_client

# Configuration
TEST_COLLECTION = "videntify_simple_test"
VECTOR_DIM = 8  # Using a smaller dimension for simpler testing
TIMEOUT = 60  # Longer timeout for operations


def check_containers():
    """Check if Milvus Docker containers are running."""
    print("\n=== Checking Milvus Containers ===")
    import subprocess
    result = subprocess.run(["docker", "ps", "--filter", "name=milvus"], 
                           capture_output=True, text=True)
    
    all_running = True
    
    if "milvus-standalone" in result.stdout:
        print("✅ Milvus server is running")
    else:
        print("❌ Milvus server is NOT running")
        all_running = False
    
    if "milvus-connector" in result.stdout:
        print("✅ Milvus connector is running")
    else:
        print("❌ Milvus connector is NOT running")
        all_running = False
    
    return all_running


def test_connection():
    """Test basic connection to Milvus."""
    print("\n=== Testing Connection ===")
    client = get_vector_db_client()
    print(f"Client type: {type(client).__name__}")
    
    try:
        connected = client.connect()
        if connected:
            print("✅ Successfully connected to Milvus")
            return client
        else:
            print("❌ Failed to connect")
            return None
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")
        return None


def test_collection_creation(client):
    """Test creating a collection."""
    print(f"\n=== Creating Collection: {TEST_COLLECTION} ===")
    
    # First check if collection exists and drop it
    try:
        collections = client.list_collections()
        print(f"Found {len(collections)} existing collections")
        
        if TEST_COLLECTION in collections:
            print(f"Collection {TEST_COLLECTION} exists, dropping it...")
            if client.drop_collection(TEST_COLLECTION):
                print(f"✅ Successfully dropped {TEST_COLLECTION}")
            else:
                print(f"❌ Failed to drop {TEST_COLLECTION}")
    except Exception as e:
        print(f"❌ Error listing/dropping collections: {type(e).__name__}: {e}")
    
    # Create the collection
    try:
        # Set parameters to avoid loading collection into memory
        result = client.create_collection(
            TEST_COLLECTION, 
            VECTOR_DIM,
            with_metadata=True,
            create_index=False,  # Skip index creation for now
            skip_loading=True    # Skip loading into memory
        )
        
        if result:
            print(f"✅ Successfully created collection {TEST_COLLECTION}")
            return True
        else:
            print(f"❌ Failed to create collection")
            return False
    except Exception as e:
        print(f"❌ Error creating collection: {type(e).__name__}: {e}")
        return False


def test_vector_insertion(client):
    """Test inserting vectors."""
    print("\n=== Inserting Test Vectors ===")
    
    try:
        # Create simple test vectors - use a smaller dimension to ensure compatibility
        # Milvus may be more sensitive with larger dimensions
        test_dim = 8  # Start with a smaller dimension
        vectors = np.random.rand(3, test_dim).astype(np.float32).tolist()
        print(f"Generated {len(vectors)} test vectors of dimension {test_dim}")
        
        # Ensure each vector element is explicitly a Python float
        explicit_vectors = []
        for vec in vectors:
            explicit_vectors.append([float(x) for x in vec])
        
        print(f"Converted to explicit Python floats")
        
        # Simplify metadata to string format
        metadata = [
            f'{{"source": "test", "index": {i}}}'
            for i in range(len(explicit_vectors))
        ]
        
        # Insert vectors
        print("Inserting vectors...")
        ids = client.insert(TEST_COLLECTION, explicit_vectors, metadata)
        
        if ids and len(ids) > 0:
            print(f"✅ Successfully inserted {len(ids)} vectors")
            print(f"  IDs: {ids}")
            return True
        else:
            print("❌ Failed to insert vectors")
            return False
    except Exception as e:
        print(f"❌ Error inserting vectors: {type(e).__name__}: {e}")
        return False


def test_vector_search(client):
    """Test searching for vectors."""
    print("\n=== Searching Vectors ===")
    
    try:
        # Create a test query vector
        query = np.random.rand(1, VECTOR_DIM).astype(np.float32).tolist()
        print(f"Generated query vector of dimension {VECTOR_DIM}")
        
        # Search
        print("Searching...")
        results = client.search(TEST_COLLECTION, query, top_k=3)
        
        if results and len(results) > 0:
            print(f"✅ Search returned {len(results[0])} results")
            for i, res in enumerate(results[0]):
                print(f"  Result {i+1}: ID={res.get('id')}, Score={res.get('score'):.4f}")
            return True
        else:
            print("❌ Search returned no results")
            return False
    except Exception as e:
        print(f"❌ Error searching vectors: {type(e).__name__}: {e}")
        return False


def main():
    """Run the simplified Milvus test."""
    print("===== Simplified Milvus Integration Test =====")
    
    # Step 1: Check if containers are running
    if not check_containers():
        print("\n⚠️ Some Milvus containers are not running. Please start them first.")
        return
    
    # Step 2: Test connection
    client = test_connection()
    if not client:
        print("\n⚠️ Could not connect to Milvus. Please check the server and connector.")
        return
    
    # Step 3: Test collection creation
    if not test_collection_creation(client):
        print("\n⚠️ Could not create test collection. Skipping remaining tests.")
        return
    
    # Step 4: Test vector insertion
    if not test_vector_insertion(client):
        print("\n⚠️ Could not insert vectors. Skipping search test.")
        return
    
    # Step 5: Test vector search
    test_vector_search(client)
    
    print("\n===== Milvus Integration Test Complete =====")


if __name__ == "__main__":
    main()
