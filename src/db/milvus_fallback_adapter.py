#!/usr/bin/env python3
"""
Milvus Fallback Adapter for Videntify

This adapter provides a resilient interface to Milvus with automatic fallback
to local vector operations when the Milvus service is unavailable.
"""

import json
import numpy as np
import requests
import os
import pickle
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from .vector_db_base import VectorDBClient


class MilvusFallbackAdapter(VectorDBClient):
    """Resilient adapter for Milvus with fallback to local operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Milvus fallback adapter.
        
        Args:
            config: Configuration dictionary with Milvus connection parameters.
                   Should contain 'connector_host' and 'connector_port' for the Docker-based Milvus connector.
                   Can also contain 'fallback_dir' for the directory to store fallback files.
        """
        super().__init__(config)
        
        # Milvus connector configuration
        self.connector_host = config.get('connector_host', 'localhost')
        self.connector_port = config.get('connector_port', 5050)
        self.timeout = config.get('timeout', 30)  # 30-second timeout
        self.base_url = f"http://{self.connector_host}:{self.connector_port}"
        self.connected = False
        
        # Milvus server parameters
        self.milvus_params = {
            'host': config.get('host', 'host.docker.internal'),
            'port': config.get('port', 19530),
            'user': config.get('user', ''),
            'password': config.get('password', ''),
            'db_name': config.get('db_name', 'default')
        }
        
        # Fallback configuration
        self.fallback_dir = config.get('fallback_dir', os.path.join(os.getcwd(), 'milvus_fallback'))
        self.fallback_mode = config.get('fallback_mode', 'auto')  # 'auto', 'always', 'never'
        self.max_retries = config.get('max_retries', 3)
        
        # Create fallback directory if it doesn't exist
        os.makedirs(self.fallback_dir, exist_ok=True)
        
        # Local collection storage
        self._collections = {}
        
        print(f"Initialized MilvusFallbackAdapter with connector at {self.base_url}")
        print(f"Fallback mode: {self.fallback_mode}, Fallback dir: {self.fallback_dir}")
        
        # Try initial connection if auto or never fallback
        if self.fallback_mode != 'always':
            self.connect()
        else:
            print("Running in forced fallback mode - not connecting to Milvus")
    
    def connect(self) -> bool:
        """Connect to Milvus via the connector.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.fallback_mode == 'always':
            print("Skipping connection due to forced fallback mode")
            return False
        
        for attempt in range(self.max_retries):
            try:
                print(f"Connecting to Milvus connector at {self.base_url} (attempt {attempt+1}/{self.max_retries})")
                
                # First check if the connector is running
                try:
                    health_response = requests.get(
                        f"{self.base_url}/health",
                        timeout=self.timeout
                    )
                    if health_response.status_code != 200:
                        print(f"Milvus connector health check failed: {health_response.status_code}")
                        continue  # Try again
                    print("Milvus connector health check successful")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to connect to Milvus connector: {e}")
                    continue  # Try again
                
                # Now try to connect to Milvus server via the connector
                response = requests.post(
                    f"{self.base_url}/connect",
                    json=self.milvus_params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        self.connected = True
                        print("Successfully connected to Milvus")
                        return True
                    else:
                        print(f"Failed to connect to Milvus: {result.get('message', 'Unknown error')}")
                else:
                    print(f"Failed to connect to Milvus: HTTP {response.status_code}")
                
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                print(f"Error connecting to Milvus: {type(e).__name__}: {e}")
                time.sleep(1)  # Wait before retrying
        
        print(f"Failed to connect after {self.max_retries} attempts, operating in fallback mode")
        return False
    
    def disconnect(self) -> bool:
        """Disconnect from Milvus.
        
        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        if not self.connected:
            return True
        
        try:
            response = requests.post(
                f"{self.base_url}/disconnect",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.connected = False
                print("Successfully disconnected from Milvus")
                return True
            else:
                print(f"Failed to disconnect from Milvus: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Error disconnecting from Milvus: {type(e).__name__}: {e}")
            self.connected = False  # Assume disconnected
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Milvus.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if self.fallback_mode == 'always':
            return False
        
        if not self.connected:
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            self.connected = False
            return False
    
    def _get_collection_path(self, collection_name: str) -> str:
        """Get the path to the local collection file.
        
        Args:
            collection_name: Name of the collection.
            
        Returns:
            str: Path to the local collection file.
        """
        return os.path.join(self.fallback_dir, f"{collection_name}.pkl")
    
    def _save_local_collection(self, collection_name: str) -> bool:
        """Save a local collection to disk.
        
        Args:
            collection_name: Name of the collection to save.
            
        Returns:
            bool: True if save successful, False otherwise.
        """
        try:
            if collection_name not in self._collections:
                return False
            
            with open(self._get_collection_path(collection_name), 'wb') as f:
                pickle.dump(self._collections[collection_name], f)
            return True
        except Exception as e:
            print(f"Error saving local collection {collection_name}: {e}")
            return False
    
    def _load_local_collection(self, collection_name: str) -> bool:
        """Load a local collection from disk.
        
        Args:
            collection_name: Name of the collection to load.
            
        Returns:
            bool: True if load successful, False otherwise.
        """
        try:
            path = self._get_collection_path(collection_name)
            if not os.path.exists(path):
                return False
            
            with open(path, 'rb') as f:
                self._collections[collection_name] = pickle.load(f)
            return True
        except Exception as e:
            print(f"Error loading local collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in Milvus or fallback storage.
        
        Returns:
            List[str]: List of collection names.
        """
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                response = requests.get(
                    f"{self.base_url}/list_collections",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("collections", [])
            except Exception as e:
                print(f"Error listing collections from Milvus: {e}")
        
        # Fallback: list local collections
        print("Using fallback for list_collections")
        collections = []
        
        # Include in-memory collections
        collections.extend(list(self._collections.keys()))
        
        # Include collections saved on disk
        for file in os.listdir(self.fallback_dir):
            if file.endswith(".pkl"):
                name = file[:-4]  # Remove .pkl extension
                if name not in collections:
                    collections.append(name)
        
        return collections
    
    def create_collection(self, collection_name: str, dimension: int, **kwargs) -> bool:
        """Create a new collection in Milvus or fallback storage.
        
        Args:
            collection_name: Name of the collection to create.
            dimension: Dimension of vectors to store.
            **kwargs: Additional collection parameters.
        
        Returns:
            bool: True if creation successful, False otherwise.
        """
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                with_metadata = kwargs.get('with_metadata', True)
                skip_loading = kwargs.get('skip_loading', True)
                load_timeout = kwargs.get('load_timeout', 5)
                
                params = {
                    "collection_name": collection_name,
                    "dimension": dimension,
                    "with_metadata": with_metadata,
                    "skip_loading": skip_loading,
                    "load_timeout": load_timeout
                }
                
                response = requests.post(
                    f"{self.base_url}/create_collection",
                    json=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        return True
            except Exception as e:
                print(f"Error creating collection in Milvus: {e}")
        
        # Fallback: create local collection
        print(f"Using fallback to create collection {collection_name}")
        try:
            # Initialize local collection structure
            self._collections[collection_name] = {
                'dimension': dimension,
                'vectors': [],  # List of vectors
                'ids': [],      # List of IDs
                'metadata': []  # List of metadata dicts
            }
            
            # Save to disk
            self._save_local_collection(collection_name)
            return True
        except Exception as e:
            print(f"Error creating fallback collection: {e}")
            return False
    
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from Milvus or fallback storage.
        
        Args:
            collection_name: Name of the collection to drop.
        
        Returns:
            bool: True if drop successful, False otherwise.
        """
        success = False
        
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                response = requests.post(
                    f"{self.base_url}/drop_collection",
                    json={"collection_name": collection_name},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        success = True
            except Exception as e:
                print(f"Error dropping collection from Milvus: {e}")
        
        # Also drop from local storage
        try:
            # Remove from memory
            if collection_name in self._collections:
                del self._collections[collection_name]
            
            # Remove file if it exists
            file_path = self._get_collection_path(collection_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Dropped local collection {collection_name}")
            
            return True
        except Exception as e:
            print(f"Error dropping fallback collection: {e}")
            return success  # Return Milvus result if available
    
    def insert(self, collection_name: str, vectors: List[List[float]], metadata: Optional[List[Dict]] = None) -> List[int]:
        """Insert vectors into a collection.
        
        Args:
            collection_name: Name of the collection to insert into.
            vectors: List of vectors to insert.
            metadata: Optional list of metadata dictionaries, one per vector.
        
        Returns:
            List[int]: List of IDs of inserted vectors.
        """
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                data = {
                    "collection_name": collection_name,
                    "vectors": vectors
                }
                
                if metadata:
                    data["metadata"] = metadata
                
                response = requests.post(
                    f"{self.base_url}/insert",
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        return result.get("ids", [])
            except Exception as e:
                print(f"Error inserting into Milvus: {e}")
        
        # Fallback: insert into local collection
        print(f"Using fallback to insert {len(vectors)} vectors into {collection_name}")
        try:
            # Load collection if not in memory
            if collection_name not in self._collections:
                if not self._load_local_collection(collection_name):
                    print(f"Collection {collection_name} does not exist for fallback insertion")
                    return []
            
            collection = self._collections[collection_name]
            start_id = len(collection['vectors'])
            ids = list(range(start_id, start_id + len(vectors)))
            
            # Add vectors
            collection['vectors'].extend(vectors)
            collection['ids'].extend(ids)
            
            # Add metadata if provided
            if metadata:
                if len(metadata) < len(vectors):
                    metadata = metadata + [{} for _ in range(len(vectors) - len(metadata))]
                collection['metadata'].extend(metadata)
            else:
                collection['metadata'].extend([{} for _ in range(len(vectors))])
            
            # Save to disk
            self._save_local_collection(collection_name)
            return ids
        except Exception as e:
            print(f"Error inserting into fallback collection: {e}")
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
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                data = {
                    "collection_name": collection_name,
                    "query_vectors": query_vectors,
                    "top_k": top_k
                }
                
                search_params = kwargs.get('search_params')
                if search_params:
                    data["search_params"] = search_params
                
                response = requests.post(
                    f"{self.base_url}/search",
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        return result.get("results", [])
            except Exception as e:
                print(f"Error searching in Milvus: {e}")
        
        # Fallback: search in local collection
        print(f"Using fallback to search in {collection_name}")
        try:
            # Load collection if not in memory
            if collection_name not in self._collections:
                if not self._load_local_collection(collection_name):
                    print(f"Collection {collection_name} does not exist for fallback search")
                    return [[] for _ in range(len(query_vectors))]
            
            collection = self._collections[collection_name]
            results = []
            
            for query in query_vectors:
                # Simple L2 distance calculation (can be optimized)
                distances = []
                for i, vector in enumerate(collection['vectors']):
                    # Compute distance between query and vector
                    distance = sum((a - b) ** 2 for a, b in zip(query, vector)) ** 0.5
                    distances.append((i, distance))
                
                # Sort by distance (ascending)
                distances.sort(key=lambda x: x[1])
                
                # Take top-k
                query_results = []
                for i, distance in distances[:top_k]:
                    result = {
                        "id": collection['ids'][i],
                        "distance": float(distance),
                        "score": float(1.0 / (1.0 + distance))  # Convert distance to score
                    }
                    
                    # Add metadata if available
                    if i < len(collection['metadata']):
                        result["metadata"] = collection['metadata'][i]
                    
                    query_results.append(result)
                
                results.append(query_results)
            
            return results
        except Exception as e:
            print(f"Error searching in fallback collection: {e}")
            return [[] for _ in range(len(query_vectors))]
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection to get statistics for.
        
        Returns:
            Dict[str, Any]: Collection statistics.
        """
        # Try Milvus first if connected
        if self.is_connected() and self.fallback_mode != 'always':
            try:
                response = requests.get(
                    f"{self.base_url}/collection_stats/{collection_name}",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        return result.get("stats", {})
            except Exception as e:
                print(f"Error getting collection stats from Milvus: {e}")
        
        # Fallback: get stats from local collection
        print(f"Using fallback to get stats for {collection_name}")
        try:
            # Load collection if not in memory
            if collection_name not in self._collections:
                if not self._load_local_collection(collection_name):
                    print(f"Collection {collection_name} does not exist for fallback stats")
                    return {}
            
            collection = self._collections[collection_name]
            stats = {
                "name": collection_name,
                "dimension": collection['dimension'],
                "vector_count": len(collection['vectors']),
                "fallback": True
            }
            return stats
        except Exception as e:
            print(f"Error getting fallback collection stats: {e}")
            return {}
