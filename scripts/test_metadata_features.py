"""Focused Test Script for Metadata Enrichment System Features

This script specifically demonstrates:
1. Different user roles and their access levels
2. Caching performance improvements
3. Generation of UI-ready data for frontend consumption
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pprint import pprint

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.metadata_enrichment import MetadataEnrichmentEngine
from src.core.metadata_auth import MetadataAuthManager, UserInfo, UserRole, MetadataScope
from src.core.metadata_cache import MetadataCache
from src.core.metadata_field_permissions import get_content_type_ttl, get_field_scope

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample movie data for testing
SAMPLE_CONTENTS = [
    {
        "content_id": "vid001",
        "title": "The Matrix",
        "type": "movie",
        "release_date": "1999-03-31",
        "overview": "A computer hacker learns about the true nature of reality.",
        "genres": ["Action", "Sci-Fi"],
        "runtime": 136,
        "tmdb_id": 603,
        "directors": ["Lana Wachowski", "Lilly Wachowski"],
        "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
        "vote_average": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/fNG7i7RqMErkcqhohV2a6cV1Ehy.jpg",
        "budget": 63000000,
        "revenue": 463517383,
        "filming_locations": [
            {"name": "Sydney, Australia", "coordinates": [151.2093, -33.8688]}
        ],
        "streaming_services": [
            {"name": "Netflix", "url": "https://netflix.com/watch/123"},
            {"name": "HBO Max", "url": "https://hbomax.com/watch/456"}
        ],
        "content_type": "movie",
        "file_path": "/sample/path/matrix.mp4",
        "file_size": 1543503872,
        "codec": "h264",
        "themes": ["virtual reality", "dystopia", "artificial intelligence"],
        "soundtrack_url": "https://open.spotify.com/album/2Q3SJFpI0klazNLkbmjSpy"
    }
]

# Mock authentication configuration
AUTH_CONFIG = {
    "auth": {
        "enable_auth": True,
        "default_role": "guest",
        "token_expiry_seconds": 3600,
        "role_permissions": {
            "guest": ["public"],
            "user": ["public", "basic_info"],
            "premium": ["public", "basic_info", "external_api"],
            "staff": ["public", "basic_info", "external_api", "sensitive"],
            "admin": ["public", "basic_info", "external_api", "sensitive", "admin"]
        }
    },
    "users": [
        {
            "user_id": "guest",
            "username": "guest",
            "role": "guest"
        },
        {
            "user_id": "user1",
            "username": "regular_user",
            "role": "user",
            "api_keys": ["user1_api_key"]
        },
        {
            "user_id": "premium1",
            "username": "premium_user",
            "role": "premium",
            "api_keys": ["premium1_api_key"]
        },
        {
            "user_id": "staff1",
            "username": "staff_user",
            "role": "staff",
            "api_keys": ["staff1_api_key"]
        },
        {
            "user_id": "admin1",
            "username": "admin_user",
            "role": "admin",
            "api_keys": ["admin1_api_key"]
        }
    ]
}

# Cache configuration
CACHE_CONFIG = {
    "enabled": True,
    "memory_cache": {
        "enabled": True,
        "ttl": 3600,       # 1 hour in memory
        "max_size": 1000,  # Max 1000 entries
    },
    "file_cache": {
        "enabled": True,
        "ttl": 86400,     # 24 hours on disk
        "directory": "/tmp/videntify_test_cache",
        "max_size_mb": 100 # Max 100MB
    },
    "redis_cache": {
        "enabled": False   # Redis disabled for this test
    }
}

async def main():
    # Initialize services
    auth_manager = MetadataAuthManager(AUTH_CONFIG)
    metadata_cache = MetadataCache(CACHE_CONFIG)
    
    # Create tokens for testing
    tokens = {
        "guest": None,  # No token for guest
        "user": auth_manager.create_auth_token("user1"),
        "premium": auth_manager.create_auth_token("premium1"),
        "staff": auth_manager.create_auth_token("staff1"),
        "admin": auth_manager.create_auth_token("admin1")
    }
    
    # Test 1: Different user roles and their access levels
    print("\n\n===== TEST 1: USER ROLES AND ACCESS LEVELS =====\n")
    await test_user_roles_access(auth_manager, tokens)
    
    # Test 2: Caching performance improvements
    print("\n\n===== TEST 2: CACHING PERFORMANCE IMPROVEMENTS =====\n")
    await test_caching_performance(metadata_cache)
    
    # Test 3: Generating UI-ready data
    print("\n\n===== TEST 3: UI-READY DATA GENERATION =====\n")
    await test_ui_data_generation(auth_manager, tokens)

async def test_user_roles_access(auth_manager, tokens):
    """Test different user roles and their access to metadata fields."""
    # Sample full metadata with fields of varying permission levels
    sample_metadata = SAMPLE_CONTENTS[0]
    
    # Test each role
    results = {}
    roles = ["guest", "user", "premium", "staff", "admin"]
    
    for role in roles:
        print(f"\n=== Testing {role.upper()} role access ===\n")
        
        # Authenticate with appropriate token
        auth_header = None if role == "guest" else f"Bearer {tokens[role]}"
        user = auth_manager.authenticate(auth_header=auth_header)
        
        print(f"Authenticated as: {user.username} with role {user.role}")
        print(f"Scopes: {', '.join(s.value for s in user.scopes)}")
        
        # Filter metadata based on role permissions
        filtered_metadata = auth_manager.filter_metadata_fields(sample_metadata, user)
        results[role] = filtered_metadata
        
        # Print accessible fields
        field_count = len(filtered_metadata)
        print(f"Can access {field_count} fields out of {len(sample_metadata)} total fields")
        print("Sample of accessible fields:")
        
        # Print a sample of the accessible fields
        sample_fields = list(filtered_metadata.keys())[:min(5, field_count)]
        for field in sample_fields:
            field_value = filtered_metadata[field]
            display_value = str(field_value)
            if isinstance(field_value, list) and len(field_value) > 2:
                display_value = f"[{field_value[0]}, {field_value[1]}, ...]" 
            elif len(display_value) > 50:
                display_value = display_value[:50] + "..."
                
            print(f"  - {field}: {display_value}")
    
    # Analyze results
    print("\n=== Role Access Comparison ===\n")
    all_fields = set()
    for role_data in results.values():
        all_fields.update(role_data.keys())
    
    field_access_table = {}
    for field in sorted(all_fields):
        field_access_table[field] = {
            role: field in results[role] for role in roles
        }
    
    # Print access matrix for a few interesting fields
    interesting_fields = [
        "title", "poster_url", "overview", "genres", "tmdb_id", 
        "streaming_services", "budget", "file_path", "themes"
    ]
    
    print(f"{'Field':<20} | {'Guest':<6} | {'User':<6} | {'Premium':<7} | {'Staff':<6} | {'Admin':<6}")
    print(f"{'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*7}-+-{'-'*6}-+-{'-'*6}")
    
    for field in interesting_fields:
        if field in field_access_table:
            access_row = field_access_table[field]
            print(f"{field:<20} | {str(access_row['guest']):<6} | {str(access_row['user']):<6} | "
                  f"{str(access_row['premium']):<7} | {str(access_row['staff']):<6} | {str(access_row['admin']):<6}")

async def test_caching_performance(metadata_cache):
    """Test caching performance improvements."""
    # Sample data for cache testing
    cache_test_data = {
        "small": {"content_id": "small001", "title": "Small Test Data", "value": "x" * 100},  # 100 bytes
        "medium": {"content_id": "medium001", "title": "Medium Test Data", "value": "x" * 10000},  # 10KB
        "large": {"content_id": "large001", "title": "Large Test Data", "value": "x" * 1000000}  # 1MB
    }
    
    # Test cache operations
    print("Testing cache performance for different data sizes...\n")
    
    for data_type, data in cache_test_data.items():
        content_id = data["content_id"]
        data_size = len(json.dumps(data))
        
        print(f"=== {data_type.upper()} Data ({data_size} bytes) ===\n")
        
        # Test 1: Without cache (first access)
        metadata_cache.invalidate(content_id)  # Ensure no cache exists
        
        start_time = time.time()
        cache_result = metadata_cache.get(content_id)
        uncached_time = time.time() - start_time
        print(f"Uncached access (miss): {uncached_time*1000:.2f} ms")
        print(f"Result: {cache_result is None}")
        
        # Test 2: Write to cache
        start_time = time.time()
        metadata_cache.set(content_id, data)
        cache_write_time = time.time() - start_time
        print(f"Cache write time: {cache_write_time*1000:.2f} ms")
        
        # Test 3: Memory cache hit
        start_time = time.time()
        memory_result = metadata_cache.get(content_id)
        memory_time = time.time() - start_time
        print(f"Memory cache hit: {memory_time*1000:.2f} ms")
        
        # Test 4: Clear memory and test file cache
        metadata_cache.memory_cache = {}  # Clear memory cache
        
        start_time = time.time()
        file_result = metadata_cache.get(content_id)
        file_time = time.time() - start_time
        print(f"File cache hit: {file_time*1000:.2f} ms")
        
        # Performance comparison
        if memory_time > 0 and file_time > 0:
            memory_vs_uncached = "∞" if uncached_time == 0 else f"{uncached_time/memory_time:.1f}x"
            file_vs_uncached = "∞" if uncached_time == 0 else f"{uncached_time/file_time:.1f}x"
            memory_vs_file = f"{file_time/memory_time:.1f}x"
            
            print(f"\nPerformance improvements:")
            print(f"- Memory cache vs. uncached: {memory_vs_uncached} faster")
            print(f"- File cache vs. uncached: {file_vs_uncached} faster")
            print(f"- Memory cache vs. file cache: {memory_vs_file} faster")
        print()
    
    # Cache statistics
    cache_stats = metadata_cache.get_stats()
    print("\n=== Cache Statistics ===\n")
    pprint(cache_stats)

async def test_ui_data_generation(auth_manager, tokens):
    """Generate UI-ready data for different user roles."""
    # Sample full metadata for a movie
    sample_metadata = SAMPLE_CONTENTS[0]
    
    # Generate UI data for each role
    for role in ["guest", "user", "premium", "admin"]:
        print(f"\n=== Generating UI data for {role.upper()} role ===\n")
        
        # Authenticate with appropriate token
        auth_header = None if role == "guest" else f"Bearer {tokens[role]}"
        user = auth_manager.authenticate(auth_header=auth_header)
        
        # Filter metadata based on role permissions
        filtered_metadata = auth_manager.filter_metadata_fields(sample_metadata, user)
        
        # Convert to UI-ready format
        ui_data = prepare_ui_data(filtered_metadata, role)
        
        # Save to file for UI testing
        ui_file_path = f"/tmp/videntify_ui_{role}.json"
        with open(ui_file_path, "w") as f:
            json.dump(ui_data, f, indent=2)
            
        print(f"Saved UI-ready data to {ui_file_path}")
        print(f"UI data contains {len(ui_data['metadata'])} metadata fields and {len(ui_data['categories'])} categories")
        
        # Print main categories available to this role
        print("Available categories:")
        for category in ui_data['categories']:
            field_count = len(ui_data['categoryFields'].get(category, []))
            print(f"  - {category}: {field_count} fields")

def prepare_ui_data(metadata, role):
    """Prepare metadata for UI display based on user role."""
    # Define UI categories and their fields
    categories = {
        "basic": ["title", "release_date", "genres", "runtime", "vote_average", "directors", "overview"],
        "media": ["poster_url", "backdrop_url", "thumbnail_url", "locations_map_url", "filming_locations", "cast"],
        "content": ["themes", "mood", "time_period", "keywords", "soundtrack_url", "soundtrack_artists"],
        "external": ["streaming_services", "purchase_options", "tmdb_id", "imdb_id", "wikipedia_url"],
        "technical": ["content_id", "file_size", "codec", "duration", "content_type"]
    }
    
    # Filter categories based on data available for this role
    available_categories = []
    category_fields = {}
    
    for category, fields in categories.items():
        available_fields = [field for field in fields if field in metadata]
        if available_fields:
            available_categories.append(category)
            category_fields[category] = available_fields
    
    # Prepare UI-friendly data structure
    ui_data = {
        "metadata": metadata,
        "role": role,
        "categories": available_categories,
        "categoryFields": category_fields,
        "timestamp": datetime.now().isoformat()
    }
    
    return ui_data

if __name__ == "__main__":
    asyncio.run(main())
