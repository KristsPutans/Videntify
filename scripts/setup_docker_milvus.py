#!/usr/bin/env python3
"""
Deploy and configure Docker-based Milvus for Videntify

This script sets up a Docker-based Milvus environment with version compatibility
supported through a dedicated connector service.
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Try to import the ConfigManager
try:
    from src.config.config import ConfigManager
except ImportError:
    print("\033[91mError: Could not import ConfigManager. Make sure the Videntify package is installed.\033[0m")
    sys.exit(1)

# Define constants
MILVUS_CONNECTOR_DIR = project_root / "scripts" / "milvus_connector"
CONFIG_PATH = project_root / "config" / "config.json"

def check_docker_installed() -> bool:
    """Check if Docker is installed."""
    try:
        result = subprocess.run(["docker", "--version"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed."""
    try:
        result = subprocess.run(["docker-compose", "--version"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        return result.returncode == 0
    except FileNotFoundError:
        # Try docker compose (newer format)
        try:
            result = subprocess.run(["docker", "compose", "version"], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True,
                                check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

def get_docker_compose_command() -> str:
    """Get the appropriate docker-compose command."""
    # Check for docker-compose (older format)
    try:
        result = subprocess.run(["docker-compose", "--version"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        if result.returncode == 0:
            return "docker-compose"
    except FileNotFoundError:
        pass
    
    # Check for docker compose (newer format)
    try:
        result = subprocess.run(["docker", "compose", "version"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        if result.returncode == 0:
            return "docker compose"
    except FileNotFoundError:
        pass
    
    return ""

def deploy_milvus_connector() -> bool:
    """Deploy the Milvus connector using Docker Compose."""
    docker_compose_cmd = get_docker_compose_command()
    if not docker_compose_cmd:
        print("\033[91mError: Docker Compose not found. Please install Docker Compose.\033[0m")
        return False
    
    try:
        # Navigate to the Milvus connector directory
        os.chdir(MILVUS_CONNECTOR_DIR)
        
        # Build and deploy the Milvus connector
        if docker_compose_cmd == "docker-compose":
            subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
        else:
            subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
        
        print("\033[92m✅ Milvus connector deployed successfully\033[0m")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\033[91mError deploying Milvus connector: {e}\033[0m")
        return False
    except Exception as e:
        print(f"\033[91mUnexpected error deploying Milvus connector: {e}\033[0m")
        return False
    finally:
        # Return to the project root
        os.chdir(project_root)

def configure_videntify(host: str = "localhost", port: int = 5050) -> bool:
    """Configure Videntify to use the Milvus adapter."""
    try:
        # Load the configuration manager
        config_manager = ConfigManager()
        
        # Set up the vector_db configuration
        vector_db_config = {
            "type": "milvus_adapter",
            "host": host,
            "port": port,
            "dimension_mapping": {
                "cnn_features": 2048,
                "perceptual_hash": 64,
                "motion_pattern": 256,
                "audio_spectrogram": 512,
                "scene_transition": 128,
                "audio_transcript": 768
            },
            "index_params": {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 1024}
            },
            "search_params": {
                "metric_type": "L2",
                "params": {"nprobe": 16}
            }
        }
        
        # Update the configuration
        config_manager.set("vector_db", vector_db_config)
        config_manager.save(str(CONFIG_PATH))
        
        print("\033[92m✅ Updated Videntify configuration to use Milvus adapter\033[0m")
        return True
    except Exception as e:
        print(f"\033[91mError configuring Videntify: {e}\033[0m")
        return False

def check_connector_health(host: str = "localhost", port: int = 5050, max_attempts: int = 10) -> bool:
    """Check if the Milvus connector is healthy."""
    try:
        import requests
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"http://{host}:{port}/health", timeout=5)
                if response.status_code == 200:
                    print("\033[92m✅ Milvus connector is healthy\033[0m")
                    return True
            except requests.RequestException:
                pass
            
            print(f"Waiting for Milvus connector to become available (attempt {attempt+1}/{max_attempts})...")
            time.sleep(5)
        
        print("\033[91m❌ Milvus connector health check failed\033[0m")
        return False
    except ImportError:
        print("\033[93mWarning: requests module not found. Skipping health check.\033[0m")
        return True

def register_milvus_adapter() -> bool:
    """Register the Milvus adapter in the vector_db module."""
    try:
        adapter_file = project_root / "src" / "db" / "milvus_adapter.py"
        vector_db_file = project_root / "src" / "db" / "vector_db.py"
        
        if not adapter_file.exists():
            print(f"\033[91mError: Milvus adapter file {adapter_file} not found\033[0m")
            return False
        
        # Check if the adapter is already registered
        with open(vector_db_file, 'r') as f:
            content = f.read()
            if "milvus_adapter" in content and "MilvusAdapter" in content:
                print("\033[92m✅ Milvus adapter already registered\033[0m")
                return True
        
        # Import statements to add
        import_stmt = "from .milvus_adapter import MilvusAdapter\n"
        
        # Client mapping to update
        client_map_str = "    'milvus_adapter': MilvusAdapter,"
        
        # Update the vector_db.py file
        with open(vector_db_file, 'r') as f:
            lines = f.readlines()
        
        # Add import statement
        import_position = next((i for i, line in enumerate(lines) if line.startswith('from .')), 1)
        lines.insert(import_position, import_stmt)
        
        # Add client mapping
        client_map_position = next((i for i, line in enumerate(lines) if "'milvus'" in line), None)
        if client_map_position is not None:
            lines.insert(client_map_position + 1, client_map_str + '\n')
        else:
            client_map_position = next((i for i, line in enumerate(lines) if "'mock'" in line), None)
            if client_map_position is not None:
                lines.insert(client_map_position + 1, client_map_str + '\n')
            else:
                print("\033[91mError: Could not find position to add client mapping\033[0m")
                return False
        
        # Write the updated file
        with open(vector_db_file, 'w') as f:
            f.writelines(lines)
        
        print("\033[92m✅ Registered Milvus adapter in vector_db module\033[0m")
        return True
    except Exception as e:
        print(f"\033[91mError registering Milvus adapter: {e}\033[0m")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Deploy and configure Docker-based Milvus for Videntify')
    parser.add_argument('--host', type=str, default='localhost', help='Host for the Milvus connector')
    parser.add_argument('--port', type=int, default=5050, help='Port for the Milvus connector')
    parser.add_argument('--skip-deploy', action='store_true', help='Skip deployment of Milvus connector')
    parser.add_argument('--skip-config', action='store_true', help='Skip configuration of Videntify')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    print("=== Setting up Docker-based Milvus for Videntify ===\n")
    
    # Check Docker installation
    if not check_docker_installed():
        print("\033[91m❌ Docker is not installed. Please install Docker first.\033[0m")
        sys.exit(1)
    
    # Check Docker Compose installation
    if not check_docker_compose_installed():
        print("\033[91m❌ Docker Compose is not installed. Please install Docker Compose first.\033[0m")
        sys.exit(1)
    
    # Register the Milvus adapter
    if not register_milvus_adapter():
        print("\033[91m❌ Failed to register Milvus adapter\033[0m")
        sys.exit(1)
    
    # Deploy Milvus connector
    if not args.skip_deploy:
        if not deploy_milvus_connector():
            print("\033[91m❌ Failed to deploy Milvus connector\033[0m")
            sys.exit(1)
        
        # Check connector health
        if not check_connector_health(args.host, args.port):
            print("\033[93mWarning: Milvus connector health check failed, but continuing...\033[0m")
    
    # Configure Videntify
    if not args.skip_config:
        if not configure_videntify(args.host, args.port):
            print("\033[91m❌ Failed to configure Videntify\033[0m")
            sys.exit(1)
    
    print("\n=== Docker-based Milvus setup complete! ===")
    print("You can now use Milvus with Videntify for vector storage and similarity search.")
    print("\nTo test the integration, run:\n  python3 -m pytest tests/test_vector_db_integration.py -v")

if __name__ == "__main__":
    main()
