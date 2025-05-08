#!/usr/bin/env python3
"""
Configure Videntify to use the running Milvus instance

This script will update the configuration files to point to the running Milvus service.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import ConfigManager

# Milvus configuration
MILVUS_CONFIG = {
    "type": "milvus",
    "host": "localhost",
    "port": 19530,
    "user": "",  # Leave empty for no authentication
    "password": "",  # Leave empty for no authentication
    "collection_prefix": "vidid_",
    "dimension_mapping": {
        "cnn_features": 2048,
        "perceptual_hash": 64,
        "motion_pattern": 256,
        "audio_spectrogram": 512
    },
    "index_params": {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {
            "nlist": 1024
        }
    },
    "search_params": {
        "params": {
            "nprobe": 16
        }
    }
}

def configure_videntify():
    """Configure Videntify to use Milvus."""
    try:
        # Install pymilvus if needed
        try:
            import pymilvus
            print("\u2705 PyMilvus already installed")
        except ImportError:
            print("Installing pymilvus package...")
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pymilvus"],
                check=True
            )
            print("\u2705 Installed pymilvus package")
        
        # Update the vector_db configuration
        config_manager = ConfigManager()
        
        # Get current config
        current_config = config_manager.get("vector_db", {})
        
        # Merge with Milvus config
        updated_config = {**current_config, **MILVUS_CONFIG}
        
        # Save the configuration
        config_manager.set("vector_db", updated_config)
        # Use default config path
        config_path = os.path.join(project_root, "config", "config.json")
        config_manager.save(config_path)
        
        print("\u2705 Updated Videntify configuration to use Milvus")
        
        # Test connection to Milvus
        try:
            from pymilvus import connections
            connections.connect(
                alias="default", 
                host=MILVUS_CONFIG["host"],
                port=MILVUS_CONFIG["port"]
            )
            print("\u2705 Successfully connected to Milvus")
            connections.disconnect("default")
            return True
        except Exception as e:
            print(f"\u274c Failed to connect to Milvus: {e}")
            print("  Configuration has been updated, but connection test failed.")
            print("  Make sure Milvus is running on localhost:19530")
            return False
            
    except Exception as e:
        print(f"\u274c Error configuring Videntify: {e}")
        return False

if __name__ == "__main__":
    print("=== Configuring Videntify to use Milvus ===\n")
    configure_videntify()
    print("\nConfiguration complete!")
    print("You can now use Milvus with Videntify for vector storage and similarity search.")
