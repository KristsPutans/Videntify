#!/usr/bin/env python3
"""
Milvus Adapter for Videntify

This adapter interfaces with the Docker-based Milvus connector to provide
seamless vector database functionality without version compatibility issues.
"""

import json
import requests
from typing import List, Dict, Any, Optional, Union
from .vector_db_base import VectorDBClient

class MilvusAdapter(VectorDBClient):
    """Adapter for the Docker-based Milvus connector."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Milvus adapter.
        
        Args:
            config: Configuration dictionary with Milvus connection parameters.
                   Should contain 'host' and 'port' for the Docker-based Milvus connector.
        """
        super().__init__(config)
        
        # Extract connection parameters from config
        self.connector_host = config.get('connector_host', 'localhost')
        self.connector_port = config.get('connector_port', 5050)
        self.timeout = config.get('timeout', 30)  # Increased default timeout from 10 to 30 seconds
        
        # Build base URL for the connector
        self.base_url = f"http://{self.connector_host}:{self.connector_port}"
        self.connected = False
        print(f"Initialized MilvusAdapter with connector at {self.base_url} and timeout {self.timeout}s")
        
        # Store Milvus server parameters for connection
        self.milvus_params = {
            # Use host.docker.internal for Docker-to-host communication
            # This is important because 'localhost' inside the Docker container refers
            # to the container itself, not the host machine
            'host': 'host.docker.internal',
            'port': config.get('port', 19530),
            'user': config.get('user', ''),
            'password': config.get('password', ''),
            'db_name': config.get('db_name', 'default')
        }
    
    def connect(self) -> bool:
        """Connect to Milvus via the connector.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            print(f"Connecting to Milvus connector at {self.base_url}")
            print(f"Using Milvus params: {json.dumps({k: v for k, v in self.milvus_params.items() if k != 'password'})}")
            
            # First check if the connector is running
            try:
                health_response = requests.get(
                    f"{self.base_url}/health",
                    timeout=self.timeout
                )
                if health_response.status_code != 200:
                    print(f"Milvus connector health check failed: {health_response.status_code}")
                    return False
                print("Milvus connector health check successful")
            except requests.exceptions.RequestException as e:
                print(f"Failed to connect to Milvus connector: {e}")
                return False
            
            # Now try to connect to Milvus server via the connector
            response = requests.post(
                f"{self.base_url}/connect",
                json=self.milvus_params,
                timeout=self.timeout
            )
            
            # Log the response for debugging
            print(f"Milvus connect response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Milvus connect result: {json.dumps(result)}")
                if result.get("status") == "success":
                    self.connected = True
                    print("Successfully connected to Milvus")
                    return True
                else:
                    print(f"Failed to connect to Milvus: {result.get('message', 'Unknown error')}")
            else:
                print(f"Failed to connect to Milvus: HTTP {response.status_code}")
            
            return False
        except Exception as e:
            print(f"Error connecting to Milvus: {type(e).__name__}: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Milvus.
        
        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        try:
            response = requests.post(
                f"{self.base_url}/disconnect",
                timeout=self.timeout
            )
            if response.status_code == 200:
                self.connected = False
                return True
            return False
        except Exception as e:
            print(f"Error disconnecting from Milvus: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Milvus.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("milvus_status") == "Connected"
            return False
        except Exception:
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in Milvus.
        
        Returns:
            List[str]: List of collection names.
        """
        try:
            response = requests.get(
                f"{self.base_url}/list_collections",
                timeout=self.timeout
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("collections", [])
            return []
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def create_collection(self, collection_name: str, dimension: int, **kwargs) -> bool:
        """Create a new collection in Milvus.
        
        Args:
            collection_name: Name of the collection to create.
            dimension: Dimension of vectors to store.
            **kwargs: Additional collection parameters.
                - with_metadata: Whether to include a metadata field (default: True)
                - create_index: Whether to create an index (default: True)
                - index_params: Custom index parameters
                - skip_loading: Skip loading collection into memory (default: True)
                - load_timeout: Timeout for loading collection (default: 5 seconds)
        
        Returns:
            bool: True if creation successful, False otherwise.
        """
        try:
            print(f"Creating collection {collection_name} with dimension {dimension}")
            
            # First check if the collection already exists and drop it if needed
            if collection_name in self.list_collections():
                print(f"Collection {collection_name} already exists, dropping it first")
                self.drop_collection(collection_name)
            
            # Set default parameters
            data = {
                "collection_name": collection_name,
                "dimension": dimension,
                "with_metadata": kwargs.get('with_metadata', True),  # Default to include metadata
                "create_index": kwargs.get('create_index', True),     # Default to create index
                "skip_loading": kwargs.get('skip_loading', True),     # Default to skip loading to avoid timeouts
                "load_timeout": kwargs.get('load_timeout', 5)        # Default 5 second timeout for loading
            }
            
            # Add optional index parameters if provided
            if 'index_params' in kwargs:
                data['index_params'] = kwargs['index_params']
            
            # Add any other parameters
            for k, v in kwargs.items():
                if k not in ['with_metadata', 'create_index', 'index_params', 'skip_loading', 'load_timeout']:
                    data[k] = v
            
            print(f"Sending create_collection request with data: {data}")
            
            response = requests.post(
                f"{self.base_url}/create_collection",
                json=data,
                timeout=self.timeout * 2  # Double timeout for collection creation
            )
            
            success = response.status_code == 200 and response.json().get("status") == "success"
            if success:
                print(f"Successfully created collection {collection_name}")
            else:
                print(f"Failed to create collection: {response.text}")
            
            return success
        except Exception as e:
            print(f"Error creating collection: {type(e).__name__}: {e}")
            return False
    
    def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection from Milvus.
        
        Args:
            collection_name: Name of the collection to drop.
        
        Returns:
            bool: True if drop successful, False otherwise.
        """
        try:
            response = requests.post(
                f"{self.base_url}/drop_collection",
                json={"collection_name": collection_name},
                timeout=self.timeout
            )
            
            return response.status_code == 200 and response.json().get("status") == "success"
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
        try:
            print(f"Inserting {len(vectors)} vectors into collection {collection_name}")
            
            # Ensure collection exists first
            if collection_name not in self.list_collections():
                print(f"Collection {collection_name} does not exist, creating it first")
                dimension = len(vectors[0]) if vectors and len(vectors) > 0 else 128
                if not self.create_collection(collection_name, dimension, with_metadata=(metadata is not None)):
                    print(f"Failed to create collection {collection_name}")
                    return []
                print(f"Successfully created collection {collection_name}")

            # Prepare vectors - ensure they are float32 compatible
            try:
                import numpy as np
                vectors_np = np.array(vectors, dtype=np.float32)
                vectors_list = vectors_np.tolist()
                print(f"Converted vectors to proper format, shape: {vectors_np.shape}")
            except Exception as format_error:
                print(f"Error converting vectors to proper format: {format_error}")
                # Just continue with original vectors if conversion fails
                vectors_list = vectors
            
            data = {
                "collection_name": collection_name,
                "vectors": vectors_list
            }
            
            # Process metadata if provided
            if metadata:
                # Convert metadata to strings if needed
                string_metadata = []
                for m in metadata:
                    if isinstance(m, dict):
                        string_metadata.append(json.dumps(m))
                    elif isinstance(m, str):
                        # Assume it's already JSON string
                        string_metadata.append(m)
                    else:
                        string_metadata.append(str(m))
                data["metadata"] = string_metadata
                print(f"Added {len(string_metadata)} metadata items")
            
            # Make the API call to insert vectors
            print(f"Sending insert request to {self.base_url}/insert")
            response = requests.post(
                f"{self.base_url}/insert",
                json=data,
                timeout=self.timeout * 2  # Double timeout for insertion operations
            )
            
            if response.status_code == 200 and response.json().get("status") == "success":
                ids = response.json().get("ids", [])
                print(f"Successfully inserted {len(ids)} vectors")
                return ids
            else:
                print(f"Failed to insert vectors: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error inserting vectors: {type(e).__name__}: {e}")
            return []
    
    def search(self, collection_name: str, query_vectors: List[List[float]], top_k: int = 10, **kwargs) -> List[List[Dict]]:
        """Search for similar vectors in a collection.
        
        Args:
            collection_name: Name of the collection to search in.
            query_vectors: List of query vectors.
            top_k: Number of results to return per query.
            **kwargs: Additional search parameters.
                - search_params: Custom search parameters.
        
        Returns:
            List[List[Dict]]: List of lists of search results.
        """
        try:
            print(f"Searching collection {collection_name} with {len(query_vectors)} query vectors, top_k={top_k}")
            
            # Check if collection exists
            if collection_name not in self.list_collections():
                print(f"Collection {collection_name} does not exist, cannot search")
                return []
            
            # Prepare query vectors - ensure they are float32 compatible
            try:
                import numpy as np
                query_vectors_np = np.array(query_vectors, dtype=np.float32)
                query_vectors_list = query_vectors_np.tolist()
                print(f"Converted query vectors to proper format, shape: {query_vectors_np.shape}")
            except Exception as format_error:
                print(f"Error converting query vectors to proper format: {format_error}")
                # Just continue with original vectors if conversion fails
                query_vectors_list = query_vectors
            
            # Prepare search parameters
            search_params = kwargs.get('search_params', {"metric_type": "L2", "params": {"nprobe": 10}})
            
            data = {
                "collection_name": collection_name,
                "query_vectors": query_vectors_list,
                "top_k": top_k,
                "search_params": search_params
            }
            
            # Add any other parameters
            for k, v in kwargs.items():
                if k != 'search_params':
                    data[k] = v
            
            print(f"Sending search request to {self.base_url}/search")
            response = requests.post(
                f"{self.base_url}/search",
                json=data,
                timeout=self.timeout * 2  # Double timeout for search operations
            )
            
            if response.status_code == 200 and response.json().get("status") == "success":
                results = response.json().get("results", [])
                print(f"Search returned {len(results)} result sets")
                return results
            else:
                print(f"Failed to search vectors: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error searching vectors: {type(e).__name__}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection to get statistics for.
        
        Returns:
            Dict[str, Any]: Collection statistics.
        """
        try:
            response = requests.get(
                f"{self.base_url}/get_collection_stats",
                params={"collection_name": collection_name},
                timeout=self.timeout
            )
            
            if response.status_code == 200 and response.json().get("status") == "success":
                return {
                    "num_entities": response.json().get("num_entities", 0),
                    "stats": response.json().get("stats", {})
                }
            return {"num_entities": 0, "stats": {}}
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"num_entities": 0, "stats": {}}
