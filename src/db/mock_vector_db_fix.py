"""Fix for the MockVectorDBClient

This script adds the missing list_collections method to the MockVectorDBClient class.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.db.mock_vector_db import MockVectorDBClient

# Monkey patch the missing method
def list_collections(self):
    """List all collections in the mock vector database.
    
    Returns:
        List of collection names
    """
    if not self.connected:
        self.connect()
    
    return list(self.collections.keys())

# Monkey patch the get_collection_stats method
def get_collection_stats(self, collection_name):
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

def apply_fixes():
    """Apply fixes to the MockVectorDBClient class."""
    # Add the list_collections method if it doesn't exist
    if not hasattr(MockVectorDBClient, 'list_collections') or \
       MockVectorDBClient.list_collections.__name__ == 'list_collections':
        MockVectorDBClient.list_collections = list_collections
        print("✅ Added list_collections method to MockVectorDBClient")
    
    # Add the get_collection_stats method if it doesn't exist
    if not hasattr(MockVectorDBClient, 'get_collection_stats') or \
       MockVectorDBClient.get_collection_stats.__name__ == 'get_collection_stats':
        MockVectorDBClient.get_collection_stats = get_collection_stats
        print("✅ Added get_collection_stats method to MockVectorDBClient")

if __name__ == "__main__":
    apply_fixes()
    print("✅ MockVectorDBClient fixes applied successfully")
