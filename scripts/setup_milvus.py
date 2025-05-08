#!/usr/bin/env python3
"""
Milvus Setup Script for Videntify

This script helps set up and test Milvus as a production vector database for Videntify.
It includes functionality to:
1. Install required dependencies
2. Run Milvus using Docker Compose
3. Configure Videntify to use Milvus
4. Perform basic validation tests
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import ConfigManager
from src.db.vector_db import VectorDBType


DOCKER_COMPOSE_CONTENT = """
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.0
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2020-12-03T00-03-10Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.0.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"

networks:
  default:
    name: milvus
"""

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


def check_docker():
    """Check if Docker and Docker Compose are installed and running."""
    try:
        # Check Docker
        docker_version = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ Docker installed: {docker_version.stdout.strip()}")
        
        # Check Docker Compose
        compose_version = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ Docker Compose installed: {compose_version.stdout.strip()}")
        
        # Check Docker is running
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        print("✅ Docker daemon is running")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker check failed: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Docker or Docker Compose not found: {e}")
        return False


def setup_docker_compose():
    """Create a Docker Compose file for Milvus."""
    docker_dir = project_root / "docker"
    docker_dir.mkdir(exist_ok=True)
    
    compose_file = docker_dir / "milvus-docker-compose.yml"
    
    with open(compose_file, "w") as f:
        f.write(DOCKER_COMPOSE_CONTENT)
    
    print(f"✅ Created Docker Compose file at: {compose_file}")
    return compose_file


def start_milvus(compose_file):
    """Start Milvus using Docker Compose."""
    try:
        # Create volumes directory
        volumes_dir = project_root / "docker" / "volumes"
        volumes_dir.mkdir(exist_ok=True)
        
        # Start containers
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d"],
            check=True
        )
        
        print("✅ Started Milvus containers")
        print("⏳ Waiting for Milvus to be ready...")
        
        # Wait for Milvus to be ready
        max_retries = 10
        retry_interval = 5
        
        for i in range(max_retries):
            try:
                subprocess.run(
                    ["docker", "exec", "milvus-standalone", "curl", "-s", "localhost:9091/api/v1/health"],
                    check=True, capture_output=True
                )
                print("✅ Milvus is ready!")
                return True
            except subprocess.CalledProcessError:
                print(f"⏳ Milvus not ready yet, retrying ({i+1}/{max_retries})...")
                time.sleep(retry_interval)
        
        print("❌ Milvus failed to start properly")
        return False
    except Exception as e:
        print(f"❌ Error starting Milvus: {e}")
        return False


def configure_videntify(install_pymilvus=True):
    """Configure Videntify to use Milvus."""
    try:
        if install_pymilvus:
            print("Installing pymilvus package...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pymilvus"],
                check=True
            )
            print("✅ Installed pymilvus package")
        
        # Update the vector_db configuration
        config_manager = ConfigManager()
        
        # Get current config
        current_config = config_manager.get("vector_db", {})
        
        # Merge with Milvus config
        updated_config = {**current_config, **MILVUS_CONFIG}
        
        # Save the configuration
        config_manager.set("vector_db", updated_config)
        config_manager.save()
        
        print("✅ Updated Videntify configuration to use Milvus")
        return True
    except Exception as e:
        print(f"❌ Error configuring Videntify: {e}")
        return False


def test_milvus_connection():
    """Test the connection to Milvus."""
    try:
        from src.db.vector_db import get_vector_db_client
        
        # Get the Milvus client
        client = get_vector_db_client()
        
        # Connect to Milvus
        connected = client.connect()
        
        if connected:
            print("✅ Successfully connected to Milvus")
            
            # Create a test collection
            collection_name = "vidid_test_collection"
            dimension = 128
            
            created = client.create_collection(collection_name, dimension)
            
            if created:
                print(f"✅ Successfully created test collection: {collection_name}")
                
                # List collections
                collections = client.list_collections()
                print(f"📋 Available collections: {collections}")
                
                # Drop the test collection
                dropped = client.drop_collection(collection_name)
                
                if dropped:
                    print(f"✅ Successfully dropped test collection: {collection_name}")
                else:
                    print(f"❌ Failed to drop test collection: {collection_name}")
            else:
                print(f"❌ Failed to create test collection: {collection_name}")
            
            # Disconnect
            client.disconnect()
            print("✅ Successfully disconnected from Milvus")
            
            return True
        else:
            print("❌ Failed to connect to Milvus")
            return False
    except Exception as e:
        print(f"❌ Error testing Milvus connection: {e}")
        return False


def import_sample_data():
    """Import sample data into Milvus for testing."""
    try:
        import numpy as np
        from src.core.vector_db_integration import VectorDBIntegration
        from src.core.feature_extraction import FeatureType
        
        print("Importing sample data into Milvus...")
        
        # Create a VectorDBIntegration instance
        vector_db = VectorDBIntegration()
        
        # Generate some random feature vectors
        num_features = 10
        feature_types = [
            (FeatureType.CNN_FEATURES, 2048),
            (FeatureType.PERCEPTUAL_HASH, 64),
            (FeatureType.MOTION_PATTERN, 256),
            (FeatureType.AUDIO_SPECTROGRAM, 512)
        ]
        
        for feature_type, dimension in feature_types:
            print(f"Importing {num_features} {feature_type.name} features...")
            
            for i in range(num_features):
                # Generate a random feature vector
                feature_vector = np.random.rand(dimension).astype(np.float32)
                
                # Generate a random video ID
                video_id = f"sample_video_{i}"
                
                # Store the feature vector
                feature_id = vector_db.store_video_feature(
                    video_id=video_id,
                    feature_type=feature_type,
                    feature_vector=feature_vector,
                    metadata={
                        "source": "sample_data",
                        "index": i
                    }
                )
                
                if feature_id:
                    print(f"  ✅ Stored {feature_type.name} feature for {video_id}")
                else:
                    print(f"  ❌ Failed to store {feature_type.name} feature for {video_id}")
        
        print("✅ Sample data import completed")
        return True
    except Exception as e:
        print(f"❌ Error importing sample data: {e}")
        return False


def stop_milvus(compose_file):
    """Stop Milvus containers."""
    try:
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "down"],
            check=True
        )
        print("✅ Stopped Milvus containers")
        return True
    except Exception as e:
        print(f"❌ Error stopping Milvus: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Milvus Setup Script for Videntify")
    parser.add_argument("--install", action="store_true", help="Install and start Milvus")
    parser.add_argument("--configure", action="store_true", help="Configure Videntify to use Milvus")
    parser.add_argument("--test", action="store_true", help="Test Milvus connection")
    parser.add_argument("--import-data", action="store_true", help="Import sample data")
    parser.add_argument("--stop", action="store_true", help="Stop Milvus containers")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    
    args = parser.parse_args()
    
    # Default to --all if no arguments provided
    if not any(vars(args).values()):
        args.all = True
    
    print("=== Milvus Setup for Videntify ===\n")
    
    compose_file = None
    
    if args.all or args.install:
        print("\n📋 Checking Docker installation...")
        if not check_docker():
            print("\n❌ Docker or Docker Compose not found or not running. Please install and start Docker.")
            return 1
        
        print("\n📋 Setting up Docker Compose for Milvus...")
        compose_file = setup_docker_compose()
        
        print("\n📋 Starting Milvus...")
        if not start_milvus(compose_file):
            print("\n❌ Failed to start Milvus. Please check the error messages above.")
            return 1
    
    if args.all or args.configure:
        print("\n📋 Configuring Videntify to use Milvus...")
        if not configure_videntify():
            print("\n❌ Failed to configure Videntify. Please check the error messages above.")
            return 1
    
    if args.all or args.test:
        print("\n📋 Testing Milvus connection...")
        if not test_milvus_connection():
            print("\n❌ Connection test failed. Please check the error messages above.")
            return 1
    
    if args.all or args.import_data:
        print("\n📋 Importing sample data...")
        if not import_sample_data():
            print("\n❌ Sample data import failed. Please check the error messages above.")
            return 1
    
    if args.all or args.stop:
        if not compose_file:
            compose_file = project_root / "docker" / "milvus-docker-compose.yml"
        
        print("\n📋 Stopping Milvus containers...")
        if not stop_milvus(compose_file):
            print("\n❌ Failed to stop Milvus. Please check the error messages above.")
            return 1
    
    print("\n✅ Milvus setup completed successfully!")
    print("\nTo use Milvus with Videntify:")
    print("1. Start Milvus: ./scripts/setup_milvus.py --install")
    print("2. Configure Videntify: ./scripts/setup_milvus.py --configure")
    print("3. Import sample data: ./scripts/setup_milvus.py --import-data")
    print("4. When done, stop Milvus: ./scripts/setup_milvus.py --stop")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
