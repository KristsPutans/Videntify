#!/usr/bin/env python3
"""
Test Milvus Integration with Videntify

This script verifies that Milvus is running properly and that the
Videntify system can connect to it and perform basic operations.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db.vector_db import get_vector_db_client
from src.config.config import ConfigManager


def test_docker_status():
    """Check if Milvus Docker containers are running."""
    print("\n=== Checking Milvus Docker Containers ===")
    
    # Check milvus containers
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=milvus"],
        capture_output=True,
        text=True
    )
    
    if "milvus-standalone" in result.stdout:
        print("\u2705 Milvus server container is running")
    else:
        print("\u274c Milvus server container is NOT running")
    
    if "milvus-etcd" in result.stdout:
        print("\u2705 Milvus etcd container is running")
    else:
        print("\u274c Milvus etcd container is NOT running")
    
    if "milvus-minio" in result.stdout:
        print("\u2705 Milvus MinIO container is running")
    else:
        print("\u274c Milvus MinIO container is NOT running")
    
    return "milvus-standalone" in result.stdout


def test_milvus_connection():
    """Test connection to Milvus using the VectorDBClient."""
    print("\n=== Testing Milvus Connection ===")
    
    # Get the client
    client = get_vector_db_client()
    
    print(f"\u2139️ Vector DB client type: {type(client).__name__}")
    
    # Test connection
    if hasattr(client, 'is_connected') and callable(client.is_connected):
        connected = client.is_connected()
        if connected:
            print("\u2705 Successfully connected to Milvus")
        else:
            print("\u274c Failed to connect to Milvus")
        return connected
    
    print("\u26a0️ Client does not have is_connected method")
    return False


def test_vector_operations():
    """Test basic vector operations."""
    print("\n=== Testing Vector Operations ===")
    
    # Get the client
    client = get_vector_db_client()
    
    # List collections
    print("Listing collections...")
    try:
        collections = client.list_collections()
        print(f"\u2705 Found {len(collections)} collections:")
        for collection in collections:
            print(f"  - {collection}")
    except Exception as e:
        print(f"\u274c Error listing collections: {e}")
        collections = []
    
    # Test collection creation and deletion
    test_collection = "videntify_test_collection"
    
    # Check if test collection already exists
    if test_collection in collections:
        print(f"\u2139️ Test collection '{test_collection}' already exists")
        
        # Get collection stats
        try:
            stats = client.get_collection_stats(test_collection)
            print(f"\u2705 Collection stats: {stats}")
        except Exception as e:
            print(f"\u274c Error getting collection stats: {e}")
    else:
        print(f"Creating test collection '{test_collection}'...")
        try:
            created = client.create_collection(test_collection, 128)
            if created:
                print(f"\u2705 Created test collection '{test_collection}'")
            else:
                print(f"\u274c Failed to create test collection '{test_collection}'")
        except Exception as e:
            print(f"\u274c Error creating test collection: {e}")
    
    # Test vector insertion
    try:
        import numpy as np
        print("Inserting test vectors...")
        
        # Create 5 random vectors - make sure they're float32 for Milvus compatibility
        vectors_np = np.random.rand(5, 128).astype(np.float32)
        vectors = vectors_np.tolist()
        
        print(f"Vector shape: {vectors_np.shape}, dtype: {vectors_np.dtype}")
        
        # Add metadata - stringify for better compatibility
        metadata = [
            json.dumps({"source": "test", "timestamp": time.time(), "index": i})
            for i in range(5)
        ]
        
        # Insert vectors
        # Force recreation of collection with proper schema if needed
        if test_collection in client.list_collections():
            print(f"Dropping existing collection {test_collection} to ensure proper schema")
            client.drop_collection(test_collection)
            print(f"Creating fresh collection {test_collection} with proper schema")
            client.create_collection(test_collection, dimension=128, with_metadata=True)
            
        # Insert vectors
        result = client.insert(test_collection, vectors, metadata)
        
        if result and len(result) > 0:
            print(f"\u2705 Successfully inserted {len(result)} vectors")
            print(f"  IDs: {result[:3]}...")
        else:
            print("\u274c Failed to insert vectors")
    except Exception as e:
        print(f"\u274c Error inserting vectors: {e}")
    
    # Test vector search
    try:
        print("Searching for similar vectors...")
        
        # Create a query vector - ensure correct format for Milvus compatibility
        query_vector_np = np.random.rand(1, 128).astype(np.float32)
        query_vector = query_vector_np.tolist()
        print(f"Query vector shape: {query_vector_np.shape}, dtype: {query_vector_np.dtype}")
        
        # Search
        results = client.search(test_collection, query_vector, top_k=3)
        
        if results and len(results) > 0 and len(results[0]) > 0:
            print(f"\u2705 Search returned {len(results[0])} results")
            for i, result in enumerate(results[0]):
                print(f"  Result {i+1}: ID={result.get('id')}, Score={result.get('score'):.4f}")
        else:
            print("\u274c Search returned no results")
    except Exception as e:
        print(f"\u274c Error searching vectors: {e}")


def get_config_info():
    """Get configuration information."""
    print("\n=== Current Configuration ===")
    
    # Load configuration
    config_manager = ConfigManager()
    vector_db_config = config_manager.get('vector_db', {})
    
    # Print configuration
    print(f"Vector DB Type: {vector_db_config.get('type', 'unknown')}")
    print(f"Host: {vector_db_config.get('host', 'unknown')}")
    print(f"Port: {vector_db_config.get('port', 'unknown')}")
    
    # Print dimension mapping
    dimension_mapping = vector_db_config.get('dimension_mapping', {})
    if dimension_mapping:
        print("\nDimension Mapping:")
        for feature, dimension in dimension_mapping.items():
            print(f"  {feature}: {dimension}")


def main():
    """Main function."""
    print("===== Videntify Milvus Integration Test =====")
    
    # Override default configuration with test settings
    config = ConfigManager()
    # Set proper connector configuration
    config.set('vector_db', {
        'type': 'milvus',
        'host': 'host.docker.internal',  # Use host.docker.internal for Docker containers to reach the host
        'port': 19530,
        'connector_host': 'localhost',  # For the client to reach the connector
        'connector_port': 5050
    })
    
    # Check if Milvus containers are running
    containers_running = test_docker_status()
    
    if not containers_running:
        print("\n\u26a0️ Milvus containers are not running. Please start them first.")
        return
    
    # Get configuration information
    get_config_info()
    
    # Test connection to Milvus
    connected = test_milvus_connection()
    
    if not connected:
        print("\n\u26a0️ Could not connect to Milvus. Please check your configuration.")
        return
    
    # Test vector operations
    test_vector_operations()
    
    print("\n===== Milvus Integration Test Complete =====")


if __name__ == "__main__":
    main()
