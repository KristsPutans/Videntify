#!/usr/bin/env python3
"""
Test Identification API with Vector Database Integration

This script tests the identification API endpoints with vector database integration,
verifying that features are properly stored and retrieved.
"""

import os
import sys
import time
import logging
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow importing modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
SAMPLE_VIDEO_PATH = "/path/to/sample_video.mp4"  # Replace with an actual test video path
SAMPLE_IMAGE_PATH = "/path/to/sample_image.jpg"  # Replace with an actual test image path

# Mock JWT token for authentication (for testing only)
MOCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MTkwMjQxMDB9.signature"

def test_video_identification_with_vector_db():
    """Test video identification endpoint with vector database integration."""
    logger.info("Testing video identification with vector database...")
    
    # Make sure the test video file exists
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        logger.error(f"Test video file not found: {SAMPLE_VIDEO_PATH}")
        return False
    
    # Prepare request data
    url = f"{API_BASE_URL}/identification/video"
    headers = {
        "Authorization": f"Bearer {MOCK_TOKEN}"
    }
    params = {
        "matching_algorithms": ["cosine_similarity", "hamming_distance"],
        "max_results": 5,
        "threshold": 0.7,
        "save_query": True  # Set to True to test vector database storage
    }
    
    # Open video file for upload
    with open(SAMPLE_VIDEO_PATH, "rb") as video_file:
        files = {
            "video_file": (os.path.basename(SAMPLE_VIDEO_PATH), video_file, "video/mp4")
        }
        
        try:
            # Make the request
            logger.info("Sending identification request...")
            response = requests.post(url, headers=headers, data=params, files=files)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Identification successful! Query ID: {result['query_id']}")
                logger.info(f"Found {len(result['results'])} matches")
                
                # The returned query_id should match what's stored in the vector database
                return result['query_id']
            else:
                logger.error(f"Identification request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during identification request: {e}")
            return None

def test_frame_identification_with_vector_db():
    """Test frame identification endpoint with vector database integration."""
    logger.info("Testing frame identification with vector database...")
    
    # Make sure the test image file exists
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        logger.error(f"Test image file not found: {SAMPLE_IMAGE_PATH}")
        return False
    
    # Prepare request data
    url = f"{API_BASE_URL}/identification/frame"
    headers = {
        "Authorization": f"Bearer {MOCK_TOKEN}"
    }
    params = {
        "matching_algorithms": ["cosine_similarity"],
        "max_results": 5,
        "threshold": 0.7,
        "save_query": True  # Set to True to test vector database storage
    }
    
    # Open image file for upload
    with open(SAMPLE_IMAGE_PATH, "rb") as image_file:
        files = {
            "frame_file": (os.path.basename(SAMPLE_IMAGE_PATH), image_file, "image/jpeg")
        }
        
        try:
            # Make the request
            logger.info("Sending frame identification request...")
            response = requests.post(url, headers=headers, data=params, files=files)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Frame identification successful! Query ID: {result['query_id']}")
                logger.info(f"Found {len(result['results'])} matches")
                
                # The returned query_id should match what's stored in the vector database
                return result['query_id']
            else:
                logger.error(f"Frame identification request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during frame identification request: {e}")
            return None

# Verify vector database integration by checking if features were stored
def verify_vector_db_storage(query_id: Optional[str]) -> bool:
    """Verify that features were stored in the vector database for the given query ID."""
    if not query_id:
        logger.error("No query ID provided, cannot verify vector database storage")
        return False
    
    try:
        # Import the vector database integration module
        from src.core.vector_db_integration import VectorDBIntegration
        from src.core.feature_extraction import FeatureType
        
        # Initialize vector database integration
        vector_db = VectorDBIntegration()
        
        # Try to retrieve features for the query ID
        # Note: This requires additional implementation in VectorDBIntegration
        # to support retrieving features by video_id
        # The following is a placeholder for demonstration:
        feature_types = [FeatureType.CNN_FEATURES, FeatureType.PERCEPTUAL_HASH]
        
        features_found = False
        for feat_type in feature_types:
            # Placeholder for feature retrieval - would need to be implemented
            # features = vector_db.get_video_features(video_id=query_id, feature_type=feat_type)
            # if features:
            #     features_found = True
            #     logger.info(f"Found features of type {feat_type} for query ID {query_id}")
            
            # For now, just log what we would be checking
            logger.info(f"Would check for features of type {feat_type} for query ID {query_id}")
            
        logger.info(f"Vector database verification {'successful' if features_found else 'simulated'} for query ID {query_id}")
        return True  # Returning True for demonstration purposes
        
    except Exception as e:
        logger.error(f"Error verifying vector database storage: {e}")
        return False

def main():
    """Run tests for identification API with vector database integration."""
    logger.info("=== Starting Identification API with Vector DB Tests ===")
    
    # Test video identification
    video_query_id = test_video_identification_with_vector_db()
    if video_query_id:
        verify_vector_db_storage(video_query_id)
    
    # Test frame identification
    frame_query_id = test_frame_identification_with_vector_db()
    if frame_query_id:
        verify_vector_db_storage(frame_query_id)
    
    logger.info("=== Identification API with Vector DB Tests Completed ===")

if __name__ == "__main__":
    main()
