#!/usr/bin/env python3
"""
Direct Milvus Test

This script directly uses pymilvus to test Milvus functionality without the connector layer.
This will help us diagnose if the issue is with our connector or with Milvus itself.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Try to import pymilvus directly
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections, utility

# Constants
COLLECTION_NAME = "videntify_direct_test"
VECTOR_DIM = 128
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530

def connect_to_milvus():
    """Connect to Milvus server."""
    print(f"\n=== Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT} ===")
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        print("u2705 Connected to Milvus successfully")
        return True
    except Exception as e:
        print(f"u274c Failed to connect to Milvus: {type(e).__name__}: {e}")
        return False

def create_collection():
    """Create a test collection."""
    print(f"\n=== Creating Collection '{COLLECTION_NAME}' ===")
    
    # Check if collection exists and drop it
    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME} exists, dropping it...")
        utility.drop_collection(COLLECTION_NAME)
    
    # Define fields for the collection
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
    ]
    
    # Create schema and collection
    try:
        schema = CollectionSchema(fields=fields, description=f"Test collection for {COLLECTION_NAME}")
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        print(f"u2705 Created collection {COLLECTION_NAME}")
        return collection
    except Exception as e:
        print(f"u274c Failed to create collection: {type(e).__name__}: {e}")
        return None

def insert_vectors(collection):
    """Insert test vectors into the collection."""
    print("\n=== Inserting Vectors ===")
    
    # Create test data
    try:
        # Generate random vectors
        vectors_count = 3
        vectors = np.random.rand(vectors_count, VECTOR_DIM).astype(np.float32)
        
        # Convert numpy array to Python list for insertion
        vectors_data = vectors.tolist()
        
        # Create metadata
        metadata = [f'{{"test_id": {i}, "timestamp": {time.time()}}}' for i in range(vectors_count)]
        
        # Prepare data for insertion
        data = [
            vectors_data,  # vector field
            metadata       # metadata field
        ]
        
        # Insert data
        print(f"Inserting {vectors_count} vectors...")
        insert_result = collection.insert(data=[vectors_data, metadata])
        
        # Print result
        print(f"u2705 Successfully inserted vectors. Primary keys: {insert_result.primary_keys}")
        
        # Flush the collection to ensure data is available for search
        collection.flush()
        print("Collection flushed")
        
        return vectors_data  # Return vectors for search
    except Exception as e:
        print(f"u274c Failed to insert vectors: {type(e).__name__}: {e}")
        return None

def search_vectors(collection, vectors):
    """Search for similar vectors."""
    print("\n=== Searching Vectors ===")
    
    try:
        # Load collection for search
        print("Loading collection...")
        collection.load()
        
        # Use the first vector as the query vector
        query_vector = [vectors[0]]
        
        # Search parameters
        search_params = {"metric_type": "L2"}
        
        # Search
        print("Searching for similar vectors...")
        results = collection.search(
            data=query_vector,      # Query vectors
            anns_field="vector",    # Search in the vector field
            param=search_params,    # Search parameters
            limit=3,               # Top-k
            expr=None               # Filter expression
        )
        
        # Print results
        for i, result in enumerate(results):
            print(f"\nResult for query vector {i}:")
            for j, hit in enumerate(result):
                print(f"  Top {j+1}: ID={hit.id}, Distance={hit.distance}")
        
        print("u2705 Search completed successfully")
        return True
    except Exception as e:
        print(f"u274c Failed to search vectors: {type(e).__name__}: {e}")
        return False

def main():
    """Run the direct Milvus test."""
    print("====== Direct Milvus Test ======")
    
    # Step 1: Connect to Milvus
    if not connect_to_milvus():
        print("Exiting due to connection failure")
        return
    
    # Step 2: Create collection
    collection = create_collection()
    if not collection:
        print("Exiting due to collection creation failure")
        return
    
    # Step 3: Insert vectors
    vectors = insert_vectors(collection)
    if not vectors:
        print("Exiting due to insertion failure")
        return
    
    # Step 4: Search vectors
    search_vectors(collection, vectors)
    
    print("\n====== Direct Milvus Test Completed ======")

if __name__ == "__main__":
    main()
