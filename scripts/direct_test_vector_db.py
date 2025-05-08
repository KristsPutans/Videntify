#!/usr/bin/env python3
"""
Direct Testing Script for Vector Database Integration

This script directly tests the vector database integration without requiring the full API server.
"""

import os
import sys
import json
import uuid
import logging
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import necessary modules
from src.core.vector_db_integration import VectorDBIntegration
from src.core.feature_extraction import FeatureType
from src.core.matching_engine import MatchingEngine, MatchingAlgorithm
from src.db.vector_db import get_vector_db_client

def test_vector_db_connection():
    """Test connecting to the vector database"""
    logger.info("Testing vector database connection...")
    try:
        vector_db = VectorDBIntegration()
        logger.info(f"Vector DB client type: {type(vector_db.vector_db_client).__name__}")
        logger.info("Vector DB connection successful!")
        return vector_db
    except Exception as e:
        logger.error(f"Error connecting to vector database: {e}")
        return None

def test_store_feature_vector(vector_db, feature_type=FeatureType.CNN_FEATURES):
    """Test storing a feature vector in the vector database"""
    logger.info(f"Testing storing a feature vector of type {feature_type.name}...")
    
    # Generate a random feature vector with dimensions based on type
    dims = {
        FeatureType.CNN_FEATURES: 2048,
        FeatureType.PERCEPTUAL_HASH: 64,
        FeatureType.MOTION_PATTERN: 256,
        FeatureType.AUDIO_SPECTROGRAM: 512
    }
    
    dimension = dims.get(feature_type, 2048)
    
    if feature_type == FeatureType.PERCEPTUAL_HASH:
        # Binary vector for perceptual hash
        feature_vector = np.random.randint(0, 2, size=dimension).astype(np.float32)
    else:
        # Random vector for other feature types
        feature_vector = np.random.rand(dimension).astype(np.float32)
    
    # Generate a random video ID
    video_id = f"test_video_{int(uuid.uuid4().hex[:8], 16)}"  
    
    try:
        # Store the feature vector
        feature_id = vector_db.store_video_feature(
            video_id=video_id,
            feature_type=feature_type,
            feature_vector=feature_vector,
            metadata={"test": True, "timestamp": "2025-05-08T11:32:00"}
        )
        
        if feature_id:
            logger.info(f"Successfully stored feature vector with ID {feature_id}")
            return True
        else:
            logger.error("Failed to store feature vector")
            return False
    except Exception as e:
        logger.error(f"Error storing feature vector: {e}")
        return False

def test_search_vectors(vector_db, feature_type=FeatureType.CNN_FEATURES):
    """Test searching for similar vectors"""
    logger.info(f"Testing vector similarity search for {feature_type.name}...")
    
    # Generate a random query vector
    dims = {
        FeatureType.CNN_FEATURES: 2048,
        FeatureType.PERCEPTUAL_HASH: 64,
        FeatureType.MOTION_PATTERN: 256,
        FeatureType.AUDIO_SPECTROGRAM: 512
    }
    
    dimension = dims.get(feature_type, 2048)
    
    if feature_type == FeatureType.PERCEPTUAL_HASH:
        # Binary vector for perceptual hash
        query_vector = np.random.randint(0, 2, size=dimension).astype(np.float32)
    else:
        # Random vector for other feature types
        query_vector = np.random.rand(dimension).astype(np.float32)
    
    try:
        # Search for similar vectors
        results = vector_db.vector_db_client.similarity_search(
            collection_name=f"vidid_{feature_type.value}",
            query_vector=query_vector,
            top_k=5
        )
        
        logger.info(f"Search results: {results}")
        logger.info(f"Found {len(results)} similar vectors")
        return True
    except Exception as e:
        logger.error(f"Error searching for similar vectors: {e}")
        return False

def test_matching_engine(vector_db):
    """Test the matching engine with the vector database"""
    logger.info("Testing matching engine with vector database...")
    
    try:
        # First store some test vectors
        for feature_type in [
            FeatureType.CNN_FEATURES,
            FeatureType.PERCEPTUAL_HASH,
            FeatureType.MOTION_PATTERN,
            FeatureType.AUDIO_SPECTROGRAM
        ]:
            test_store_feature_vector(vector_db, feature_type)
        
        # Create a matching engine instance
        config = {"match_threshold": 0.7}
        matching_engine = MatchingEngine(config)
        
        # Prepare a test scene with features
        test_features = {
            FeatureType.CNN_FEATURES.value: np.random.rand(2048).astype(np.float32),
            FeatureType.PERCEPTUAL_HASH.value: np.random.randint(0, 2, size=64).astype(np.float32)
        }
        
        # Prepare the video features structure
        video_features = {
            "scenes": [
                {
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "features": test_features
                }
            ]
        }
        
        # Define an async function for testing
        import asyncio
        
        async def run_match_test():
            results = await matching_engine.match_video(
                video_features,
                algorithms=[MatchingAlgorithm.COSINE_SIMILARITY],
                top_k=5
            )
            return results
        
        # Create and run the event loop
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(run_match_test())
        
        logger.info(f"Matching results: {results}")
        return True
    except Exception as e:
        logger.error(f"Error testing matching engine: {e}")
        return False

def test_vector_db_performance(vector_db):
    """Test vector database performance"""
    logger.info("Testing vector database performance...")
    
    try:
        # Test how quickly we can store and retrieve vectors
        import time
        
        # Store 10 vectors and measure time
        start_time = time.time()
        for _ in range(10):
            test_store_feature_vector(vector_db, FeatureType.CNN_FEATURES)
        end_time = time.time()
        
        store_time = end_time - start_time
        logger.info(f"Time to store 10 vectors: {store_time:.2f} seconds")
        
        # Search 10 times and measure time
        start_time = time.time()
        for _ in range(10):
            test_search_vectors(vector_db, FeatureType.CNN_FEATURES)
        end_time = time.time()
        
        search_time = end_time - start_time
        logger.info(f"Time to search 10 times: {search_time:.2f} seconds")
        
        return True
    except Exception as e:
        logger.error(f"Error testing vector database performance: {e}")
        return False

def run_all_tests():
    """Run all vector database tests"""
    logger.info("=== Starting Direct Vector Database Tests ===")
    
    # Test vector database connection
    vector_db = test_vector_db_connection()
    if not vector_db:
        logger.error("Vector database connection failed, cannot continue tests")
        return False
    
    # Run storage tests
    for feature_type in [
        FeatureType.CNN_FEATURES,
        FeatureType.PERCEPTUAL_HASH,
        FeatureType.MOTION_PATTERN,
        FeatureType.AUDIO_SPECTROGRAM
    ]:
        test_store_feature_vector(vector_db, feature_type)
    
    # Run search tests
    for feature_type in [
        FeatureType.CNN_FEATURES,
        FeatureType.PERCEPTUAL_HASH,
        FeatureType.MOTION_PATTERN,
        FeatureType.AUDIO_SPECTROGRAM
    ]:
        test_search_vectors(vector_db, feature_type)
    
    # Test matching engine
    test_matching_engine(vector_db)
    
    # Test performance
    test_vector_db_performance(vector_db)
    
    logger.info("=== Direct Vector Database Tests Completed ===")
    return True

if __name__ == "__main__":
    run_all_tests()
