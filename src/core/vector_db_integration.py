"""Vector Database Integration

This module provides integration between the core VidID components
and the vector database for efficient similarity searches.
"""

import logging
import numpy as np
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple

from src.db.feature_storage import FeatureStorageManager
from src.db.models import Video, VideoSegment, VideoFeature, SegmentFeature, FeatureTypeEnum
from src.db.vector_db import get_vector_db_client

# Set up logging
logger = logging.getLogger(__name__)


class VectorDBIntegration:
    """Integration class between core components and vector database."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the vector database integration.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.feature_storage = FeatureStorageManager(config_path)
        self.vector_db_client = get_vector_db_client(config_path)
        
        # Connect to vector database
        if self.vector_db_client:
            self.vector_db_client.connect()
        
    def store_video_feature(self, video_id: str, feature_type: FeatureTypeEnum, 
                          feature_vector: Union[np.ndarray, List[float]], 
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Store a video-level feature vector in the vector database.
        
        Args:
            video_id: ID of the video
            feature_type: Type of feature (perceptual_hash, cnn_features, etc.)
            feature_vector: The feature vector to store
            metadata: Optional additional metadata
            
        Returns:
            ID of the stored feature vector, or None if storage failed
        """
        try:
            # Convert enum to string if needed
            feature_type_str = feature_type.value if hasattr(feature_type, 'value') else str(feature_type)
            
            # Store feature vector
            feature_id = self.feature_storage.store_feature_vector(
                feature_type=feature_type_str,
                feature_vector=feature_vector,
                video_id=video_id
            )
            
            return feature_id
        except Exception as e:
            logger.error(f"Error storing video feature: {e}")
            return None
    
    def store_segment_feature(self, video_id: str, segment_id: str,
                            feature_type: FeatureTypeEnum, 
                            feature_vector: Union[np.ndarray, List[float]],
                            timestamp: Optional[float] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Store a segment-level feature vector in the vector database.
        
        Args:
            video_id: ID of the video
            segment_id: ID of the segment
            feature_type: Type of feature (perceptual_hash, cnn_features, etc.)
            feature_vector: The feature vector to store
            timestamp: Optional timestamp for the feature
            metadata: Optional additional metadata
            
        Returns:
            ID of the stored feature vector, or None if storage failed
        """
        try:
            # Convert enum to string if needed
            feature_type_str = feature_type.value if hasattr(feature_type, 'value') else str(feature_type)
            
            # Store feature vector
            feature_id = self.feature_storage.store_feature_vector(
                feature_type=feature_type_str,
                feature_vector=feature_vector,
                video_id=video_id,
                segment_id=segment_id,
                timestamp=timestamp
            )
            
            return feature_id
        except Exception as e:
            logger.error(f"Error storing segment feature: {e}")
            return None
            
    def search_similar_videos(self, query_vector: Union[np.ndarray, List[float]],
                             feature_type: FeatureTypeEnum, top_k: int = 10,
                             metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for videos with similar features.
        
        Args:
            query_vector: Query feature vector
            feature_type: Type of feature to search
            top_k: Number of top results to return
            metadata_filter: Optional filter parameters
            
        Returns:
            List of search results with video IDs, distances, and metadata
        """
        try:
            # Convert enum to string if needed
            feature_type_str = feature_type.value if hasattr(feature_type, 'value') else str(feature_type)
            
            # Search for similar features
            results = self.feature_storage.search_similar_features(
                query_vector=query_vector,
                feature_type=feature_type_str,
                top_k=top_k,
                filter_params=metadata_filter
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching similar videos: {e}")
            return []
            
    def search_similar_segments(self, query_vector: Union[np.ndarray, List[float]],
                              feature_type: FeatureTypeEnum, top_k: int = 10,
                              metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for video segments with similar features.
        
        Args:
            query_vector: Query feature vector
            feature_type: Type of feature to search
            top_k: Number of top results to return
            metadata_filter: Optional filter parameters
            
        Returns:
            List of search results with segment IDs, video IDs, distances, and metadata
        """
        try:
            # Convert enum to string if needed
            feature_type_str = feature_type.value if hasattr(feature_type, 'value') else str(feature_type)
            
            # Add segment_id filter to ensure we only get segments
            filter_params = metadata_filter.copy() if metadata_filter else {}
            filter_params['segment_id'] = {'$exists': True}
            
            # Search for similar features
            results = self.feature_storage.search_similar_features(
                query_vector=query_vector,
                feature_type=feature_type_str,
                top_k=top_k,
                filter_params=filter_params
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching similar segments: {e}")
            return []
            
    def batch_search_similar_features(self, query_vectors: List[Union[np.ndarray, List[float]]],
                                    feature_type: FeatureTypeEnum, top_k: int = 10,
                                    metadata_filter: Optional[Dict[str, Any]] = None) -> List[List[Dict[str, Any]]]:
        """Batch search for similar feature vectors.
        
        Args:
            query_vectors: List of query feature vectors
            feature_type: Type of feature to search
            top_k: Number of top results to return
            metadata_filter: Optional filter parameters
            
        Returns:
            List of search results for each query vector
        """
        try:
            # Convert enum to string if needed
            feature_type_str = feature_type.value if hasattr(feature_type, 'value') else str(feature_type)
            
            # Batch search for similar features
            results = self.feature_storage.batch_search_similar_features(
                query_vectors=query_vectors,
                feature_type=feature_type_str,
                top_k=top_k,
                filter_params=metadata_filter
            )
            
            return results
        except Exception as e:
            logger.error(f"Error batch searching similar features: {e}")
            return []
    
    def delete_video_features(self, video_id: str) -> bool:
        """Delete all features for a specific video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.feature_storage.delete_all_features_for_video(video_id)
        except Exception as e:
            logger.error(f"Error deleting video features: {e}")
            return False
            
    def close(self) -> None:
        """Close connections to databases."""
        if self.feature_storage:
            self.feature_storage.close()
