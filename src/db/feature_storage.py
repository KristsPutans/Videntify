"""Feature Storage Manager

This module provides a centralized way to store and retrieve feature vectors
extracted from videos, managing both file-based storage and vector database storage.
"""

import os
import json
import uuid
import logging
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from src.config.config import ConfigManager
from src.db.vector_db import get_vector_db_client, VectorDBClient
from src.utils.storage import ObjectStorage, create_storage

# Set up logging
logger = logging.getLogger(__name__)


class FeatureStorageManager:
    """Manager for storing and retrieving feature vectors."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the feature storage manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_all()
        
        # Initialize storage clients
        storage_config = self.config.get('storage', {})
        self.storage_client = create_storage(storage_config)
        self.vector_db_client = get_vector_db_client(config_path)
        
        # Define feature dimensions for different feature types
        self.feature_dimensions = {
            'perceptual_hash': 64,     # 64-bit perceptual hash
            'cnn_features': 2048,      # ResNet-50 features
            'scene_transition': 128,   # Scene transition features
            'motion_pattern': 256,     # Motion pattern features
            'audio_spectrogram': 512,  # Audio spectrogram features
            'audio_transcript': 768    # Text embedding dimension
        }
        
        # Initialize vector database collections if not already created
        self._init_vector_db()
        
    def _init_vector_db(self) -> bool:
        """Initialize vector database collections.
        
        Returns:
            True if successful, False otherwise
        """
        if self.vector_db_client is None:
            logger.error("Vector database client is not initialized")
            return False
            
        # Connect to vector database
        if not self.vector_db_client.connect():
            logger.error("Failed to connect to vector database")
            return False
            
        # Create collections for different feature types if they don't exist
        success = True
        for feature_type, dimension in self.feature_dimensions.items():
            collection_name = f"vidid_{feature_type}"
            if not self.vector_db_client.create_collection(collection_name, dimension):
                logger.error(f"Failed to create collection {collection_name}")
                success = False
                
        return success
        
    def store_feature_vector(self, feature_type: str, feature_vector: Union[np.ndarray, List[float]],
                           video_id: str, segment_id: Optional[str] = None,
                           timestamp: Optional[float] = None) -> Optional[str]:
        """Store a feature vector for a video or segment.
        
        Args:
            feature_type: Type of feature (perceptual_hash, cnn_features, etc.)
            feature_vector: The feature vector to store
            video_id: ID of the video
            segment_id: Optional ID of the video segment
            timestamp: Optional timestamp for the feature
            
        Returns:
            ID of the stored feature vector, or None if storage failed
        """
        try:
            # Generate a unique ID for this feature vector
            feature_id = str(uuid.uuid4())
            
            # Store feature vector in file system
            file_path = self._store_feature_file(feature_id, feature_type, feature_vector, video_id, segment_id)
            if not file_path:
                return None
                
            # Store feature vector in vector database
            if not self._store_feature_in_vector_db(feature_id, feature_type, feature_vector, video_id, segment_id):
                logger.warning(f"Failed to store feature vector {feature_id} in vector database")
                # Continue anyway as we have the file storage as backup
            
            return feature_id
        except Exception as e:
            logger.error(f"Error storing feature vector: {e}")
            return None
            
    def _store_feature_file(self, feature_id: str, feature_type: str, feature_vector: Union[np.ndarray, List[float]],
                          video_id: str, segment_id: Optional[str]) -> Optional[str]:
        """Store feature vector in a file.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of feature
            feature_vector: The feature vector
            video_id: ID of the video
            segment_id: Optional ID of the segment
            
        Returns:
            Path to the stored file, or None if storage failed
        """
        try:
            # Create directory structure: features/{video_id}/{feature_type}
            base_path = f"features/{video_id}/{feature_type}"
            if segment_id:
                base_path += f"/segments/{segment_id}"
                
            # Convert feature vector to numpy array if it's a list
            if isinstance(feature_vector, list):
                feature_vector = np.array(feature_vector, dtype=np.float32)
                
            # Serialize feature vector based on type
            if feature_type == 'perceptual_hash':
                # Store perceptual hash as a binary file
                file_extension = 'bin'
                # Convert to bytes, regardless of input type
                if isinstance(feature_vector, np.ndarray):
                    content = feature_vector.tobytes()
                elif isinstance(feature_vector, bytes):
                    content = feature_vector
                else:
                    # Convert to string then bytes if it's another type
                    content = '\n'.join(map(str, feature_vector)).encode('utf-8')
            else:
                # Store other features as numpy binary
                file_extension = 'npy'
                content = feature_vector.tobytes()
                
            # Define the file path
            file_path = f"{base_path}/{feature_id}.{file_extension}"
            
            # Create a temporary file to use with the storage client
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Store the file using storage client
            if not self.storage_client.upload_file(temp_file_path, file_path):
                logger.error(f"Failed to store feature file {file_path}")
                os.unlink(temp_file_path)  # Clean up temp file
                return None
                
            # Clean up temporary file
            os.unlink(temp_file_path)
                
            return file_path
        except Exception as e:
            logger.error(f"Error storing feature file: {e}")
            return None
            
    def _store_feature_in_vector_db(self, feature_id: str, feature_type: str, feature_vector: Union[np.ndarray, List[float]],
                                  video_id: str, segment_id: Optional[str]) -> bool:
        """Store feature vector in the vector database.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of feature
            feature_vector: The feature vector
            video_id: ID of the video
            segment_id: Optional ID of the segment
            
        Returns:
            True if successful, False otherwise
        """
        if self.vector_db_client is None:
            logger.error("Vector database client is not initialized")
            return False
            
        try:
            # Ensure feature vector is a list
            if isinstance(feature_vector, np.ndarray):
                feature_vector = feature_vector.tolist()
                
            # Prepare metadata
            metadata = {
                'video_id': video_id,
                'feature_type': feature_type
            }
            if segment_id:
                metadata['segment_id'] = segment_id
                
            # Get the collection name based on feature type
            collection_name = f"vidid_{feature_type}"
            
            # Insert the vector into the vector database
            success = self.vector_db_client.insert_vectors(
                collection_name=collection_name,
                vectors=[feature_vector],
                ids=[feature_id],
                metadata=[metadata]
            )
            
            return success
        except Exception as e:
            logger.error(f"Error storing feature in vector database: {e}")
            return False
            
    def retrieve_feature_vector(self, feature_id: str, feature_type: str,
                              video_id: str, segment_id: Optional[str] = None) -> Optional[np.ndarray]:
        """Retrieve a feature vector by ID.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of the feature
            video_id: ID of the video
            segment_id: Optional ID of the segment
            
        Returns:
            The feature vector as a numpy array, or None if not found
        """
        try:
            # Construct file path
            base_path = f"features/{video_id}/{feature_type}"
            if segment_id:
                base_path += f"/segments/{segment_id}"
                
            # Determine file extension based on feature type
            file_extension = 'txt' if feature_type == 'perceptual_hash' else 'npy'
            file_path = f"{base_path}/{feature_id}.{file_extension}"
            
            # Create a temporary file to download to
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            temp_file_path = temp_file.name
            
            # Try to download the file - this will also check if it exists
            if not self.storage_client.download_file(file_path, temp_file_path):
                logger.error(f"Feature file {file_path} not found or couldn't be downloaded")
                os.unlink(temp_file_path)  # Clean up temp file
                return None
                
            # Read the content from the temp file
            with open(temp_file_path, 'rb') as f:
                content = f.read()
                
            # Clean up the temp file
            os.unlink(temp_file_path)
            
            if not content:
                logger.error(f"Failed to retrieve content from {file_path}")
                return None
                
            # Parse feature vector based on type
            if feature_type == 'perceptual_hash':
                # Parse perceptual hash from text
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                feature_vector = np.array(list(map(int, content.strip().split())), dtype=np.int8)
            else:
                # Parse numpy binary
                feature_vector = np.frombuffer(content, dtype=np.float32)
                
            return feature_vector
        except Exception as e:
            logger.error(f"Error retrieving feature vector: {e}")
            return None
            
    def search_similar_features(self, query_vector: Union[np.ndarray, List[float]],
                               feature_type: str, top_k: int = 10,
                               filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar feature vectors in the vector database.
        
        Args:
            query_vector: Query feature vector
            feature_type: Type of feature to search
            top_k: Number of top results to return
            filter_params: Optional filter parameters
            
        Returns:
            List of search results with IDs, distances, and metadata
        """
        if self.vector_db_client is None:
            logger.error("Vector database client is not initialized")
            return []
            
        try:
            # Ensure query vector is a list
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
                
            # Get the collection name based on feature type
            collection_name = f"vidid_{feature_type}"
            
            # Search the vector database
            results = self.vector_db_client.search_vectors(
                collection_name=collection_name,
                query_vectors=[query_vector],
                top_k=top_k,
                metadata_filter=filter_params
            )
            
            # Return the first set of results (for the single query vector)
            return results[0] if results else []
        except Exception as e:
            logger.error(f"Error searching for similar features: {e}")
            return []
            
    def batch_search_similar_features(self, query_vectors: List[Union[np.ndarray, List[float]]],
                                    feature_type: str, top_k: int = 10,
                                    filter_params: Optional[Dict[str, Any]] = None) -> List[List[Dict[str, Any]]]:
        """Batch search for similar feature vectors in the vector database.
        
        Args:
            query_vectors: List of query feature vectors
            feature_type: Type of feature to search
            top_k: Number of top results to return
            filter_params: Optional filter parameters
            
        Returns:
            List of search results for each query vector
        """
        if self.vector_db_client is None:
            logger.error("Vector database client is not initialized")
            return []
            
        try:
            # Ensure query vectors are lists
            query_vectors_list = [
                v.tolist() if isinstance(v, np.ndarray) else v
                for v in query_vectors
            ]
            
            # Get the collection name based on feature type
            collection_name = f"vidid_{feature_type}"
            
            # Search the vector database
            results = self.vector_db_client.search_vectors(
                collection_name=collection_name,
                query_vectors=query_vectors_list,
                top_k=top_k,
                metadata_filter=filter_params
            )
            
            return results
        except Exception as e:
            logger.error(f"Error batch searching for similar features: {e}")
            return []
            
    def delete_feature_vector(self, feature_id: str, feature_type: str,
                            video_id: str, segment_id: Optional[str] = None) -> bool:
        """Delete a feature vector.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of feature
            video_id: ID of the video
            segment_id: Optional ID of the segment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from file storage
            file_deleted = self._delete_feature_file(feature_id, feature_type, video_id, segment_id)
            
            # Delete from vector database
            vector_deleted = self._delete_feature_from_vector_db(feature_id, feature_type)
            
            return file_deleted or vector_deleted
        except Exception as e:
            logger.error(f"Error deleting feature vector: {e}")
            return False
            
    def _delete_feature_file(self, feature_id: str, feature_type: str,
                           video_id: str, segment_id: Optional[str] = None) -> bool:
        """Delete a feature vector file.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of feature
            video_id: ID of the video
            segment_id: Optional ID of the segment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct file path
            base_path = f"features/{video_id}/{feature_type}"
            if segment_id:
                base_path += f"/segments/{segment_id}"
                
            # Determine file extension based on feature type
            file_extension = 'txt' if feature_type == 'perceptual_hash' else 'npy'
            file_path = f"{base_path}/{feature_id}.{file_extension}"
            
            # Delete the file - delete_file handles the existence check internally
            return self.storage_client.delete_file(file_path)
        except Exception as e:
            logger.error(f"Error deleting feature file: {e}")
            return False
            
    def _delete_feature_from_vector_db(self, feature_id: str, feature_type: str) -> bool:
        """Delete a feature vector from the vector database.
        
        Args:
            feature_id: ID of the feature vector
            feature_type: Type of feature
            
        Returns:
            True if successful, False otherwise
        """
        # Note: This is a placeholder as the vector_db module needs to be expanded
        # to support deletion of individual vectors. Many vector DBs don't support
        # efficient single vector deletion, so this might require a batch approach.
        logger.warning("Deletion of individual vectors from vector DB not yet implemented")
        return False
        
    def delete_all_features_for_video(self, video_id: str) -> bool:
        """Delete all features for a specific video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from file storage
            base_path = f"features/{video_id}"
            
            # Note: ObjectStorage may not support recursive deletion directly
            # This will just try to delete the directory as a single path
            # A more robust implementation would need to list and delete each file
            return self.storage_client.delete_file(base_path)
                
            # Delete from vector database (would require filtering by video_id)
            # This is currently a limitation as we would need to search and delete
            logger.warning("Deletion of all vectors for a video from vector DB not yet implemented")
            
            return False
        except Exception as e:
            logger.error(f"Error deleting all features for video {video_id}: {e}")
            return False
            
    def close(self) -> None:
        """Close connections to storage and vector database."""
        if self.vector_db_client is not None:
            self.vector_db_client.close()
