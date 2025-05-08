#!/usr/bin/env python3
"""
Vector Database Configuration Utility

This script helps manage vector database configurations for the VidID system.
It can switch between different vector database backends and configure connection settings.
"""

import os
import json
import sys
import argparse
from pathlib import Path

# Add project root to path to allow importing modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

CONFIG_DIR = project_root / "config"
MAIN_CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config(config_file=None):
    """Load configuration from file."""
    if config_file is None:
        config_file = MAIN_CONFIG_FILE
    else:
        config_file = Path(config_file)
        
    if not config_file.exists():
        print(f"Config file {config_file} not found.")
        return None
        
    with open(config_file, 'r') as f:
        return json.load(f)


def save_config(config, output_file=None):
    """Save configuration to file."""
    if output_file is None:
        output_file = MAIN_CONFIG_FILE
    else:
        output_file = Path(output_file)
        
    # Create parent directories if they don't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {output_file}")
    return True


def merge_configs(base_config, overlay_config):
    """Merge two configurations, with overlay_config taking precedence."""
    if isinstance(base_config, dict) and isinstance(overlay_config, dict):
        for key, value in overlay_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                merge_configs(base_config[key], value)
            else:
                base_config[key] = value
    return base_config


def list_available_configs():
    """List available vector database configurations."""
    configs = []
    for file in CONFIG_DIR.glob("vector_db_*.json"):
        configs.append(file.name)
    return configs


def switch_vector_db(db_type, output_file=None):
    """Switch to a different vector database configuration."""
    # Load the main configuration
    main_config = load_config()
    if main_config is None:
        print(f"Creating new configuration file at {MAIN_CONFIG_FILE}")
        main_config = {}
    
    # Find the requested vector database configuration
    db_config_file = CONFIG_DIR / f"vector_db_{db_type}.json"
    if not db_config_file.exists():
        print(f"Vector database configuration for {db_type} not found at {db_config_file}")
        return False
    
    # Load the vector database configuration
    db_config = load_config(db_config_file)
    if db_config is None:
        return False
    
    # Merge the configurations
    merged_config = merge_configs(main_config, db_config)
    
    # Save the merged configuration
    return save_config(merged_config, output_file)


def test_vector_db_config():
    """Test the current vector database configuration."""
    try:
        from src.db.vector_db import get_vector_db_client
        
        print("Testing vector database connection...")
        client = get_vector_db_client()
        
        if client is None:
            print("Failed to create vector database client. Check configuration.")
            return False
        
        print(f"Successfully created {client.__class__.__name__}")
        
        if not client.connect():
            print("Failed to connect to vector database. Check connection settings.")
            return False
        
        print("Successfully connected to vector database!")
        return True
        
    except Exception as e:
        print(f"Error testing vector database configuration: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Vector Database Configuration Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available vector database configurations")
    
    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch to a different vector database configuration")
    switch_parser.add_argument("db_type", help="Vector database type (e.g., milvus, pinecone, faiss, mock)")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test the current vector database configuration")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "list":
        configs = list_available_configs()
        if not configs:
            print("No vector database configurations found.")
        else:
            print("Available vector database configurations:")
            for config in configs:
                print(f"  - {config}")
    elif args.command == "switch":
        db_type = args.db_type.lower()
        if switch_vector_db(db_type):
            print(f"Successfully switched to {db_type} vector database configuration.")
        else:
            print(f"Failed to switch to {db_type} vector database configuration.")
    elif args.command == "test":
        if test_vector_db_config():
            print("Vector database configuration test passed!")
        else:
            print("Vector database configuration test failed.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
