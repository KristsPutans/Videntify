"""Tests for the matching engine."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.matching_engine import (
    MatchingEngine,
    MatchingAlgorithm,
    MatchResult
)
from src.core.feature_extraction import FeatureType


@pytest.fixture
def matching_engine():
    """Create a matching engine for testing."""
    config = {"match_threshold": 0.85, "default_top_k": 5}
    vector_db_client = MagicMock()
    metadata_db_client = MagicMock()
    return MatchingEngine(config, vector_db_client, metadata_db_client)


def test_hamming_distance(matching_engine):
    """Test the Hamming distance calculation."""
    hash1 = "0101010101010101"
    hash2 = "0101010101010111"  # Different in last 2 bits
    
    # Calculate distance
    distance = matching_engine.hamming_distance(hash1, hash2)
    
    # The difference is 2 bits out of 16, so distance should be 0.125
    assert distance == 2/16
    
    # Test with identical hashes
    assert matching_engine.hamming_distance(hash1, hash1) == 0.0
    
    # Test with completely different hashes
    assert matching_engine.hamming_distance("0000", "1111") == 1.0


def test_cosine_similarity(matching_engine):
    """Test the cosine similarity calculation."""
    vec1 = np.array([1, 0, 1, 0])
    vec2 = np.array([0, 1, 0, 1])
    
    # These vectors are orthogonal, so similarity should be 0
    assert matching_engine.cosine_similarity(vec1, vec2) == 0.0
    
    # Test with identical vectors
    assert matching_engine.cosine_similarity(vec1, vec1) == 1.0
    
    # Test with similar vectors
    vec3 = np.array([1, 0.1, 0.9, 0])
    assert 0.95 < matching_engine.cosine_similarity(vec1, vec3) < 1.0


@pytest.mark.asyncio
async def test_match_hash_sequence(matching_engine):
    """Test matching a sequence of perceptual hashes."""
    # Create a sample hash sequence
    query_hashes = ["0101010101010101", "1010101010101010"]
    
    # Get matches
    results = await matching_engine.match_hash_sequence(query_hashes, top_k=2)
    
    # Verify the results
    assert len(results) == 2
    assert "content_id" in results[0]
    assert "confidence" in results[0]
    assert "match_type" in results[0]
    assert results[0]["match_type"] == "hash"


@pytest.mark.asyncio
async def test_match_video_segment(matching_engine):
    """Test matching a video segment."""
    # Create sample features
    segment_features = {
        FeatureType.PERCEPTUAL_HASH: ["0101010101010101", "1010101010101010"],
        FeatureType.CNN_FEATURES: np.ones(2048, dtype=np.float32)
    }
    
    # Mock the hash and CNN matching methods
    matching_engine.match_hash_sequence = MagicMock(return_value=[
        {"content_id": "vid123", "title": "Sample Video 1", "confidence": 0.95, "match_type": "hash"}
    ])
    matching_engine.match_cnn_features = MagicMock(return_value=[
        {"content_id": "vid456", "title": "Sample Video 2", "confidence": 0.87, "match_type": "cnn"}
    ])
    
    # Get matches
    results = await matching_engine.match_video_segment(
        segment_features, 
        [MatchingAlgorithm.ENSEMBLE],
        top_k=2
    )
    
    # Verify the results
    assert len(results) == 2
    assert all(isinstance(result, MatchResult) for result in results)
    assert results[0].confidence > results[1].confidence
