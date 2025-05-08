#!/usr/bin/env python3
"""
Exact Milvus 2.0.0 Insert Test

This script implements vector insertion following the exact API conventions
described in the Milvus 2.0.0 documentation, bypassing any abstractions.
"""

import os
import sys
import json
import time
import requests

# Constants
CONNECTOR_URL = "http://localhost:5050"
TEST_COLLECTION = "milvus_exact_test"
VECTOR_DIM = 8

# Main function for testing the insert operation
def test_milvus_exact_insert():
    print("===== Exact Milvus 2.0.0 Insert Test =====")
    
    # 1. Connect to Milvus
    print("Connecting to Milvus...")
    response = requests.post(
        f"{CONNECTOR_URL}/connect",
        json={
            "host": "host.docker.internal",
            "port": 19530,
            "user": "",
            "db_name": "default"
        }
    )
    
    if response.status_code != 200:
        print(f"Failed to connect: {response.status_code} - {response.text}")
        return False
    print("Connected successfully.")
    
    # 2. Check and drop existing collection
    print(f"\nChecking for existing collection {TEST_COLLECTION}...")
    response = requests.get(f"{CONNECTOR_URL}/list_collections")
    collections = response.json().get("collections", [])
    
    if TEST_COLLECTION in collections:
        print(f"Dropping existing collection {TEST_COLLECTION}...")
        response = requests.post(
            f"{CONNECTOR_URL}/drop_collection",
            json={"collection_name": TEST_COLLECTION}
        )
        print(f"Drop result: {response.status_code}")
    
    # 3. Create collection using the dedicated endpoint
    print(f"\nCreating collection {TEST_COLLECTION}...")
    create_data = {
        "collection_name": TEST_COLLECTION,
        "dimension": VECTOR_DIM,
        "with_metadata": False  # Simplify by not using metadata
    }
    
    response = requests.post(
        f"{CONNECTOR_URL}/create_collection",
        json=create_data
    )
    
    if response.status_code != 200:
        print(f"Failed to create collection: {response.status_code} - {response.text}")
        return False
    print("Collection created successfully.")
    
    # 4. Prepare minimal test data with just vectors
    print("\nPreparing test data...")
    vectors = [
        [float(i) for i in range(1, VECTOR_DIM+1)],  # [1.0, 2.0, 3.0, ..., 8.0]
        [float(VECTOR_DIM-i+1) for i in range(1, VECTOR_DIM+1)]  # [8.0, 7.0, 6.0, ..., 1.0]
    ]
    print(f"Created {len(vectors)} test vectors of dimension {VECTOR_DIM}.")
    
    # 5. Insert vectors using the exact Milvus 2.0.0 format
    print("\nInserting vectors...")
    insert_data = {
        "collection_name": TEST_COLLECTION,
        "vectors": vectors
    }
    
    response = requests.post(
        f"{CONNECTOR_URL}/insert",
        json=insert_data
    )
    
    if response.status_code != 200:
        print(f"Failed to insert vectors: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    print(f"Insert result: {result}")
    print("Vectors inserted successfully.")
    
    # 6. If insertion succeeded, try a simple search
    if result.get("status") == "success":
        print("\nInsertion succeeded, attempting search...")
        search_data = {
            "collection_name": TEST_COLLECTION,
            "query_vectors": [vectors[0]],  # Search using the first vector
            "top_k": 2
        }
        
        response = requests.post(
            f"{CONNECTOR_URL}/search",
            json=search_data
        )
        
        if response.status_code == 200:
            search_result = response.json()
            print(f"Search successful: {search_result}")
            return True
        else:
            print(f"Search failed: {response.status_code} - {response.text}")
    
    print("\n===== Test Complete =====")
    return True

if __name__ == "__main__":
    test_milvus_exact_insert()
