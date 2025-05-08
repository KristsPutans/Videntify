#!/usr/bin/env python3
"""
Milvus Data Format Test

This script tests different data format approaches with the connector.
"""

import requests
import numpy as np
import json

# Constants
CONNECTOR_URL = "http://localhost:5050"
TEST_COLLECTION = "format_test_collection"
VECTOR_DIM = 8

def test_format():
    print("===== Milvus 2.0.0 Format Test =====")
    
    # 1. Connect to Milvus
    print("Connecting to Milvus...")
    response = requests.post(
        f"{CONNECTOR_URL}/connect",
        json={
            "host": "host.docker.internal",
            "port": 19530
        }
    )
    
    if response.status_code != 200:
        print(f"Failed to connect: {response.status_code} - {response.text}")
        return False
    print("Connected successfully")
    
    # 2. Drop collection if exists
    print(f"\nDropping existing collection {TEST_COLLECTION} if it exists...")
    response = requests.post(
        f"{CONNECTOR_URL}/drop_collection",
        json={"collection_name": TEST_COLLECTION}
    )
    print(f"Drop result: {response.status_code}")
    
    # 3. Create the collection
    print(f"\nCreating collection {TEST_COLLECTION}...")
    response = requests.post(
        f"{CONNECTOR_URL}/create_collection",
        json={
            "collection_name": TEST_COLLECTION,
            "dimension": VECTOR_DIM
        }
    )
    
    if response.status_code != 200:
        print(f"Failed to create collection: {response.status_code} - {response.text}")
        return False
    print("Collection created successfully")
    
    # 4. Create different vector format variations
    print("\nTesting different vector formats...")
    
    # Base test vector
    base_vector = [float(i) for i in range(1, VECTOR_DIM+1)]
    print(f"Base vector: {base_vector}")
    
    # Test variation 1: Single vector as list of floats
    print("\n--- Test 1: Single vector ---")
    insert_data = {
        "collection_name": TEST_COLLECTION,
        "vectors": [base_vector]  # Single vector in a list
    }
    
    print(f"Format: {json.dumps(insert_data)}")
    response = requests.post(f"{CONNECTOR_URL}/insert", json=insert_data)
    print(f"Result: {response.status_code} - {response.text}")
    
    # Test variation 2: Pre-encoded JSON string
    print("\n--- Test 2: Pre-encoded JSON string ---")
    # Create a list of vectors
    vectors = [base_vector, [float(VECTOR_DIM-i+1) for i in range(1, VECTOR_DIM+1)]]
    
    # Encode as string first, then decode back to ensure proper JSON encoding
    vectors_json = json.dumps(vectors)
    vectors_decoded = json.loads(vectors_json)
    
    insert_data = {
        "collection_name": TEST_COLLECTION,
        "vectors": vectors_decoded
    }
    
    print(f"Format: {json.dumps({**insert_data, 'vectors': '[2 vectors]'})}")
    response = requests.post(f"{CONNECTOR_URL}/insert", json=insert_data)
    print(f"Result: {response.status_code} - {response.text}")
    
    # Test variation 3: Numpy array converted to list
    print("\n--- Test 3: NumPy array converted to list ---")
    np_vectors = np.array([base_vector], dtype=np.float32)
    
    insert_data = {
        "collection_name": TEST_COLLECTION,
        "vectors": np_vectors.tolist()
    }
    
    print(f"Format: {json.dumps({**insert_data, 'vectors': '[NumPy array as list]'})}")
    response = requests.post(f"{CONNECTOR_URL}/insert", json=insert_data)
    print(f"Result: {response.status_code} - {response.text}")
    
    # Test variation 4: Using native Python types and formats
    print("\n--- Test 4: Using native Python types ---")
    
    # Create a list of lists with explicit Python floats
    explicit_vectors = []
    explicit_vectors.append([float(val) for val in base_vector])
    
    insert_data = {
        "collection_name": TEST_COLLECTION,
        "vectors": explicit_vectors
    }
    
    print(f"Format: {json.dumps({**insert_data, 'vectors': '[Explicit Python floats]'})}")
    response = requests.post(f"{CONNECTOR_URL}/insert", json=insert_data)
    print(f"Result: {response.status_code} - {response.text}")
    
    print("\n===== Test Complete =====")
    return True

if __name__ == "__main__":
    test_format()
