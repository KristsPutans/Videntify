#!/usr/bin/env python3
"""
Manual API Testing Script

This script tests the identification API with the vector database integration
by making direct requests to the endpoints.
"""

import os
import sys
import json
import time
import uuid
import logging
import asyncio
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/api"


async def test_start_server():
    """Start the API server if not already running"""
    import subprocess
    import sys
    import time
    
    # Check if server is already running
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            logger.info("API server is already running")
            return True
    except requests.exceptions.ConnectionError:
        logger.info("API server is not running, starting it...")
    
    # Start the server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    for _ in range(10):
        time.sleep(1)
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                logger.info("API server started successfully")
                return server_process
        except requests.exceptions.ConnectionError:
            continue
    
    logger.error("Failed to start API server")
    server_process.terminate()
    return None


async def test_video_identification(video_path: str) -> Dict[str, Any]:
    """Test the video identification endpoint"""
    logger.info(f"Testing video identification with {video_path}")
    
    # Read video file
    with open(video_path, "rb") as f:
        video_data = f.read()
    
    # Prepare multipart form data
    files = {
        "video_file": (os.path.basename(video_path), video_data, "video/mp4")
    }
    data = {
        "algorithms": ["cosine_similarity"],
        "max_results": 5,
        "threshold": 0.7,
        "save_query": True
    }
    
    # Make request
    url = f"{API_BASE_URL}/identify/video"
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Video identification successful: {json.dumps(result, indent=2)}")
        return result
    else:
        logger.error(f"Video identification failed: {response.status_code} - {response.text}")
        return {"error": response.text}


async def test_frame_identification(frame_path: str) -> Dict[str, Any]:
    """Test the frame identification endpoint"""
    logger.info(f"Testing frame identification with {frame_path}")
    
    # Read frame file
    with open(frame_path, "rb") as f:
        frame_data = f.read()
    
    # Prepare multipart form data
    files = {
        "frame_file": (os.path.basename(frame_path), frame_data, "image/jpeg")
    }
    data = {
        "algorithms": ["cosine_similarity"],
        "max_results": 5,
        "threshold": 0.7,
        "save_query": True
    }
    
    # Make request
    url = f"{API_BASE_URL}/identify/frame"
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Frame identification successful: {json.dumps(result, indent=2)}")
        return result
    else:
        logger.error(f"Frame identification failed: {response.status_code} - {response.text}")
        return {"error": response.text}


async def test_audio_identification(audio_path: str) -> Dict[str, Any]:
    """Test the audio identification endpoint"""
    logger.info(f"Testing audio identification with {audio_path}")
    
    # Read audio file
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    # Prepare multipart form data
    files = {
        "audio_file": (os.path.basename(audio_path), audio_data, "audio/mpeg")
    }
    data = {
        "algorithms": ["cosine_similarity"],
        "max_results": 5,
        "threshold": 0.7,
        "save_query": True
    }
    
    # Make request
    url = f"{API_BASE_URL}/identify/audio"
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Audio identification successful: {json.dumps(result, indent=2)}")
        return result
    else:
        logger.error(f"Audio identification failed: {response.status_code} - {response.text}")
        return {"error": response.text}


async def test_query_history(query_id: str) -> Dict[str, Any]:
    """Test the query history endpoint"""
    logger.info(f"Testing query history for query ID {query_id}")
    
    # Make request
    url = f"{API_BASE_URL}/identify/query/{query_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Query history successful: {json.dumps(result, indent=2)}")
        return result
    else:
        logger.error(f"Query history failed: {response.status_code} - {response.text}")
        return {"error": response.text}


async def main():
    """Main function"""
    # Start the server if not already running
    server_process = await test_start_server()
    
    try:
        # Ask user what to test
        print("\nVidID API Testing Tool")
        print("====================\n")
        print("Available tests:")
        print("1. Video identification")
        print("2. Frame identification")
        print("3. Audio identification")
        print("4. Query history")
        print("5. Run all tests")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ")
        
        if choice == "1" or choice == "5":
            # Test video identification
            video_path = input("Enter path to test video file (or leave empty for default): ")
            if not video_path:
                video_path = os.path.join(project_root, "tests", "data", "sample_video.mp4")
                # Create test directory if it doesn't exist
                os.makedirs(os.path.dirname(video_path), exist_ok=True)
                if not os.path.exists(video_path):
                    # Create a simple test video if it doesn't exist
                    logger.info("Test video not found, please provide a valid path to a video file")
                    sys.exit(1)
            
            result = await test_video_identification(video_path)
            if "query_id" in result:
                query_id = result["query_id"]
                # Test query history with the result
                await test_query_history(query_id)
        
        if choice == "2" or choice == "5":
            # Test frame identification
            frame_path = input("Enter path to test frame file (or leave empty for default): ")
            if not frame_path:
                frame_path = os.path.join(project_root, "tests", "data", "sample_frame.jpg")
                # Create test directory if it doesn't exist
                os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                if not os.path.exists(frame_path):
                    # Create a simple test frame if it doesn't exist
                    logger.info("Test frame not found, please provide a valid path to a frame file")
                    sys.exit(1)
            
            result = await test_frame_identification(frame_path)
            if "query_id" in result:
                query_id = result["query_id"]
                # Test query history with the result
                await test_query_history(query_id)
        
        if choice == "3" or choice == "5":
            # Test audio identification
            audio_path = input("Enter path to test audio file (or leave empty for default): ")
            if not audio_path:
                audio_path = os.path.join(project_root, "tests", "data", "sample_audio.mp3")
                # Create test directory if it doesn't exist
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                if not os.path.exists(audio_path):
                    # Create a simple test audio if it doesn't exist
                    logger.info("Test audio not found, please provide a valid path to an audio file")
                    sys.exit(1)
            
            result = await test_audio_identification(audio_path)
            if "query_id" in result:
                query_id = result["query_id"]
                # Test query history with the result
                await test_query_history(query_id)
        
        if choice == "4":
            # Test query history
            query_id = input("Enter query ID: ")
            await test_query_history(query_id)
        
        if choice == "0":
            logger.info("Exiting...")
            sys.exit(0)
            
    finally:
        # Cleanup
        if server_process and server_process is not True:
            logger.info("Stopping API server...")
            server_process.terminate()


if __name__ == "__main__":
    asyncio.run(main())
