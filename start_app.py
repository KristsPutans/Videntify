#!/usr/bin/env python3
"""
VidID Application Starter

This script starts the VidID application with the configured vector database.
"""

import os
import sys
import argparse
import subprocess
import signal
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import configuration modules
from src.config.config import ConfigManager

def start_api_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server using uvicorn.
    
    Args:
        host: Host to bind the server to
        port: Port to run the server on
        reload: Whether to enable auto-reload
    """
    print(f"Starting VidID API server on {host}:{port}")
    
    # Run the server using uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", host, 
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    # Start the server in the foreground
    try:
        print("VidID server is starting...")
        print("Press Ctrl+C to stop the server")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down VidID server...")

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "pydantic": "pydantic",
        "python-multipart": "multipart",
        "passlib": "passlib",
        "python-jose": "jose",
        "numpy": "numpy",
        "opencv-python-headless": "cv2"
    }
    
    missing_packages = []
    
    for package_name, module_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("The following required packages are missing:")
        print(", ".join(missing_packages))
        print("\nPlease install them using pip:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_vector_db_config():
    """Check and validate the vector database configuration."""
    try:
        config_manager = ConfigManager()
        vector_db_config = config_manager.get("vector_db", {})
        
        vector_db_type = vector_db_config.get("type")
        if not vector_db_type:
            print("No vector database type specified in configuration.")
            print("Using mock vector database as fallback.")
            return True
        
        print(f"Vector database type: {vector_db_type}")
        
        if vector_db_type != "mock":
            print(f"WARNING: Using {vector_db_type} - make sure it's accessible or the app will fall back to mock.")
        else:
            print("Using mock vector database for development.")
        
        # Check if fallback is enabled
        fallback_enabled = vector_db_config.get("fallback_to_mock", False)
        if fallback_enabled:
            print("Fallback to mock database is enabled if the primary database is unavailable.")
        
        return True
    except Exception as e:
        print(f"Error checking vector database configuration: {e}")
        return False

def main():
    """Main function to start the VidID application."""
    parser = argparse.ArgumentParser(description="Start the VidID application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    print("=== VidID Application Starter ===")
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        return 1
    
    # Check vector database configuration
    print("\nChecking vector database configuration...")
    if not check_vector_db_config():
        return 1
    
    # Start the API server
    print("\nStarting the API server...")
    start_api_server(host=args.host, port=args.port, reload=not args.no_reload)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
