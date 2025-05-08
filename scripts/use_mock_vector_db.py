#!/usr/bin/env python3
"""
Configure Videntify to use the Mock Vector Database

This script updates the configuration to use the mock vector database implementation,
which is ideal for development and testing without external dependencies.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Mock vector database configuration
MOCK_VECTOR_DB_CONFIG = {
    "type": "mock",
    "storage_path": str(project_root / "data" / "mock_vector_db"),
    "simulate_latency_ms": 10,  # Add a small delay to simulate network latency
    "dimensions": {
        "cnn_features": 2048,
        "perceptual_hash": 64,
        "motion_pattern": 256,
        "audio_spectrogram": 512
    }
}

def update_configuration():
    """Update the configuration to use the mock vector database."""
    try:
        # Find the config file
        config_path = project_root / "config" / "config.json"
        
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(exist_ok=True)
        
        # Load existing config or create new one
        if config_path.exists():
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    config = {}
        else:
            config = {}
        
        # Update vector_db configuration
        config["vector_db"] = MOCK_VECTOR_DB_CONFIG
        
        # Create the storage directory
        os.makedirs(MOCK_VECTOR_DB_CONFIG["storage_path"], exist_ok=True)
        
        # Save the updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\u2705 Updated configuration at: {config_path}")
        print(f"\u2705 Vector database set to: {MOCK_VECTOR_DB_CONFIG['type']}")
        print(f"\u2705 Storage path: {MOCK_VECTOR_DB_CONFIG['storage_path']}")
        
        return True
    except Exception as e:
        print(f"\u274c Error updating configuration: {e}")
        return False

def test_mock_vector_db():
    """Test that the mock vector database can be initialized."""
    try:
        from src.db.vector_db import get_vector_db_client
        
        # Get the vector database client
        client = get_vector_db_client()
        
        # Check the type
        from src.db.mock_vector_db import MockVectorDBClient
        if isinstance(client, MockVectorDBClient):
            print("\u2705 Successfully initialized MockVectorDBClient")
            
            # Test basic operations
            if client.connect():
                print("\u2705 Connected to mock vector database")
                
                # Test creating a collection
                collection_name = "test_collection"
                dimension = 128
                
                if client.create_collection(collection_name, dimension):
                    print(f"\u2705 Created test collection: {collection_name}")
                    
                    # List collections
                    collections = client.list_collections()
                    print(f"\u2705 Available collections: {collections}")
                    
                    # Drop the test collection
                    if client.drop_collection(collection_name):
                        print(f"\u2705 Dropped test collection: {collection_name}")
                    else:
                        print(f"\u274c Failed to drop test collection: {collection_name}")
                else:
                    print(f"\u274c Failed to create test collection: {collection_name}")
                
                return True
            else:
                print("\u274c Failed to connect to mock vector database")
                return False
        else:
            print(f"\u274c Expected MockVectorDBClient, got {type(client).__name__}")
            return False
    except Exception as e:
        print(f"\u274c Error testing mock vector database: {e}")
        return False

def main():
    print("=== Configuring Videntify to use Mock Vector Database ===\n")
    
    # Update configuration
    if update_configuration():
        print("\nTesting mock vector database configuration...")
        test_mock_vector_db()
    
    print("\nConfiguration complete!")
    print("You can now use the mock vector database with Videntify for development and testing.")
    print("When you're ready to switch to Milvus or another vector database, you can update the configuration accordingly.")

if __name__ == "__main__":
    main()
