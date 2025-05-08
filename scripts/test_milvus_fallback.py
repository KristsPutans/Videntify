#!/usr/bin/env python3
"""
Milvus Fallback Adapter Test

This script tests the MilvusFallbackAdapter's ability to work with or without
a functioning Milvus server by gracefully falling back to local operations.
"""

import os
import sys
import time
import json
import numpy as np

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.milvus_fallback_adapter import MilvusFallbackAdapter

# Configuration
FALLBACK_DIR = os.path.join(os.getcwd(), 'milvus_fallback_test')
TEST_COLLECTION = 'fallback_test_collection'
VECTOR_DIM = 8

def create_test_vectors(count: int, dim: int):
    """Create random test vectors."""
    return [list(map(float, np.random.rand(dim))) for _ in range(count)]

def run_test():
    print("\n====== MILVUS FALLBACK ADAPTER TEST ======\n")
    
    # Initialize the adapter
    print("Initializing MilvusFallbackAdapter...")
    adapter = MilvusFallbackAdapter({
        'connector_host': 'localhost',
        'connector_port': 5050,
        'fallback_dir': FALLBACK_DIR,
        'fallback_mode': 'auto',  # Try Milvus first, then fallback
        'timeout': 5  # Short timeout for testing
    })
    
    # Test connection status
    print(f"\nConnection status: {'Connected' if adapter.is_connected() else 'Disconnected'}")
    
    # List collections
    print("\nListing collections...")
    collections = adapter.list_collections()
    print(f"Found {len(collections)} collections: {collections}")
    
    # Clean up existing test collection
    if TEST_COLLECTION in collections:
        print(f"\nDropping existing collection {TEST_COLLECTION}...")
        result = adapter.drop_collection(TEST_COLLECTION)
        print(f"Drop result: {result}")
    
    # Create a test collection
    print(f"\nCreating collection {TEST_COLLECTION}...")
    result = adapter.create_collection(TEST_COLLECTION, VECTOR_DIM)
    print(f"Create result: {result}")
    
    # Check if collection was created
    collections = adapter.list_collections()
    if TEST_COLLECTION in collections:
        print(f"✅ Collection {TEST_COLLECTION} created successfully")
    else:
        print(f"❌ Failed to create collection {TEST_COLLECTION}")
        return
    
    # Insert vectors
    print("\nInserting vectors...")
    vectors = create_test_vectors(5, VECTOR_DIM)
    metadata = [{"source": f"test_{i}"} for i in range(len(vectors))]
    
    ids = adapter.insert(TEST_COLLECTION, vectors, metadata)
    print(f"Inserted {len(ids)} vectors with IDs: {ids}")
    
    # Search vectors
    print("\nSearching for similar vectors...")
    query_vectors = [vectors[0]]  # Use the first vector as query
    results = adapter.search(TEST_COLLECTION, query_vectors, top_k=3)
    
    print(f"Search results for query vector:")
    for i, result_list in enumerate(results):
        print(f"  Query {i+1} ({len(result_list)} results):")
        for j, match in enumerate(result_list):
            print(f"    Match {j+1}: ID={match.get('id')}, Score={match.get('score'):.4f}")
    
    # Get collection stats
    print("\nGetting collection stats...")
    stats = adapter.get_collection_stats(TEST_COLLECTION)
    print(f"Collection stats: {json.dumps(stats, indent=2)}")
    
    # Test with fallback mode forced
    print("\n----- TESTING FORCED FALLBACK MODE -----")
    
    # Create a new adapter with forced fallback mode
    print("\nInitializing adapter with forced fallback mode...")
    fallback_adapter = MilvusFallbackAdapter({
        'connector_host': 'localhost',
        'connector_port': 5050,
        'fallback_dir': FALLBACK_DIR,
        'fallback_mode': 'always',  # Always use fallback
        'timeout': 5
    })
    
    # Insert more vectors
    print("\nInserting vectors in fallback mode...")
    more_vectors = create_test_vectors(3, VECTOR_DIM)
    more_metadata = [{"source": f"fallback_{i}"} for i in range(len(more_vectors))]
    
    more_ids = fallback_adapter.insert(TEST_COLLECTION, more_vectors, more_metadata)
    print(f"Inserted {len(more_ids)} more vectors with IDs: {more_ids}")
    
    # Search again
    print("\nSearching in fallback mode...")
    query_vectors = [more_vectors[0]]  # Use the first of the new vectors
    results = fallback_adapter.search(TEST_COLLECTION, query_vectors, top_k=5)
    
    print(f"Search results in fallback mode:")
    for i, result_list in enumerate(results):
        print(f"  Query {i+1} ({len(result_list)} results):")
        for j, match in enumerate(result_list):
            print(f"    Match {j+1}: ID={match.get('id')}, Score={match.get('score'):.4f}")
    
    print("\n====== TEST COMPLETED ======\n")

if __name__ == "__main__":
    run_test()
