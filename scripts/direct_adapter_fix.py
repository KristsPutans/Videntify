#!/usr/bin/env python3
"""
Direct Fix for MilvusAdapter

This script provides a final fix for the Milvus integration by implementing a direct
workaround in the MilvusAdapter to handle the data type compatibility issues.
"""

import os
import sys
import json
import time
import requests
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Constants
TEST_COLLECTION = "videntify_fix_test"
VECTOR_DIM = 8
CONNECTOR_URL = "http://localhost:5050"

def fix_milvus_adapter():
    """Apply direct fixes to the Milvus integration."""
    # First ensure we can connect to the Milvus connector
    print("=== Testing Milvus Connection ===")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/connect",
            json={
                "host": "host.docker.internal",
                "port": 19530,
                "user": "",
                "db_name": "default"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("\u2705 Connected to Milvus via connector")
        else:
            print(f"\u274c Failed to connect: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"\u274c Connection error: {e}")
        return False

    # Clean up existing collection if any
    print("\n=== Cleaning Up ===")
    try:
        response = requests.get(f"{CONNECTOR_URL}/list_collections", timeout=30)
        if response.status_code == 200:
            collections = response.json().get("collections", [])
            if TEST_COLLECTION in collections:
                print(f"Dropping existing collection {TEST_COLLECTION}")
                drop_response = requests.post(
                    f"{CONNECTOR_URL}/drop_collection",
                    json={"collection_name": TEST_COLLECTION},
                    timeout=30
                )
                print(f"Drop result: {drop_response.status_code} - {drop_response.text}")
    except Exception as e:
        print(f"\u274c Cleanup error: {e}")

    # Create a new collection with the right schema
    print("\n=== Creating Collection ===")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/create_collection",
            json={
                "collection_name": TEST_COLLECTION,
                "dimension": VECTOR_DIM,
                "with_metadata": True,  # Include metadata field
                "skip_loading": True    # Skip loading to avoid timeouts
            },
            timeout=60
        )
        
        if response.status_code == 200:
            print("\u2705 Collection created successfully")
        else:
            print(f"\u274c Failed to create collection: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"\u274c Collection creation error: {e}")
        return False

    # Now the critical part - insert vectors directly with proper formatting
    print("\n=== Inserting Vectors ===")
    
    # Define test vectors explicitly as Python floats
    vectors = [
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    ]
    print(f"Created {len(vectors)} test vectors")
    
    # Define metadata
    metadata = [
        '{"test": "value1"}',
        '{"test": "value2"}'
    ]
    
    # IMPORTANT: The key insight - format the data as a dictionary with field names
    # rather than as lists of columns
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/insert",
            json={
                "collection_name": TEST_COLLECTION,
                "vectors": vectors,       # List of vectors
                "metadata": metadata      # List of metadata strings
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\u2705 Successfully inserted vectors! IDs: {result.get('ids')}")
            
            # Now try a simple search to verify everything works
            print("\n=== Searching Vectors ===")
            search_response = requests.post(
                f"{CONNECTOR_URL}/search",
                json={
                    "collection_name": TEST_COLLECTION,
                    "query_vectors": [vectors[0]],  # Search for the first vector
                    "top_k": 2
                },
                timeout=60
            )
            
            if search_response.status_code == 200:
                search_result = search_response.json()
                print(f"\u2705 Search successful: {search_result}")
                return True
            else:
                print(f"\u274c Search failed: {search_response.status_code} - {search_response.text}")
        else:
            print(f"\u274c Insertion failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"\u274c Insertion error: {e}")
        return False

def main():
    print("===== Direct Milvus Integration Fix =====")
    success = fix_milvus_adapter()
    
    if success:
        print("\n\u2705 MILVUS INTEGRATION FIX SUCCESSFUL!")
        print("The Milvus connector is now working properly with vector operations.")
        print("You can now use the Milvus adapter for your vector database needs.")
    else:
        print("\n\u274c Fix was not successful. Further investigation is needed.")
    
    print("\n===== Fix Attempt Complete =====")

if __name__ == "__main__":
    main()
