#!/usr/bin/env python3
"""
Simple script to test Milvus connection
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import ConfigManager

def test_milvus_connection():
    """Test connection to Milvus."""
    # Load configuration
    config_manager = ConfigManager()
    vector_db_config = config_manager.get("vector_db", {})
    
    print("Vector DB Configuration:")
    for key, value in vector_db_config.items():
        if key not in ["dimension_mapping", "index_params", "search_params"]:
            print(f"  {key}: {value}")
    
    # Try to connect to Milvus
    print("\nAttempting to connect to Milvus...")
    try:
        from pymilvus import connections
        
        host = vector_db_config.get("host", "localhost")
        port = vector_db_config.get("port", 19530)
        
        connections.connect(
            alias="default", 
            host=host,
            port=port
        )
        
        print("\u2705 Successfully connected to Milvus!")
        
        # Check for collections
        from pymilvus import utility
        
        collections = utility.list_collections()
        print(f"\nFound {len(collections)} collections:")
        for collection in collections:
            print(f"  - {collection}")
        
        # Disconnect
        connections.disconnect("default")
        print("\nDisconnected from Milvus")
        
        return True
    except ImportError:
        print("\u274c PyMilvus not installed. Install with: python3 -m pip install pymilvus")
        return False
    except Exception as e:
        print(f"\u274c Error connecting to Milvus: {e}")
        print("\nMake sure Milvus is running. Check with: docker ps | grep milvus")
        return False

if __name__ == "__main__":
    print("=== Testing Milvus Connection ===\n")
    test_milvus_connection()
