"""Tests for the feature extraction engine."""

import os
import tempfile
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.feature_extraction import (
    FeatureExtractionEngine, 
    FeatureType
)


@pytest.fixture
def feature_engine():
    """Create a feature extraction engine for testing."""
    config = {
        "gpu_enabled": False,
        "batch_size": 1,
        "model_path": "models/resnet50.pth",
        "scene_detection_threshold": 30.0
    }
    with patch('torch.nn.Sequential'):
        with patch('torchvision.models.resnet50'):
            return FeatureExtractionEngine(config)


@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing."""
    # Create a temporary video file
    fd, path = tempfile.mkstemp(suffix='.mp4')
    os.close(fd)
    
    # Create a short test video (black frames)
    width, height = 320, 240
    fps = 30
    duration = 1  # 1 second
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    
    for _ in range(fps * duration):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    
    yield path
    
    # Clean up the temporary file
    if os.path.exists(path):
        os.unlink(path)


def test_compute_perceptual_hash(feature_engine):
    """Test computing perceptual hash from a frame."""
    # Create a simple test frame
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    # Add some patterns to make it non-uniform
    frame[100:150, 100:150] = 255
    
    # Compute hash
    hash_str = feature_engine.compute_perceptual_hash(frame)
    
    # Verify the hash is a string of 0s and 1s with the expected length
    assert isinstance(hash_str, str)
    assert all(c in '01' for c in hash_str)
    assert len(hash_str) == 64  # 8x8 DCT coefficients


@patch('src.core.feature_extraction.FeatureExtractionEngine.extract_cnn_features')
def test_process_video_segment(mock_extract_cnn, feature_engine, sample_video_file):
    """Test processing a video segment."""
    # Mock CNN feature extraction to return a fixed vector
    mock_extract_cnn.return_value = np.ones(2048, dtype=np.float32)
    
    # Process a segment of the video
    features = feature_engine.process_video_segment(
        sample_video_file, 
        0.0, 
        0.5, 
        [FeatureType.PERCEPTUAL_HASH, FeatureType.CNN_FEATURES]
    )
    
    # Verify the features contain the expected types
    assert FeatureType.PERCEPTUAL_HASH in features
    assert FeatureType.CNN_FEATURES in features
    
    # Verify the hash list is non-empty
    assert len(features[FeatureType.PERCEPTUAL_HASH]) > 0
    
    # Verify the CNN features have the expected shape
    assert features[FeatureType.CNN_FEATURES].shape == (2048,)
