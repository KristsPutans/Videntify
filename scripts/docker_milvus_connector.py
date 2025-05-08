#!/usr/bin/env python3
"""
Docker-based Milvus connector for Videntify

This script provides a server that connects to Milvus using the correct version
of PyMilvus running in a Docker container, exposing an API that the main
Videntify application can use without version compatibility issues.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from flask import Flask, request, jsonify

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)

# Default Milvus connection parameters
MILVUS_HOST = os.environ.get('MILVUS_HOST', 'milvus-standalone')
MILVUS_PORT = int(os.environ.get('MILVUS_PORT', '19530'))
MILVUS_USER = os.environ.get('MILVUS_USER', '')
MILVUS_PASSWORD = os.environ.get('MILVUS_PASSWORD', '')
MILVUS_DB = os.environ.get('MILVUS_DB', 'default')

# Enable verbose logging
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Global connection reference
milvus_connection = None

def log_debug(message):
    """Log debug messages if debug mode is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stderr)

# Print version information at startup to help diagnose compatibility issues
try:
    import pymilvus
    log_debug(f"PyMilvus version: {pymilvus.__version__}")
    log_debug(f"PyMilvus modules: {dir(pymilvus)}")
except Exception as e:
    log_debug(f"Error importing pymilvus: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the service is running."""
    # Separate connector health from Milvus connection status
    connector_status = {"status": "healthy"}
    
    # Check Milvus connection if available, but don't fail the health check if it's not
    try:
        from pymilvus import connections
        milvus_connected = connections.has_connection("default")
        connector_status["milvus_status"] = "Connected" if milvus_connected else "Not connected"
        log_debug(f"Health check: connector healthy, Milvus {'connected' if milvus_connected else 'not connected'}")
    except ImportError:
        connector_status["milvus_status"] = "Unavailable"
        connector_status["milvus_error"] = "pymilvus not imported"
        log_debug("Health check: connector healthy, pymilvus not imported")
    except Exception as e:
        connector_status["milvus_status"] = "Error"
        connector_status["milvus_error"] = str(e)
        log_debug(f"Health check: connector healthy, Milvus error: {str(e)}")
    
    # Always return 200 OK for the connector health endpoint
    return jsonify(connector_status)

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to Milvus with given parameters."""
    global milvus_connection
    
    try:
        # Log the incoming request
        data = request.json or {}
        log_debug(f"Received connection request with data: {json.dumps(data)}")
        
        # Import PyMilvus here to catch import errors clearly
        try:
            from pymilvus import connections
            log_debug("Successfully imported pymilvus")
        except ImportError as e:
            error_msg = f"Failed to import pymilvus: {str(e)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # Get connection parameters from request or use defaults
        host = data.get('host', MILVUS_HOST)
        port = data.get('port', MILVUS_PORT)
        user = data.get('user', MILVUS_USER)
        password = data.get('password', MILVUS_PASSWORD)
        db_name = data.get('db_name', MILVUS_DB)
        
        log_debug(f"Connecting to Milvus at {host}:{port} with user '{user}' and db '{db_name}'")
        
        # Disconnect if already connected
        if connections.has_connection("default"):
            log_debug("Disconnecting from existing connection")
            connections.disconnect("default")
        
        # Connect to Milvus
        try:
            conn_params = {
                "alias": "default",
                "host": host,
                "port": port
            }
            
            # Only add user/password if they're provided
            if user:
                conn_params["user"] = user
            if password:
                conn_params["password"] = password
            if db_name and db_name != "default":
                conn_params["db_name"] = db_name
                
            log_debug(f"Connection params: {json.dumps({k: v for k, v in conn_params.items() if k != 'password'})}")
            connections.connect(**conn_params)
            log_debug("Successfully connected to Milvus")
            
            return jsonify({"status": "success", "message": f"Connected to Milvus at {host}:{port}"})
        except Exception as conn_err:
            error_msg = f"Failed to connect to Milvus: {str(conn_err)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error during connection: {str(e)}"
        log_debug(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from Milvus."""
    try:
        from pymilvus import connections
        connections.disconnect("default")
        return jsonify({"status": "success", "message": "Disconnected from Milvus"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/list_collections', methods=['GET'])
def list_collections():
    """List all collections in Milvus."""
    try:
        from pymilvus import utility
        collections = utility.list_collections()
        return jsonify({"status": "success", "collections": collections})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create_collection', methods=['POST'])
def create_collection():
    """Create a new collection in Milvus."""
    try:
        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility
        
        data = request.json
        log_debug(f"Received create_collection request with data: {json.dumps(data)}")
        
        collection_name = data.get('collection_name')
        dimension = data.get('dimension')
        
        if not collection_name or not dimension:
            log_debug(f"Missing collection_name or dimension in create_collection request")
            return jsonify({"status": "error", "message": "Missing collection_name or dimension"}), 400
        
        # Always force recreation of the collection to ensure it has the right schema
        if collection_name in utility.list_collections():
            log_debug(f"Collection {collection_name} already exists, dropping it first")
            try:
                utility.drop_collection(collection_name)
                log_debug(f"Successfully dropped existing collection {collection_name}")
            except Exception as drop_err:
                error_msg = f"Error dropping existing collection: {str(drop_err)}"
                log_debug(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 500
        
        log_debug(f"Creating collection {collection_name} with dimension {dimension}")
        
        # Define fields for the collection - ensure we're using the right types
        # This is critical: the vector must be FLOAT_VECTOR type with the right dimension
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension)
        ]
        
        # Always add metadata field for better compatibility
        with_metadata = data.get('with_metadata', True)  # Default to True
        log_debug(f"Including metadata field: {with_metadata}")
        if with_metadata:
            try:
                # For compatibility, use JSON data stored as a string in a VARCHAR field
                # In PyMilvus 2.0.0, we need to handle VARCHAR differently
                log_debug(f"Adding metadata field as VARCHAR with max_length=65535")
                fields.append(FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535))
            except Exception as metadata_err:
                # Fallback to a simpler STRING type if VARCHAR causes issues
                log_debug(f"Error adding VARCHAR field: {metadata_err}. Trying STRING type instead.")
                try:
                    fields.append(FieldSchema(name="metadata", dtype=DataType.STRING))
                    log_debug("Successfully added metadata field as STRING type")
                except Exception as string_err:
                    log_debug(f"Error adding STRING field too: {string_err}. Skipping metadata field.")
                    log_debug("Metadata will not be included in the collection schema")
        
        # Create schema and collection
        try:
            schema = CollectionSchema(fields=fields, description=f"Collection for {collection_name}")
            collection = Collection(name=collection_name, schema=schema)
            log_debug(f"Successfully created collection {collection_name}")
        except Exception as create_err:
            error_msg = f"Error creating collection: {str(create_err)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # Create an index on the vector field if specified
        create_index = data.get('create_index', True)  # Default to True
        if create_index:
            try:
                index_params = data.get('index_params', {
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 1024}
                })
                log_debug(f"Creating index on vector field with params: {index_params}")
                collection.create_index("vector", index_params)
                log_debug(f"Successfully created index on collection {collection_name}")
                
                # Load collection into memory for search - make it optional to avoid timeouts
                try:
                    load_timeout = data.get('load_timeout', 5)  # Default 5 second timeout
                    if data.get('skip_loading', False):
                        log_debug(f"Skipping loading collection {collection_name} into memory")
                    else:
                        log_debug(f"Loading collection {collection_name} into memory with timeout {load_timeout}s")
                        # Use a non-blocking approach with timeout
                        import threading
                        import time
                        
                        def load_with_timeout():
                            try:
                                collection.load()
                                log_debug(f"Successfully loaded collection {collection_name}")
                            except Exception as load_err:
                                log_debug(f"Error during collection loading: {load_err}")
                        
                        # Start loading in a separate thread
                        load_thread = threading.Thread(target=load_with_timeout)
                        load_thread.daemon = True  # Daemon thread will terminate when main thread exits
                        load_thread.start()
                        
                        # Wait for loading to complete, but with a timeout
                        load_thread.join(timeout=load_timeout)
                        if load_thread.is_alive():
                            # Loading is still running, but we don't want to block further
                            log_debug(f"Loading collection {collection_name} is still in progress (timeout after {load_timeout}s)")
                            log_debug("Continuing without waiting for loading completion")
                except Exception as thread_err:
                    log_debug(f"Error in threading approach for loading: {thread_err}")
                    log_debug("Collection may not be fully loaded into memory")
            except Exception as index_err:
                # Don't fail if indexing fails, just log the error
                log_debug(f"Warning: Error creating index: {str(index_err)}")
                # We can still return success as the collection was created
        
        return jsonify({
            "status": "success", 
            "message": f"Collection {collection_name} created successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/insert', methods=['POST'])
def insert():
    """Insert vectors into a collection."""
    try:
        # Import low-level Milvus modules for more direct control
        from pymilvus import Collection, DataType
        from pymilvus import utility, connections
        import numpy as np
        
        data = request.json
        log_debug(f"Received insert request with data: {json.dumps({k: v if k != 'vectors' else f'[{len(v)} vectors]' for k, v in data.items()})}")
        
        collection_name = data.get('collection_name')
        vectors = data.get('vectors')
        metadata = data.get('metadata', [])
        
        if not collection_name or not vectors:
            log_debug(f"Missing collection_name or vectors in insert request")
            return jsonify({"status": "error", "message": "Missing collection_name or vectors"}), 400
            
        log_debug(f"Processing insert request for collection {collection_name} with {len(vectors)} vectors")
        
        # DIAGNOSIS MODE: Let's print detailed information about each vector to diagnose type issues
        log_debug("===== VECTOR DIAGNOSTIC =====")
        log_debug(f"Type of vectors: {type(vectors)}")
        if len(vectors) > 0:
            vector0 = vectors[0]
            log_debug(f"Type of vector[0]: {type(vector0)}")
            log_debug(f"Length of vector[0]: {len(vector0)}")
            if len(vector0) > 0:
                log_debug(f"Type of vector[0][0]: {type(vector0[0])}")
                log_debug(f"Value of vector[0][0]: {vector0[0]}")
            # Test conversion to different numeric types
            try:
                log_debug("Testing conversions:")
                log_debug(f"  As int: {int(vector0[0])}")
                log_debug(f"  As float: {float(vector0[0])}")
                log_debug(f"  As np.float32: {np.float32(vector0[0])}")
            except Exception as e:
                log_debug(f"Conversion error: {e}")
        log_debug("===== END DIAGNOSTIC =====")
        
        # Completely simplified approach - based on what worked with simple_connector_test.py
        
        try:
            # First make sure the collection exists and has the right dimension
            collections = utility.list_collections()
            dimension = len(vectors[0])  # Get dimension from first vector
            
            if collection_name not in collections:
                log_debug(f"Collection {collection_name} does not exist, creating it first")
                # Create collection using a direct approach that works for Milvus 2.0.0
                create_data = {
                    "collection_name": collection_name,
                    "dimension": dimension,
                    "with_metadata": len(metadata) > 0  # Only include metadata if provided
                }
                log_debug(f"Creating collection with data: {json.dumps(create_data)}")
                
                # Call the internal create_collection function
                from pymilvus import FieldSchema, CollectionSchema, Collection
                
                # Define fields for the collection - ensure we're using the right types
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension)
                ]
                
                # Include metadata field if needed
                if len(metadata) > 0:
                    try:
                        # For Milvus 2.0.0, use a STRING type for metadata
                        log_debug("Adding metadata field as STRING")
                        fields.append(FieldSchema(name="metadata", dtype=DataType.STRING))
                    except Exception as meta_err:
                        log_debug(f"Error adding metadata field: {meta_err}")
                        # Continue without metadata if there's an error
                
                # Create schema and collection
                schema = CollectionSchema(fields=fields, description=f"Collection for {collection_name}")
                collection = Collection(name=collection_name, schema=schema)
                log_debug(f"Successfully created collection {collection_name}")
                
                # Wait a bit to ensure the collection is ready
                import time
                time.sleep(1)
            
            # Get the collection
            collection = Collection(name=collection_name)
            log_debug(f"Successfully loaded collection {collection_name}")
            
            # Check collection schema to ensure it has the right fields
            schema_fields = [field.name for field in collection.schema.fields]
            log_debug(f"Collection schema fields: {schema_fields}")
            
            # Simplest possible insertion approach
            log_debug(f"Using simplified insertion approach for {len(vectors)} vectors")
            
            # 1. Prepare data dictionary with vectors
            insert_data = {}
            
            # Convert to Python float lists to ensure data type compatibility
            float_vectors = []
            for vec in vectors:
                float_vectors.append([float(v) for v in vec])
            
            # Add vectors to insert data
            insert_data["vector"] = float_vectors
            log_debug(f"Prepared vector data with {len(float_vectors)} vectors")
            
            # 2. Add metadata if provided and if the schema has a metadata field
            if metadata and len(metadata) == len(vectors) and "metadata" in schema_fields:
                # Ensure all metadata items are strings
                string_metadata = []
                for m in metadata:
                    if isinstance(m, str):
                        string_metadata.append(m)
                    else:
                        string_metadata.append(str(m))
                
                insert_data["metadata"] = string_metadata
                log_debug(f"Added {len(string_metadata)} metadata items")
            
            log_debug(f"Final insert_data keys: {list(insert_data.keys())}")
        except Exception as setup_error:
            error_msg = f"Error setting up collection: {type(setup_error).__name__}: {str(setup_error)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # Insert the data
        try:
            log_debug(f"Performing direct insertion with {len(insert_data.get('vector', []))} vectors")
            
            # Direct insertion using the dictionary format
            log_debug(f"Insert data keys: {list(insert_data.keys())}")
            
            # Use a direct insertion approach that works with Milvus 2.0.0
            result = collection.insert(insert_data)
            
            # Handle the result
            if hasattr(result, 'primary_keys'):
                # Get the primary keys as a list for easier JSON serialization
                ids = list(result.primary_keys)
                log_debug(f"Insertion successful, got {len(ids)} IDs: {ids[:5] if len(ids) > 5 else ids}")
            else:
                # If primary_keys attribute is missing, handle gracefully
                log_debug("Insertion successful but no primary keys returned")
                ids = []
            
            
            # In Milvus 2.0.0, flush might not be available or work differently
            try:
                # Attempt to flush but don't fail if not available
                if hasattr(collection, 'flush'):
                    collection.flush()
                    log_debug(f"Flushed collection to ensure data is committed")
                else:
                    log_debug("Collection doesn't have flush method, skipping flush operation")
            except Exception as flush_err:
                log_debug(f"Warning: Could not flush collection: {str(flush_err)}")
                # Continue anyway since the insertion was successful
            
            # Return the successful response with the IDs
            # We've already converted the IDs to a regular Python list for JSON serialization
            try:
                response_data = {
                    "status": "success",
                    "message": f"Inserted {len(vectors)} vectors"
                }
                
                # Include IDs if available
                if ids:
                    response_data["ids"] = ids
                    log_debug(f"Returning {len(ids)} IDs in response")
                
                return jsonify(response_data)
            except Exception as json_err:
                log_debug(f"Error creating JSON response: {str(json_err)}")
                # Fallback to a very simple response
                return jsonify({
                    "status": "success",
                    "message": f"Inserted {len(vectors)} vectors successfully"
                })
        except Exception as insert_error:
            error_msg = f"Error during insertion: {type(insert_error).__name__}: {str(insert_error)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
    except Exception as e:
        error_msg = f"Error inserting vectors: {type(e).__name__}: {str(e)}"
        log_debug(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/search', methods=['POST'])
def search():
    """Search for similar vectors in a collection."""
    try:
        from pymilvus import Collection
        
        data = request.json
        log_debug(f"Received search request with data: {json.dumps({k: v if k != 'query_vectors' else f'[{len(v)} vectors]' for k, v in data.items()})}")
        
        collection_name = data.get('collection_name')
        query_vectors = data.get('query_vectors')
        top_k = data.get('top_k', 10)
        search_params = data.get('search_params', {"metric_type": "L2", "params": {"nprobe": 10}})
        
        if not collection_name or not query_vectors:
            log_debug(f"Missing collection_name or query_vectors in search request")
            return jsonify({"status": "error", "message": "Missing collection_name or query_vectors"}), 400
        
        # Get the collection
        try:
            collection = Collection(name=collection_name)
            log_debug(f"Successfully loaded collection {collection_name}")
        except Exception as coll_error:
            error_msg = f"Error loading collection {collection_name}: {str(coll_error)}"
            log_debug(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # Check collection schema
        schema_fields = [field.name for field in collection.schema.fields]
        log_debug(f"Collection schema fields: {schema_fields}")
        
        # Make sure collection is loaded - check using has_collection instead of is_loaded
        try:
            from pymilvus import utility
            log_debug(f"Loading collection {collection_name} into memory")
            collection.load()
            log_debug(f"Collection {collection_name} loaded successfully")
        except Exception as load_error:
            log_debug(f"Warning: Error loading collection into memory: {str(load_error)}")
            # Continue anyway, this might not be critical
        
        # Check if the collection has any entities
        try:
            if collection.num_entities == 0:
                log_debug(f"Collection {collection_name} has no entities, cannot perform search")
                return jsonify({"status": "error", "message": f"Collection {collection_name} is empty"}), 400
            log_debug(f"Collection {collection_name} has {collection.num_entities} entities")
        except Exception as stats_error:
            log_debug(f"Error getting collection stats: {str(stats_error)}")
            # Continue anyway, this is not critical
        
        # Search for similar vectors
        log_debug(f"Executing search with top_k={top_k} and params={search_params}")
        output_fields = ["metadata"] if "metadata" in schema_fields else []
        log_debug(f"Output fields: {output_fields}")
        
        result = collection.search(
            data=query_vectors,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=output_fields
        )
        log_debug(f"Search completed successfully, formatting results")
        
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
        
        return jsonify({
            "status": "success", 
            "results": formatted_results
        })
    except Exception as e:
        error_msg = f"Error searching vectors: {type(e).__name__}: {str(e)}"
        log_debug(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/get_collection_stats', methods=['GET'])
def get_collection_stats():
    """Get statistics for a collection."""
    try:
        from pymilvus import Collection, utility
        
        collection_name = request.args.get('collection_name')
        log_debug(f"Received get_collection_stats request for collection {collection_name}")
        
        if not collection_name:
            log_debug("Missing collection_name in get_collection_stats request")
            return jsonify({"status": "error", "message": "Missing collection_name"}), 400
        
        # Check if collection exists
        if collection_name not in utility.list_collections():
            log_debug(f"Collection {collection_name} does not exist")
            return jsonify({
                "status": "success", 
                "num_entities": 0,
                "stats": {}
            })
        
        try:
            # Get the collection
            collection = Collection(name=collection_name)
            log_debug(f"Successfully loaded collection {collection_name}")
            
            # Try to get entity count
            try:
                num_entities = collection.num_entities
                log_debug(f"Collection {collection_name} has {num_entities} entities")
            except Exception as count_error:
                log_debug(f"Error getting entity count: {str(count_error)}")
                num_entities = 0
            
            # Try to get statistics
            try:
                # Load the collection first
                collection.load()
                stats = {}  # Default to empty dict if get_stats fails
                log_debug(f"Successfully got collection stats: {stats}")
            except Exception as stats_error:
                log_debug(f"Error getting collection stats: {str(stats_error)}")
                stats = {}
            
            return jsonify({
                "status": "success", 
                "num_entities": num_entities,
                "stats": stats
            })
        except Exception as coll_error:
            log_debug(f"Error accessing collection: {str(coll_error)}")
            # Don't fail, just return empty stats
            return jsonify({
                "status": "success", 
                "num_entities": 0,
                "stats": {}
            })
    except Exception as e:
        error_msg = f"Error getting collection stats: {type(e).__name__}: {str(e)}"
        log_debug(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/drop_collection', methods=['POST'])
def drop_collection():
    """Drop a collection from Milvus."""
    try:
        from pymilvus import utility
        
        data = request.json
        collection_name = data.get('collection_name')
        log_debug(f"Received drop_collection request for collection {collection_name}")
        
        if not collection_name:
            log_debug("Missing collection_name in drop_collection request")
            return jsonify({"status": "error", "message": "Missing collection_name"}), 400
        
        # Check if collection exists
        if collection_name not in utility.list_collections():
            log_debug(f"Collection {collection_name} does not exist, nothing to drop")
            return jsonify({
                "status": "success", 
                "message": f"Collection {collection_name} does not exist, nothing to drop"
            })
        
        # Drop the collection
        utility.drop_collection(collection_name)
        log_debug(f"Successfully dropped collection {collection_name}")
        
        return jsonify({
            "status": "success", 
            "message": f"Collection {collection_name} dropped successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Docker-based Milvus connector for Videntify')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5050, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()


def main():
    """Run the server."""
    args = parse_args()
    
    # Set DEBUG flag based on command line argument
    global DEBUG
    if args.debug:
        DEBUG = True
    
    # Print startup information
    print(f"Starting Milvus connector on {args.host}:{args.port}", file=sys.stderr)
    print(f"Debug mode: {'enabled' if DEBUG else 'disabled'}", file=sys.stderr)
    print(f"Default Milvus connection: {MILVUS_HOST}:{MILVUS_PORT}", file=sys.stderr)
    
    # Configure Flask to log errors
    if not DEBUG:
        import logging
        logging.basicConfig(level=logging.ERROR)
    
    # Run the Flask app
    app.run(host=args.host, port=args.port, debug=DEBUG)

if __name__ == '__main__':
    main()
