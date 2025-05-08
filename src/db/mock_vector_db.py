"""Mock Vector Database Implementation

This module provides a mock implementation of a vector database for testing
and development purposes, avoiding the need for a real vector database.
"""

import os
import json
import time
import pickle
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from src.db.vector_db import VectorDBClient

# Set up logging
logger = logging.getLogger(__name__)


class MockVectorDBClient(VectorDBClient):
    """Mock vector database client for testing and development.
    
    This implementation stores vectors in memory with optional persistence to disk,
    and provides basic similarity search operations without requiring a real database.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the mock vector database client.
        
        Args:
            config: Vector database configuration
        """
        super().__init__(config)
        self.collections = {}
        self.connected = False
        self.dimensions = config.get('dimensions', {
            'cnn_features': 2048,
            'perceptual_hash': 64,
            'motion_pattern': 256,
            'audio_spectrogram': 512
        })
        self.simulate_latency = config.get('simulate_latency_ms', 0) / 1000
        
        # Storage path for persistence
        self.storage_path = config.get('storage_path', '/tmp/vidid/mock_vector_db')
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing collections if available
        self.load_collections()
    
    def connect(self) -> bool:
        """Connect to the mock vector database.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
            
        self.connected = True
        logger.info("Connected to mock vector database")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the mock vector database.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
            
        self.connected = False
        return True
    
    def load_collections(self) -> bool:
        """Load collections from disk if available.
        
        Returns:
            True if collections loaded, False otherwise
        """
        try:
            collections_file = os.path.join(self.storage_path, 'collections.pkl')
            if os.path.exists(collections_file):
                with open(collections_file, 'rb') as f:
                    self.collections = pickle.load(f)
                logger.info(f"Loaded {len(self.collections)} collections from disk")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading collections: {e}")
            return False
    
    def save_collections(self) -> bool:
        """Save collections to disk.
        
        Returns:
            True if collections saved, False otherwise
        """
        try:
            collections_file = os.path.join(self.storage_path, 'collections.pkl')
            with open(collections_file, 'wb') as f:
                pickle.dump(self.collections, f)
            logger.info(f"Saved {len(self.collections)} collections to disk")
            return True
        except Exception as e:
            logger.error(f"Error saving collections: {e}")
            return False
    
    def create_collection(self, collection_name: str, dimension: int, **kwargs) -> bool:
        """Create a collection in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of vectors in the collection
            
        Returns:
            True if creation successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return False
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        if collection_name in self.collections:
            logger.warning(f"Collection {collection_name} already exists")
            return True
        
        self.collections[collection_name] = {
            'dimension': dimension,
            'vectors': [],
            'ids': [],
            'metadata': []
        }
        
        logger.info(f"Created collection {collection_name} with dimension {dimension}")
        self.save_collections()
        return True
    
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from the mock vector database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return False
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        if collection_name not in self.collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return False
        
        del self.collections[collection_name]
        logger.info(f"Dropped collection {collection_name}")
        self.save_collections()
        return True
    
    def list_collections(self) -> List[str]:
        """List all collections in the mock vector database.
        
        Returns:
            List of collection names
        """
        if not self.connected:
            self.connect()
        
        return list(self.collections.keys())
    
    def get_collection_stats(self, collection_name: str) -> int:
        """Get statistics for a collection in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of vectors in the collection
        """
        if not self.connected:
            self.connect()
        
        if collection_name not in self.collections:
            return 0
        
        return len(self.collections[collection_name]['vectors'])
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if collection exists, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return False
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        return collection_name in self.collections
    
    def insert_vectors(self, collection_name: str, vectors: Union[List[List[float]], np.ndarray], 
                      ids: Optional[List[str]] = None, metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Insert vectors into a collection in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vectors to insert
            ids: Optional list of IDs for the vectors
            metadata: Optional list of metadata for the vectors
            
        Returns:
            List of IDs for the inserted vectors
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return []
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} does not exist")
            return []
        
        collection = self.collections[collection_name]
        
        # Convert vectors to numpy arrays
        if isinstance(vectors, list):
            vectors = np.array(vectors, dtype=np.float32)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        # Generate empty metadata if not provided
        if metadata is None:
            metadata = [{} for _ in range(len(vectors))]
        
        # Check dimensions match
        if vectors.shape[1] != collection['dimension']:
            logger.error(f"Vector dimension {vectors.shape[1]} does not match collection dimension {collection['dimension']}")
            return []
        
        # Add vectors to collection
        for i, (vector, id, meta) in enumerate(zip(vectors, ids, metadata)):
            collection['vectors'].append(vector)
            collection['ids'].append(id)
            collection['metadata'].append(meta)
        
        logger.info(f"Inserted {len(vectors)} vectors into collection {collection_name}")
        self.save_collections()
        return ids
    
    def search_vectors(self, collection_name: str, query_vectors: Union[List[List[float]], np.ndarray], 
                      top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            query_vectors: Query vectors to search for
            top_k: Number of results to return
            
        Returns:
            List of dictionaries with search results
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return []
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} does not exist")
            return []
        
        collection = self.collections[collection_name]
        
        # Convert query vectors to numpy arrays
        if isinstance(query_vectors, list):
            query_vectors = np.array(query_vectors, dtype=np.float32)
        
        # If only one query vector, reshape to 2D
        if len(query_vectors.shape) == 1:
            query_vectors = query_vectors.reshape(1, -1)
        
        # Check dimensions match
        if query_vectors.shape[1] != collection['dimension']:
            logger.error(f"Query vector dimension {query_vectors.shape[1]} does not match collection dimension {collection['dimension']}")
            return []
        
        # If collection is empty, return empty results
        if len(collection['vectors']) == 0:
            return [{"query_id": i, "results": []} for i in range(len(query_vectors))]
        
        # Calculate distances for each query vector
        results = []
        for i, query_vector in enumerate(query_vectors):
            # Convert collection vectors to numpy array
            collection_vectors = np.array(collection['vectors'])
            
            # Calculate cosine distances
            similarities = np.dot(collection_vectors, query_vector) / (
                np.linalg.norm(collection_vectors, axis=1) * np.linalg.norm(query_vector)
            )
            
            # Get top-k indices
            if len(similarities) <= top_k:
                top_indices = np.argsort(similarities)[::-1]
            else:
                top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Create results
            query_results = []
            for idx in top_indices:
                query_results.append({
                    "id": collection['ids'][idx],
                    "score": float(similarities[idx]),  # Convert to float for serialization
                    "metadata": collection['metadata'][idx]
                })
            
            results.append({
                "query_id": i,
                "results": query_results
            })
        
        return results
    
    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """Delete vectors from a collection in the mock vector database.
        
        Args:
            collection_name: Name of the collection
            ids: List of IDs to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to mock vector database")
            return False
            
        if self.simulate_latency > 0:
            time.sleep(self.simulate_latency)
        
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} does not exist")
            return False
        
        collection = self.collections[collection_name]
        
        # Find indices to delete
        indices_to_delete = []
        for i, id in enumerate(collection['ids']):
            if id in ids:
                indices_to_delete.append(i)
        
        # Delete in reverse order to avoid index shifting
        for i in sorted(indices_to_delete, reverse=True):
            del collection['vectors'][i]
            del collection['ids'][i]
            del collection['metadata'][i]
        
        logger.info(f"Deleted {len(indices_to_delete)} vectors from collection {collection_name}")
        self.save_collections()
        return True
