#!/usr/bin/env python3
"""
Milvus Docker Compose Integration Test

This script tests the complete Milvus setup with the Docker Compose configuration
"""

import os
import sys
import time
import requests
import numpy as np

# Configuration
CONNECTOR_URL = "http://localhost:5050"
TEST_COLLECTION = "milvus_docker_compose_test"
VECTOR_DIM = 8  # Using a small dimension for testing

def test_integration():
    print("==== Milvus Docker Compose Integration Test ====\n")
    
    # Test the connection to the connector
    print("Step 1: Testing connector health...")
    try:
        response = requests.get(f"{CONNECTOR_URL}/health")
        if response.status_code == 200:
            print("✅ Connector is healthy\n")
        else:
            print(f"❌ Connector health check failed: {response.status_code} - {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to connector: {e}\n")
        return False
    
    # Connect to Milvus
    print("Step 2: Connecting to Milvus...")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/connect",
            json={
                "host": "host.docker.internal",  # Use Docker's host machine address
                "port": 19530
            }
        )
        
        if response.status_code == 200:
            print("✅ Connected to Milvus successfully\n")
        else:
            print(f"❌ Failed to connect to Milvus: {response.status_code} - {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Connection request failed: {e}\n")
        return False
    
    # Drop the test collection if it exists
    print(f"Step 3: Cleaning up existing collection {TEST_COLLECTION}...")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/drop_collection",
            json={"collection_name": TEST_COLLECTION}
        )
        print(f"Collection drop result: {response.status_code}\n")
    except Exception as e:
        print(f"Warning: Failed to drop collection: {e}\n")
    
    # Create a new test collection
    print(f"Step 4: Creating collection {TEST_COLLECTION}...")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/create_collection",
            json={
                "collection_name": TEST_COLLECTION,
                "dimension": VECTOR_DIM
            }
        )
        
        if response.status_code == 200:
            print(f"✅ Collection {TEST_COLLECTION} created successfully\n")
        else:
            print(f"❌ Failed to create collection: {response.status_code} - {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Collection creation request failed: {e}\n")
        return False
    
    # Prepare test vectors
    print("Step 5: Preparing test vectors...")
    # Create simple test vectors
    vectors = [
        [float(i) for i in range(1, VECTOR_DIM+1)],  # [1.0, 2.0, ..., 8.0]
        [float(VECTOR_DIM-i+1) for i in range(1, VECTOR_DIM+1)]  # [8.0, 7.0, ..., 1.0]
    ]
    print(f"Created {len(vectors)} test vectors with dimension {VECTOR_DIM}\n")
    
    # Insert vectors
    print("Step 6: Inserting vectors...")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/insert",
            json={
                "collection_name": TEST_COLLECTION,
                "vectors": vectors
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Vectors inserted successfully: {result}\n")
        else:
            print(f"❌ Failed to insert vectors: {response.status_code} - {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Vector insertion request failed: {e}\n")
        return False
    
    # If insertion was successful, try a search
    print("Step 7: Testing vector search...")
    try:
        response = requests.post(
            f"{CONNECTOR_URL}/search",
            json={
                "collection_name": TEST_COLLECTION,
                "query_vectors": [vectors[0]],  # Search with the first vector
                "top_k": 2  # Return top 2 matches
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search successful: {result}\n")
        else:
            print(f"❌ Search failed: {response.status_code} - {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Search request failed: {e}\n")
        return False
    
    print("==== Integration Test Completed Successfully! ====\n")
    return True

if __name__ == "__main__":
    test_integration()
