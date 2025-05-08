"""Vector Database Integration for Identification API

This module provides utility functions to integrate the identification API
with vector database operations.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np

from src.core.feature_extraction import FeatureType
from src.core.vector_db_integration import VectorDBIntegration
from src.feature_extraction import FeatureVector

logger = logging.getLogger(__name__)


def store_video_features_in_vector_db(
    vector_db: VectorDBIntegration,
    query_id: str,
    features: Dict[str, FeatureVector],
    save_query: bool = True,
    query_type: str = "video"
) -> bool:
    """Store extracted video features in the vector database.
    
    Args:
        vector_db: Vector database integration instance
        query_id: ID of the query (used as video_id for storage)
        features: Dictionary of extracted features
        save_query: Whether to save the query
        query_type: Type of query ('video', 'frame', or 'audio')
        
    Returns:
        True if features were stored, False otherwise
    """
    if not vector_db or not save_query:
        return False
        
    vector_features_stored = False
    
    # Process and store each feature type
    for feature_name, feature_vector in features.items():
        feat_type = None
        
        if "visual_cnn" in feature_name:
            feat_type = FeatureType.CNN_FEATURES
        elif "visual_phash" in feature_name:
            feat_type = FeatureType.PERCEPTUAL_HASH
        elif "visual_motion" in feature_name:
            feat_type = FeatureType.MOTION_PATTERN
        elif "audio_fingerprint" in feature_name:
            feat_type = FeatureType.AUDIO_SPECTROGRAM
        else:
            # Skip unknown feature types
            continue
            
        try:
            # Store feature in vector database
            feature_id = vector_db.store_video_feature(
                video_id=query_id,
                feature_type=feat_type,
                feature_vector=feature_vector.vector,
                metadata={"is_query": True, "query_type": query_type}
            )
            
            if feature_id:
                vector_features_stored = True
                logger.debug(f"Stored {feature_name} in vector database with ID {feature_id}")
                
        except Exception as e:
            logger.error(f"Error storing {feature_name} in vector database: {e}")
    
    return vector_features_stored


def prepare_matching_features(
    features: Dict[str, FeatureVector]
) -> Dict[str, Union[List[float], np.ndarray]]:
    """Prepare features for matching by converting to the format expected by the matching engine.
    
    Args:
        features: Dictionary of extracted features
        
    Returns:
        Dictionary of features in the format expected by the matching engine
    """
    matching_features = {}
    
    for feature_name, feature_vector in features.items():
        if "visual_cnn" in feature_name:
            matching_features[FeatureType.CNN_FEATURES.value] = feature_vector.vector
        elif "visual_phash" in feature_name:
            matching_features[FeatureType.PERCEPTUAL_HASH.value] = feature_vector.vector
        elif "visual_motion" in feature_name:
            matching_features[FeatureType.MOTION_PATTERN.value] = feature_vector.vector
        elif "audio_fingerprint" in feature_name:
            matching_features[FeatureType.AUDIO_SPECTROGRAM.value] = feature_vector.vector
    
    return matching_features
