"""Vector Database Integration

This module provides integration with vector databases (Milvus, Pinecone)
for storing and retrieving feature vectors extracted from videos.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

from src.config.config import ConfigManager
from .vector_db_base import VectorDBClient, VectorDBType

# Set up logging
logger = logging.getLogger(__name__)

# Import specific database clients
try:
    from .milvus_adapter import MilvusAdapter
except ImportError:
    logger.warning("MilvusAdapter not available")
    MilvusAdapter = None
    
try:
    from .milvus_direct_client import MilvusDirectClient
except ImportError:
    logger.warning("MilvusDirectClient not available")
    MilvusDirectClient = None

try:
    from .faiss_vector_db import FaissClient
except ImportError:
    logger.warning("FaissClient not available")
    FaissClient = None


class MockVectorDBClient(VectorDBClient):
    """Mock vector database client for development and testing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the mock vector database client.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.collections = {}  # collection_name -> {dimension, vectors, metadata}
        self.connected = True
        logger.info("MockVectorDBClient initialized")
        
    def connect(self) -> bool:
        """Connect to the mock database (always succeeds).
        
        Returns:
            True (always successful)
        """
        self.connected = True
        return True
        
    def is_connected(self) -> bool:
        """Check if connected to the mock database.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
        
    def create_collection(self, collection_name: str, dimension: int, 
                         metric_type: str = "L2") -> bool:
        """Create a new collection in the mock database.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of the vectors
            metric_type: Metric type for similarity search
            
        Returns:
            True if successful, False otherwise
        """
        if collection_name in self.collections:
            logger.warning(f"Collection {collection_name} already exists")
            return False
            
        self.collections[collection_name] = {
            'dimension': dimension,
            'metric_type': metric_type,
            'vectors': [],
            'metadata': [],
            'ids': []
        }
        logger.info(f"Created collection {collection_name} with dimension {dimension}")
        return True
        
    def list_collections(self) -> List[str]:
        """List all collections in the mock database.
        
        Returns:
            List of collection names
        """
        return list(self.collections.keys())
        
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from the mock database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful, False otherwise
        """
        if collection_name not in self.collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return False
            
        del self.collections[collection_name]
        logger.info(f"Dropped collection {collection_name}")
        return True
        
    def insert(self, collection_name: str, vectors: List[List[float]], 
               metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Insert vectors into the mock database.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vectors to insert
            metadata: Optional metadata for each vector
            
        Returns:
            List of IDs for the inserted vectors
        """
        if collection_name not in self.collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return []
            
        collection = self.collections[collection_name]
        
        # Check dimensions
        for vector in vectors:
            if len(vector) != collection['dimension']:
                logger.error(f"Vector dimension {len(vector)} doesn't match collection dimension {collection['dimension']}")
                return []
        
        # Generate IDs (simple incrementing integers as strings)
        start_id = len(collection['ids'])
        ids = [str(start_id + i) for i in range(len(vectors))]
        
        # Add vectors and metadata
        collection['vectors'].extend(vectors)
        collection['ids'].extend(ids)
        
        # Handle metadata
        if metadata:
            if len(metadata) != len(vectors):
                logger.warning(f"Metadata count ({len(metadata)}) doesn't match vector count ({len(vectors)}), ignoring metadata")
                collection['metadata'].extend([{} for _ in range(len(vectors))])
            else:
                collection['metadata'].extend(metadata)
        else:
            collection['metadata'].extend([{} for _ in range(len(vectors))])
            
        logger.info(f"Inserted {len(vectors)} vectors into collection {collection_name}")
        return ids
        
    def search(self, collection_name: str, query_vectors: List[List[float]], 
               top_k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[List[Dict]]:
        """Search for similar vectors in the mock database.
        
        Args:
            collection_name: Name of the collection
            query_vectors: List of query vectors
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of results, each with ID, distance, and metadata
        """
        if collection_name not in self.collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return []
            
        collection = self.collections[collection_name]
        
        if not collection['vectors']:
            logger.warning(f"Collection {collection_name} is empty")
            return [[] for _ in range(len(query_vectors))]
            
        results = []
        for query in query_vectors:
            if len(query) != collection['dimension']:
                logger.error(f"Query dimension {len(query)} doesn't match collection dimension {collection['dimension']}")
                results.append([])
                continue
                
            # Calculate distances (using L2 distance)
            distances = []
            for i, vector in enumerate(collection['vectors']):
                # Apply filter if provided
                if filter and not self._match_filter(collection['metadata'][i], filter):
                    continue
                    
                # Calculate L2 distance
                dist = sum((a - b) ** 2 for a, b in zip(query, vector)) ** 0.5
                distances.append((i, dist))
                
            # Sort by distance and take top_k
            distances.sort(key=lambda x: x[1])
            top_results = distances[:top_k]
            
            # Format results
            query_results = []
            for idx, dist in top_results:
                query_results.append({
                    'id': collection['ids'][idx],
                    'distance': dist,
                    'score': 1.0 / (1.0 + dist),  # Convert distance to similarity score
                    'metadata': collection['metadata'][idx]
                })
                
            results.append(query_results)
            
        return results
        
    def _match_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter.
        
        Args:
            metadata: Metadata to check
            filter: Filter to apply
            
        Returns:
            True if metadata matches filter, False otherwise
        """
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
        
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary of collection statistics
        """
        if collection_name not in self.collections:
            logger.warning(f"Collection {collection_name} does not exist")
            return {}
            
        collection = self.collections[collection_name]
        return {
            'dimension': collection['dimension'],
            'metric_type': collection['metric_type'],
            'count': len(collection['vectors'])
        }
        
    def close(self) -> None:
        """Close the connection to the mock database."""
        self.connected = False
        logger.info("MockVectorDBClient connection closed")


def get_mock_client(config: Dict[str, Any]) -> VectorDBClient:
    """Get a mock vector database client.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Mock vector database client
    """
    return MockVectorDBClient(config)


def get_vector_db_client(config_path: str = None) -> VectorDBClient:
    """Get a vector database client based on configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Vector database client instance
    """
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        vector_db_config = config_manager.get('vector_db', {})
        logger.info("Configuration loaded successfully")
        
        # Get vector database type
        vector_db_type = vector_db_config.get('type', 'mock').lower()
        
        # Client mapping for direct access
        client_mapping = {
            'milvus': MilvusAdapter,
            'milvus_direct': MilvusDirectClient,
            'faiss_local': FaissClient,
            'mock': MockVectorDBClient
        }
        
        # Try to use the specified client
        if vector_db_type in client_mapping and client_mapping[vector_db_type] is not None:
            try:
                client_class = client_mapping[vector_db_type]
                client = client_class(vector_db_config)
                
                # Test connection if the client has a connect method
                if hasattr(client, 'connect') and callable(client.connect):
                    if client.connect():
                        logger.info(f"Connected to {vector_db_type} successfully")
                        return client
                    else:
                        logger.warning(f"Could not connect to {vector_db_type}, falling back to mock implementation")
                else:
                    # Client doesn't require explicit connection
                    logger.info(f"Using {vector_db_type} client")
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize {vector_db_type}: {e}")
                logger.warning("Falling back to mock vector database for development")
        else:
            logger.warning(f"Vector database type '{vector_db_type}' not supported or client not available")
            available_clients = [k for k, v in client_mapping.items() if v is not None]
            logger.warning(f"Available types: {available_clients}")
        
        # If we get here, fall back to mock client
        return get_mock_client(vector_db_config)
        
    except Exception as e:
        logger.error(f"Error initializing vector database client: {e}")
        logger.warning("Falling back to mock vector database for development")
        return get_mock_client({})
