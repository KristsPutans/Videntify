#!/usr/bin/env python3
"""
Minimal connector test for Milvus

This script directly tests the connector's create collection and insert functionality
with minimal vectors to pinpoint data format issues.
"""

import os
import sys
import time
import json
import requests
import numpy as np

# Constants
CONNECTOR_URL = "http://localhost:5050"
TEST_COLLECTION = "minimal_test_collection"
TIMEOUT = 30  # seconds

# Connect to Milvus through connector
def connector_connect():
    print("Connecting to Milvus via connector...")
    response = requests.post(
        f"{CONNECTOR_URL}/connect",
        json={
            "host": "host.docker.internal", 
            "port": 19530, 
            "user": "", 
            "db_name": "default"
        },
        timeout=TIMEOUT
    )
    
    if response.status_code == 200:
        print("Connected successfully")
        return True
    else:
        print(f"Connection failed: {response.status_code} - {response.text}")
        return False

# Create a test collection with absolute minimum configuration
def create_minimal_collection():
    print(f"\nCreating minimal collection: {TEST_COLLECTION}")
    
    # First check if collection exists
    response = requests.get(f"{CONNECTOR_URL}/list_collections", timeout=TIMEOUT)
    if response.status_code == 200:
        collections = response.json().get("collections", [])
        if TEST_COLLECTION in collections:
            print(f"Collection {TEST_COLLECTION} exists, dropping it...")
            requests.post(
                f"{CONNECTOR_URL}/drop_collection",
                json={"collection_name": TEST_COLLECTION},
                timeout=TIMEOUT
            )
    
    # Create new collection with absolute minimum parameters
    response = requests.post(
        f"{CONNECTOR_URL}/create_collection",
        json={
            "collection_name": TEST_COLLECTION,
            "dimension": 2,  # The smallest possible dimension
            "with_metadata": False,  # No metadata to simplify
            "create_index": False,  # Don't create index
            "skip_loading": True  # Skip loading to avoid timeouts
        },
        timeout=TIMEOUT
    )
    
    if response.status_code == 200:
        print("Collection created successfully")
        return True
    else:
        print(f"Collection creation failed: {response.status_code} - {response.text}")
        return False

# Insert minimal vectors
def insert_minimal_vectors():
    print("\nInserting minimal vectors")
    
    # Create 2 tiny vectors
    vectors = [
        [1.0, 2.0],
        [3.0, 4.0]
    ]
    
    # Insert vectors with no metadata
    response = requests.post(
        f"{CONNECTOR_URL}/insert",
        json={
            "collection_name": TEST_COLLECTION,
            "vectors": vectors
        },
        timeout=TIMEOUT
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Vectors inserted successfully. IDs: {result.get('ids')}")
        return True
    else:
        print(f"Vector insertion failed: {response.status_code} - {response.text}")
        return False

# Main function
def main():
    print("=== Minimal Milvus Connector Test ===")
    
    # Step 1: Connect to Milvus
    if not connector_connect():
        print("Connection failed. Exiting.")
        return
    
    # Step 2: Create minimal collection
    if not create_minimal_collection():
        print("Collection creation failed. Exiting.")
        return
    
    # Step 3: Insert minimal vectors
    if not insert_minimal_vectors():
        print("Vector insertion failed. Exiting.")
        return
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    main()
