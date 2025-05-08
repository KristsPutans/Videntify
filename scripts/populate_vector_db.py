#!/usr/bin/env python3
"""
Vector Database Population Script

This script populates the vector database with existing feature vectors
from the file system for testing and validation purposes.
"""

import os
import sys
import glob
import time
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path to allow importing modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
from src.core.feature_extraction import FeatureType
from src.core.vector_db_integration import VectorDBIntegration
from src.db.feature_storage import FeatureStorageManager


def scan_feature_files(features_dir: str) -> Dict[str, Dict[str, List[str]]]:
    """Scan the features directory for feature files.
    
    Args:
        features_dir: Path to features directory
        
    Returns:
        Dictionary mapping video IDs to feature types and file paths
    """
    logger.info(f"Scanning features directory: {features_dir}")
    
    # Structure: video_id -> feature_type -> [file_paths]
    result = {}
    
    # Supported feature types and their file extensions
    feature_types = {
        'perceptual_hash': ['.bin', '.txt'],
        'cnn_features': ['.npy'],
        'motion_pattern': ['.npy'],
        'audio_spectrogram': ['.npy']
    }
    
    # Walk through features directory
    for root, dirs, files in os.walk(features_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, features_dir)
            
            # Extract parts from path
            parts = rel_path.split(os.sep)
            if len(parts) >= 2:
                video_id = parts[0]
                feature_type = parts[1]
                
                # Skip if not a recognized feature type
                if feature_type not in feature_types:
                    continue
                    
                # Extract file extension
                _, ext = os.path.splitext(file)
                if ext not in feature_types[feature_type]:
                    continue
                
                # Add to result
                if video_id not in result:
                    result[video_id] = {}
                if feature_type not in result[video_id]:
                    result[video_id][feature_type] = []
                
                result[video_id][feature_type].append(file_path)
    
    # Log summary
    total_videos = len(result)
    total_features = sum(len(files) for video in result.values() for files in video.values())
    
    logger.info(f"Found {total_videos} videos with {total_features} feature files")
    return result


def load_feature_vector(file_path: str, feature_type: str) -> Optional[np.ndarray]:
    """Load a feature vector from a file.
    
    Args:
        file_path: Path to the feature file
        feature_type: Type of feature
        
    Returns:
        Feature vector as numpy array or None if loading fails
    """
    try:
        if feature_type == 'perceptual_hash':
            # Load perceptual hash from txt or bin file
            ext = os.path.splitext(file_path)[1]
            if ext == '.txt':
                with open(file_path, 'r') as f:
                    # Parse text representation of hash
                    content = f.read().strip()
                    # Handle different text formats
                    if '\n' in content:
                        # One bit per line
                        vector = np.array([int(bit) for bit in content.split('\n')], dtype=np.float32)
                    else:
                        # Space or comma-separated
                        vector = np.array([int(bit) for bit in content.split()], dtype=np.float32)
                return vector
            elif ext == '.bin':
                # Load binary hash
                with open(file_path, 'rb') as f:
                    content = f.read()
                    # Convert bytes to numpy array
                    vector = np.frombuffer(content, dtype=np.uint8).astype(np.float32)
                return vector
        else:
            # Load numpy array
            return np.load(file_path)
    except Exception as e:
        logger.error(f"Error loading feature vector from {file_path}: {e}")
        return None


def populate_vector_db(vector_db: VectorDBIntegration, features_data: Dict[str, Dict[str, List[str]]],
                      batch_size: int = 100, max_items: Optional[int] = None):
    """Populate the vector database with feature vectors.
    
    Args:
        vector_db: Vector database integration instance
        features_data: Feature data from scan_feature_files
        batch_size: Number of vectors to insert in a batch
        max_items: Maximum number of items to process (for testing)
    """
    logger.info("Beginning vector database population...")
    
    # Map feature types to enum values
    feature_type_map = {
        'perceptual_hash': FeatureType.PERCEPTUAL_HASH,
        'cnn_features': FeatureType.CNN_FEATURES,
        'motion_pattern': FeatureType.MOTION_PATTERN,
        'audio_spectrogram': FeatureType.AUDIO_SPECTROGRAM
    }
    
    # Track statistics
    stats = {
        'total_videos': 0,
        'total_features': 0,
        'successful_features': 0,
        'failed_features': 0
    }
    
    # Process each video
    for video_id, feature_types in features_data.items():
        stats['total_videos'] += 1
        
        # Check if we've reached the maximum number of items
        if max_items is not None and stats['total_videos'] > max_items:
            logger.info(f"Reached maximum number of items ({max_items}), stopping")
            break
        
        logger.info(f"Processing video {video_id} ({stats['total_videos']}/{len(features_data)})")
        
        # Process each feature type
        for feature_type, file_paths in feature_types.items():
            if feature_type not in feature_type_map:
                continue
                
            enum_type = feature_type_map[feature_type]
            
            # Process each feature file
            for file_path in file_paths:
                stats['total_features'] += 1
                
                # Load feature vector
                feature_vector = load_feature_vector(file_path, feature_type)
                if feature_vector is None:
                    stats['failed_features'] += 1
                    continue
                
                # Store in vector database
                try:
                    # Extract feature ID from filename
                    feature_id = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # Store in vector database
                    feature_id = vector_db.store_video_feature(
                        video_id=video_id,
                        feature_type=enum_type,
                        feature_vector=feature_vector,
                        metadata={
                            'source_file': file_path,
                            'feature_dimension': feature_vector.shape[0]
                        }
                    )
                    
                    if feature_id:
                        stats['successful_features'] += 1
                        if stats['successful_features'] % 100 == 0:
                            logger.info(f"Stored {stats['successful_features']} features so far")
                    else:
                        stats['failed_features'] += 1
                        
                except Exception as e:
                    logger.error(f"Error storing feature in vector database: {e}")
                    stats['failed_features'] += 1
    
    # Log final statistics
    logger.info(f"Vector database population complete!")
    logger.info(f"Processed {stats['total_videos']} videos with {stats['total_features']} feature files")
    logger.info(f"Successfully stored {stats['successful_features']} features")
    logger.info(f"Failed to store {stats['failed_features']} features")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Vector Database Population Script")
    parser.add_argument("--features-dir", default="/tmp/vidid/features",
                      help="Path to features directory")
    parser.add_argument("--batch-size", type=int, default=100,
                      help="Number of vectors to insert in a batch")
    parser.add_argument("--max-items", type=int, default=None,
                      help="Maximum number of items to process (for testing)")
    parser.add_argument("--config-path", default=None,
                      help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Initialize vector database integration
    vector_db = VectorDBIntegration(args.config_path)
    
    # Scan features directory
    features_data = scan_feature_files(args.features_dir)
    
    # Populate vector database
    populate_vector_db(vector_db, features_data, args.batch_size, args.max_items)


if __name__ == "__main__":
    main()
