#!/usr/bin/env python3
"""
Direct Milvus Client for Videntify

This client directly connects to the Milvus server without compatibility issues.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Union
import numpy as np
from .vector_db import VectorDBClient

# Check if PyMilvus is available
try:
    import pymilvus
    HAS_PYMILVUS = True
except ImportError:
    HAS_PYMILVUS = False

class MilvusDirectClient(VectorDBClient):
    """Direct client for Milvus vector database."""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 19530,
                 user: str = "",
                 password: str = "",
                 timeout: int = 10,
                 **kwargs):
        """Initialize the Milvus client.
        
        Args:
            host: Host of the Milvus server.
            port: Port of the Milvus server.
            user: Username for authentication.
            password: Password for authentication.
            timeout: Timeout for operations in seconds.
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.connected = False
        self.collection_params = {}
        
        # Check if Milvus is available
        if not HAS_PYMILVUS:
            print("PyMilvus not installed. Using mock implementation.")
    
    def connect(self, **kwargs) -> bool:
        """Connect to Milvus.
        
        Args:
            **kwargs: Additional connection parameters.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        if not HAS_PYMILVUS:
            print("PyMilvus not installed. Using mock implementation.")
            return False
            
        try:
            # Override connection parameters if provided
            host = kwargs.get('host', self.host)
            port = kwargs.get('port', self.port)
            user = kwargs.get('user', self.user)
            password = kwargs.get('password', self.password)
            
            # Connect to Milvus
            pymilvus.connections.connect(
                alias="default",
                host=host,
                port=port,
                user=user if user else None,
                password=password if password else None
            )
            
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to Milvus server: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Milvus.
        
        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        if not HAS_PYMILVUS or not self.connected:
            return True
            
        try:
            pymilvus.connections.disconnect("default")
            self.connected = False
            return True
        except Exception as e:
            print(f"Error disconnecting from Milvus: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Milvus.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if not HAS_PYMILVUS:
            return False
            
        try:
            return pymilvus.connections.has_connection("default")
        except Exception:
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in Milvus.
        
        Returns:
            List[str]: List of collection names.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return []
            
        try:
            return pymilvus.utility.list_collections()
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def create_collection(self, collection_name: str, dimension: int, **kwargs) -> bool:
        """Create a new collection in Milvus.
        
        Args:
            collection_name: Name of the collection to create.
            dimension: Dimension of vectors to store.
            **kwargs: Additional collection parameters.
        
        Returns:
            bool: True if creation successful, False otherwise.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return False
            
        try:
            # Store collection parameters for later use
            self.collection_params[collection_name] = {
                'dimension': dimension,
                'index_params': kwargs.get('index_params', {
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 1024}
                }),
                'search_params': kwargs.get('search_params', {
                    "metric_type": "L2",
                    "params": {"nprobe": 16}
                })
            }
            
            # Define fields for the collection
            fields = [
                pymilvus.FieldSchema(name="id", dtype=pymilvus.DataType.INT64, is_primary=True, auto_id=True),
                pymilvus.FieldSchema(name="vector", dtype=pymilvus.DataType.FLOAT_VECTOR, dim=dimension)
            ]
            
            # Add metadata field if specified
            if kwargs.get('with_metadata', True):
                fields.append(pymilvus.FieldSchema(name="metadata", dtype=pymilvus.DataType.VARCHAR, max_length=65535))
            
            # Create schema and collection
            schema = pymilvus.CollectionSchema(fields=fields, description=f"Collection for {collection_name}")
            collection = pymilvus.Collection(name=collection_name, schema=schema)
            
            # Create an index on the vector field if specified
            if kwargs.get('create_index', True):
                collection.create_index("vector", self.collection_params[collection_name]['index_params'])
                # Load collection into memory for search
                collection.load()
            
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from Milvus.
        
        Args:
            collection_name: Name of the collection to drop.
        
        Returns:
            bool: True if drop successful, False otherwise.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return False
            
        try:
            pymilvus.utility.drop_collection(collection_name)
            if collection_name in self.collection_params:
                del self.collection_params[collection_name]
            return True
        except Exception as e:
            print(f"Error dropping collection: {e}")
            return False
    
    def insert(self, collection_name: str, vectors: List[List[float]], metadata: Optional[List[Dict]] = None) -> List[int]:
        """Insert vectors into a collection.
        
        Args:
            collection_name: Name of the collection to insert into.
            vectors: List of vectors to insert.
            metadata: Optional list of metadata dictionaries, one per vector.
        
        Returns:
            List[int]: List of IDs of inserted vectors.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return []
            
        try:
            # Get the collection
            collection = pymilvus.Collection(name=collection_name)
            
            # Prepare data for insertion
            insert_data = {"vector": vectors}
            
            # Add metadata if provided
            if metadata and len(metadata) == len(vectors):
                # Convert metadata to strings
                string_metadata = []
                for m in metadata:
                    if isinstance(m, dict):
                        string_metadata.append(json.dumps(m))
                    else:
                        string_metadata.append(str(m))
                insert_data["metadata"] = string_metadata
            
            # Insert data
            result = collection.insert(insert_data)
            
            return result.primary_keys
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            return []
    
    def search(self, collection_name: str, query_vectors: List[List[float]], top_k: int = 10, **kwargs) -> List[List[Dict]]:
        """Search for similar vectors in a collection.
        
        Args:
            collection_name: Name of the collection to search in.
            query_vectors: List of query vectors.
            top_k: Number of results to return per query.
            **kwargs: Additional search parameters.
        
        Returns:
            List[List[Dict]]: List of lists of search results.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return []
            
        try:
            # Get the collection
            collection = pymilvus.Collection(name=collection_name)
            
            # Make sure collection is loaded
            if not collection.is_loaded:
                collection.load()
            
            # Get search parameters
            search_params = kwargs.get('search_params', None)
            if search_params is None and collection_name in self.collection_params:
                search_params = self.collection_params[collection_name].get('search_params', {
                    "metric_type": "L2",
                    "params": {"nprobe": 16}
                })
            
            # Output fields
            output_fields = []
            if "metadata" in collection.schema.fields:
                output_fields.append("metadata")
            
            # Search for similar vectors
            result = collection.search(
                data=query_vectors,
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=output_fields
            )
            
            # Format search results
            formatted_results = []
            for hits in result:
                hit_results = []
                for hit in hits:
                    hit_data = {
                        "id": hit.id,
                        "distance": hit.distance,
                        "score": float(1.0 / (1.0 + hit.distance))  # Convert distance to similarity score
                    }
                    
                    # Add metadata if available
                    if hasattr(hit, 'entity') and 'metadata' in hit.entity:
                        try:
                            hit_data["metadata"] = json.loads(hit.entity.get('metadata', '{}'))
                        except:
                            hit_data["metadata"] = hit.entity.get('metadata', '{}')
                    
                    hit_results.append(hit_data)
                formatted_results.append(hit_results)
            
            return formatted_results
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection to get statistics for.
        
        Returns:
            Dict[str, Any]: Collection statistics.
        """
        if not HAS_PYMILVUS or not self.is_connected():
            return {"num_entities": 0, "stats": {}}
            
        try:
            # Get the collection
            collection = pymilvus.Collection(name=collection_name)
            
            # Get statistics
            stats = collection.get_stats()
            num_entities = collection.num_entities
            
            return {
                "num_entities": num_entities,
                "stats": stats
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"num_entities": 0, "stats": {}}
