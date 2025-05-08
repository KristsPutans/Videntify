"""Base classes for vector database clients.

This module contains the basic interfaces and common functionality
for all vector database clients to avoid circular imports.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)


class VectorDBType(str, Enum):
    """Enum for supported vector database types."""
    MILVUS = "milvus"
    MILVUS_DIRECT = "milvus_direct"
    PINECONE = "pinecone"
    FAISS_LOCAL = "faiss_local"
    MOCK = "mock"


class VectorDBClient:
    """Base class for vector database clients."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the vector database client.
        
        Args:
            config: Vector database configuration
        """
        self.config = config
        self.client = None
        
    def connect(self) -> bool:
        """Connect to the vector database.
        
        Returns:
            True if connection successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def is_connected(self) -> bool:
        """Check if the client is connected to the vector database.
        
        Returns:
            True if connected, False otherwise
        """
        return self.client is not None
        
    def create_collection(self, collection_name: str, dimension: int, 
                         metric_type: str = "L2") -> bool:
        """Create a new collection in the vector database.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of feature vectors
            metric_type: Distance metric type
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def insert(self, collection_name: str, vectors: List[List[float]], 
                metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Insert vectors into the collection.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vectors to insert
            metadata: Metadata for each vector
            
        Returns:
            List of IDs for inserted vectors
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def search(self, collection_name: str, query_vectors: List[List[float]], 
                top_k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[List[Dict]]:
        """Search for similar vectors in the collection.
        
        Args:
            collection_name: Name of the collection
            query_vectors: List of query vectors
            top_k: Number of results to return
            filter: Filter to apply to search
            
        Returns:
            List of results, each with ID, distance, and metadata
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def list_collections(self) -> List[str]:
        """List all collections in the vector database.
        
        Returns:
            List of collection names
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from the vector database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary of collection statistics
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def close(self) -> None:
        """Close the connection to the vector database."""
        self.client = None
