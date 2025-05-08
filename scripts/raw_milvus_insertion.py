#!/usr/bin/env python3
"""
Raw Milvus Insertion Test

This script bypasses the connector entirely and uses the PyMilvus client directly.
"""

import os
import sys
import time
import numpy as np

def main():
    print("===== Raw Milvus Insertion Test =====")
    print("Importing PyMilvus...")
    
    try:
        from pymilvus import (
            connections, Collection, FieldSchema, CollectionSchema, DataType,
            utility
        )
        print("✅ PyMilvus imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PyMilvus: {e}")
        print("Try installing with: pip install pymilvus==2.0.0")
        return False
    
    try:
        print(f"\nPyMilvus version: {utility.__version__}")
    except:
        print("Could not determine PyMilvus version")
    
    # Connect directly to Milvus
    print("\nConnecting to Milvus...")
    try:
        connections.connect(
            alias="default", 
            host="host.docker.internal",  # Use Docker host routing for Mac
            port="19530"
        )
        print("✅ Connected to Milvus directly")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Collection parameters
    collection_name = "raw_test_collection"
    dim = 8
    
    # Clean up any existing collection
    if utility.has_collection(collection_name):
        print(f"\nDropping existing collection {collection_name}...")
        utility.drop_collection(collection_name)
        print(f"✅ Dropped collection {collection_name}")
    
    # Create collection
    print(f"\nCreating collection {collection_name}...")
    try:
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        
        schema = CollectionSchema(fields=fields, description=f"Test collection {collection_name}")
        collection = Collection(name=collection_name, schema=schema)
        print(f"✅ Created collection {collection_name}")
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        return False
    
    # Prepare test data using different formats to test compatibility
    print("\nPreparing test vectors...")
    
    # Format 1: Python list of Python lists with Python floats
    vectors_python = [
        [float(i) for i in range(1, dim+1)],
        [float(dim-i+1) for i in range(1, dim+1)]
    ]
    print(f"1. Python lists: {vectors_python[0][:3]}...")
    print(f"   Type: {type(vectors_python)} -> {type(vectors_python[0])} -> {type(vectors_python[0][0])}")
    
    # Format 2: NumPy array with float32
    vectors_np32 = np.array(vectors_python, dtype=np.float32)
    print(f"2. NumPy float32: {vectors_np32[0][:3]}...")
    print(f"   Type: {type(vectors_np32)}, dtype: {vectors_np32.dtype}")
    
    # Format 3: NumPy array with float64
    vectors_np64 = np.array(vectors_python, dtype=np.float64)
    print(f"3. NumPy float64: {vectors_np64[0][:3]}...")
    print(f"   Type: {type(vectors_np64)}, dtype: {vectors_np64.dtype}")
    
    # Try inserting each format
    print("\nAttempting insertions with different formats...")
    
    # 1. Python lists
    print("\n1. Trying Python lists...")
    try:
        # The Milvus 2.0.0 API expects a dictionary mapping field names to values
        data = {"vector": vectors_python}
        
        # Print exact structure for debugging
        print(f"   Data format: {type(data)}")
        print(f"   Data keys: {list(data.keys())}")
        print(f"   Data['vector'] type: {type(data['vector'])}")
        print(f"   Data['vector'][0] type: {type(data['vector'][0])}")
        
        # Detailed debugging of exact data structure
        print("   Trying to iterate through data:")
        for field_name, field_values in data.items():
            print(f"     Field '{field_name}': {len(field_values)} values of type {type(field_values[0])}")
        
        result = collection.insert(data)
        if hasattr(result, 'primary_keys'):
            print(f"✅ Insertion successful, got IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
        else:
            print(f"✅ Insertion successful, but no IDs returned")
            
    except Exception as e:
        print(f"❌ Python list insertion failed: {type(e).__name__}: {e}")
        
        # If we got a DataTypeNotSupportException, try to cast each element manually
        if "DataTypeNotSupportException" in str(e):
            print("\n   Attempting with explicit individual float conversions...")
            try:
                # Cast each element explicitly to Python float
                explicit_vectors = []
                for vec in vectors_python:
                    explicit_vectors.append([float(val) for val in vec])
                    
                data = {"vector": explicit_vectors}
                result = collection.insert(data)
                if hasattr(result, 'primary_keys'):
                    print(f"   ✅ Explicit float casting worked! IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
                else:
                    print(f"   ✅ Explicit float casting worked, but no IDs returned")
            except Exception as e2:
                print(f"   ❌ Explicit float casting failed: {type(e2).__name__}: {e2}")
    
    # 2. NumPy float32
    print("\n2. Trying NumPy float32 array...")
    try:
        data = {"vector": vectors_np32}
        result = collection.insert(data)
        if hasattr(result, 'primary_keys'):
            print(f"✅ Insertion successful, got IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
        else:
            print(f"✅ Insertion successful, but no IDs returned")
    except Exception as e:
        print(f"❌ NumPy float32 insertion failed: {type(e).__name__}: {e}")
        
        # Try converting to list
        print("   Attempting with float32 array converted to list...")
        try:
            data = {"vector": vectors_np32.tolist()}
            result = collection.insert(data)
            if hasattr(result, 'primary_keys'):
                print(f"   ✅ Float32 to list conversion worked! IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
            else:
                print(f"   ✅ Float32 to list conversion worked, but no IDs returned")
        except Exception as e2:
            print(f"   ❌ Float32 to list conversion failed: {type(e2).__name__}: {e2}")
    
    # 3. NumPy float64
    print("\n3. Trying NumPy float64 array...")
    try:
        data = {"vector": vectors_np64}
        result = collection.insert(data)
        if hasattr(result, 'primary_keys'):
            print(f"✅ Insertion successful, got IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
        else:
            print(f"✅ Insertion successful, but no IDs returned")
    except Exception as e:
        print(f"❌ NumPy float64 insertion failed: {type(e).__name__}: {e}")
        
        # Try converting to list
        print("   Attempting with float64 array converted to list...")
        try:
            data = {"vector": vectors_np64.tolist()}
            result = collection.insert(data)
            if hasattr(result, 'primary_keys'):
                print(f"   ✅ Float64 to list conversion worked! IDs: {result.primary_keys[:5] if len(result.primary_keys) > 5 else result.primary_keys}")
            else:
                print(f"   ✅ Float64 to list conversion worked, but no IDs returned")
        except Exception as e2:
            print(f"   ❌ Float64 to list conversion failed: {type(e2).__name__}: {e2}")
    
    print("\n===== Test Complete =====")
    
    # Cleanup
    try:
        connections.disconnect("default")
        print("Disconnected from Milvus")
    except:
        pass
    
    return True

if __name__ == "__main__":
    main()
