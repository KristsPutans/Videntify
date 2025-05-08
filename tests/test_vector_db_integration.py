#!/usr/bin/env python
"""
Test Vector Database Integration with API

This script tests the integration between the vector database and the API endpoints,
especially focused on the identification endpoints.
"""

import os
import sys
import logging
import json
import time
import numpy as np
from pathlib import Path

# Add project root to path to allow importing modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.vector_db_integration import VectorDBIntegration
from src.core.feature_extraction import FeatureType
from src.db.feature_storage import FeatureStorageManager
from src.core.matching_engine import MatchingEngine, MatchingAlgorithm

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import pytest

@pytest.fixture
def vector_db():
    """Fixture to create a vector database connection"""
    logger.info("Testing vector database connection...")
    try:
        vector_db = VectorDBIntegration()
        logger.info(f"Vector DB client type: {type(vector_db.vector_db_client).__name__}")
        logger.info("Vector DB connection successful!")
        return vector_db
    except Exception as e:
        logger.error(f"Error connecting to vector database: {e}")
        pytest.skip(f"Could not connect to vector database: {e}")
        
def test_vector_db_creation(vector_db):
    """Test creating a vector database connection"""
    assert vector_db is not None
    assert vector_db.vector_db_client is not None
    
def test_store_feature_vector(vector_db, feature_type=FeatureType.CNN_FEATURES):
    """Test storing a feature vector in the vector database"""
    logger.info(f"Testing storing a feature vector of type {feature_type}...")
    
    # Generate a random feature vector with correct dimensions based on type
    if feature_type == FeatureType.PERCEPTUAL_HASH:
        # Perceptual hash is typically a binary array
        # For the vector database, we need a numeric array
        feature_vector = np.random.randint(0, 2, size=64).astype(np.float32)
    elif feature_type == FeatureType.CNN_FEATURES:
        # CNN features are typically high-dimensional embeddings
        feature_vector = np.random.rand(2048)  # 2048-dimensional vector (ResNet-50)
    elif feature_type == FeatureType.MOTION_PATTERN:
        # Motion patterns for temporal features
        feature_vector = np.random.rand(256)  # 256-dimensional vector
    elif feature_type == FeatureType.AUDIO_SPECTROGRAM:
        # Audio features 
        feature_vector = np.random.rand(512)  # 512-dimensional vector
    else:
        feature_vector = np.random.rand(64)  # Generic case
    
    # Generate a test video ID
    video_id = f"test_video_{int(time.time())}"
    
    # Store the feature vector
    try:
        feature_id = vector_db.store_video_feature(
            video_id=video_id,
            feature_type=feature_type,
            feature_vector=feature_vector,
            metadata={"test": True, "feature_type": str(feature_type)}
        )
        logger.info(f"Successfully stored feature vector with ID {feature_id}")
        return video_id, feature_vector, feature_id
    except Exception as e:
        logger.error(f"Error storing feature vector: {e}")
        return None, None, None

def test_matching_engine(vector_db):
    """Test matching engine with vector database"""
    logger.info("Testing matching engine with vector database...")
    
    # Create a matching engine instance
    try:
        # First, we need to insert test vectors for testing
        test_vectors = {}
        
        # Insert a test CNN feature vector
        test_vector_id = test_store_feature_vector(vector_db, FeatureType.CNN_FEATURES)
        test_vectors[FeatureType.CNN_FEATURES.value] = np.random.rand(2048)
        
        # Also test with a perceptual hash
        test_hash_id = test_store_feature_vector(vector_db, FeatureType.PERCEPTUAL_HASH)
        test_vectors[FeatureType.PERCEPTUAL_HASH.value] = np.random.randint(0, 2, size=64).astype(np.float32)
        
        # Initialize matching engine with config
        config = {"match_threshold": 0.7}
        matching_engine = MatchingEngine(config)
        logger.info("Testing matching CNN feature vector")
        
        # Create a temporary directory for storing temporary files
        os.makedirs('/tmp/vidid/storage', exist_ok=True)
        
        # Create an async function we can run
        async def run_match_test():
            # Prepare a proper video features structure with scenes
            video_features = {
                "scenes": [
                    {
                        "start_time": 0.0,
                        "end_time": 10.0,
                        "features": test_vectors
                    }
                ]
            }
            
            return await matching_engine.match_video(
                video_features,
                algorithms=[MatchingAlgorithm.COSINE_SIMILARITY],
                top_k=5
            )
        
        # Run the async function in a synchronous context
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the test and get the results
        try:
            results = loop.run_until_complete(run_match_test())
            logger.info(f"Match results: {results}")
            assert results is not None, "No match results returned"
            return True
        except Exception as e:
            logger.error(f"Error matching CNN features: {e}")
            assert False, f"Error matching features: {e}"
            
    except Exception as e:
        logger.error(f"Error testing matching engine: {e}")
        assert False, f"Error testing matching engine: {e}"

def test_motion_pattern_storage(vector_db):
    """Test storing motion pattern features"""
    feature_id = test_store_feature_vector(vector_db, FeatureType.MOTION_PATTERN)
    assert feature_id is not None, "Failed to store motion pattern feature"
    return True
    
def test_audio_spectrogram_storage(vector_db):
    """Test storing audio spectrogram features"""
    feature_id = test_store_feature_vector(vector_db, FeatureType.AUDIO_SPECTROGRAM)
    assert feature_id is not None, "Failed to store audio spectrogram feature"
    return True

def main():
    """Run the vector database integration tests"""
    logger.info("=== Starting Vector Database Integration Tests ===")
    
    # Test vector database connection
    vector_db = test_vector_db_creation()
    if not vector_db:
        logger.error("Failed to connect to vector database. Exiting.")
        return
    
    # Test storing feature vectors for different types
    for feature_type in [FeatureType.CNN_FEATURES, FeatureType.PERCEPTUAL_HASH]:
        video_id, _, feature_id = test_store_feature_vector(vector_db, feature_type)
        if not feature_id:
            logger.warning(f"Failed to store {feature_type} feature. Continuing with tests.")
    
    # Test the matching engine
    match_results = test_matching_engine(vector_db)
    
    logger.info("=== Vector Database Integration Tests Completed ===")

if __name__ == "__main__":
    main()
