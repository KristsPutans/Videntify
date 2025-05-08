"""Test Script for the Complete Metadata Enrichment System

This script demonstrates all aspects of the enhanced metadata system:
1. Custom enrichers for unique data sources
2. Authentication integration with user permissions
3. Caching optimization with multi-level caching
4. Data preparation for UI display
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

from src.core.metadata_enrichment import (
    MetadataEnrichmentEngine, 
    MetadataSource, 
    EnrichmentPriority
)
from src.core.custom_enrichers import (
    SpotifyEnricher,
    WikipediaEnricher,
    LocationEnricher,
    ContentAnalysisEnricher
)
from src.core.metadata_auth import (
    MetadataAuthManager,
    UserInfo,
    UserRole,
    MetadataScope
)
from src.core.metadata_cache import (
    MetadataCache,
    CacheLevel,
    CachePriority
)

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
        "file_path": "/sample/path/matrix.mp4",
        "tmdb_id": 603
    },
    {
        "content_id": "vid002",
        "title": "Inception",
        "type": "movie",
        "file_path": "/sample/path/inception.mp4",
        "tmdb_id": 27205
    },
    {
        "content_id": "vid003",
        "title": "Breaking Bad",
        "type": "tv",
        "file_path": "/sample/path/breaking_bad.mp4",
        "tmdb_id": 1396
    }
]

# Mapping of themes for content analysis
THEMES_MAPPING = {
    "action": ["fight", "explosion", "chase", "hero", "villain"],
    "sci-fi": ["future", "technology", "space", "alien", "robot", "artificial intelligence"],
    "drama": ["emotional", "relationship", "struggle", "family", "conflict"],
    "thriller": ["suspense", "mystery", "tension", "crime", "detective"],
    "romance": ["love", "relationship", "romantic", "couple", "marriage"],
    "comedy": ["funny", "humor", "laugh", "joke", "comedy"],
    "horror": ["scary", "fear", "monster", "terror", "supernatural"],
    "documentary": ["real", "historical", "educational", "interview", "footage"],
    "animation": ["cartoon", "animated", "animation", "pixar", "disney"]
}

# Mapping of genres to themes
GENRES_TO_THEMES = {
    "Action": ["action"],
    "Adventure": ["action"],
    "Animation": ["animation"],
    "Comedy": ["comedy"],
    "Crime": ["thriller"],
    "Documentary": ["documentary"],
    "Drama": ["drama"],
    "Fantasy": ["sci-fi"],
    "Horror": ["horror"],
    "Romance": ["romance"],
    "Science Fiction": ["sci-fi"],
    "Thriller": ["thriller"]
}

# Mock database client
class MockDatabaseClient:
    async def get_content_metadata(self, content_id):
        # Return mock metadata based on content_id
        if content_id == "vid001":
            return {
                "title": "The Matrix",
                "director": "Lana Wachowski, Lilly Wachowski",
                "year": 1999,
                "genres": ["Action", "Sci-Fi"],
                "runtime": 136,
                "tmdb_id": 603
            }
        elif content_id == "vid002":
            return {
                "title": "Inception",
                "director": "Christopher Nolan",
                "year": 2010,
                "genres": ["Action", "Sci-Fi", "Thriller"],
                "runtime": 148,
                "tmdb_id": 27205
            }
        elif content_id == "vid003":
            return {
                "title": "Breaking Bad",
                "creator": "Vince Gilligan",
                "years": "2008-2013",
                "genres": ["Drama", "Crime", "Thriller"],
                "tmdb_id": 1396,
                "content_type": "tv"
            }
        return None
    
    async def check_availability(self, content_id):
        # Return mock availability data
        return {
            "services": [
                {"name": "Netflix", "url": "https://netflix.com/watch/"+content_id},
                {"name": "Amazon Prime", "url": "https://amazon.com/video/watch/"+content_id}
            ],
            "purchase_options": [
                {"name": "iTunes", "price": 3.99},
                {"name": "Google Play", "price": 3.99}
            ]
        }

# Mock file path resolver
def mock_file_path_resolver(content_id):
    # In a real system, this would look up the file path from a database
    for content in SAMPLE_CONTENTS:
        if content["content_id"] == content_id:
            return content["file_path"]
    return None

# Mock locations database
LOCATIONS_DB = {
    "vid001": {
        "title": "The Matrix",
        "locations": [
            {"name": "Sydney, Australia", "place_name": "Sydney, New South Wales, Australia", "coordinates": [151.2093, -33.8688]},
            {"name": "Fox Studios, Australia", "place_name": "Moore Park, Sydney, Australia"}
        ]
    },
    "vid002": {
        "title": "Inception",
        "locations": [
            {"name": "Paris, France", "coordinates": [2.3522, 48.8566]},
            {"name": "Tangier, Morocco", "coordinates": [-5.8129, 35.7595]},
            {"name": "Calgary, Canada", "coordinates": [-114.0719, 51.0447]}
        ]
    }
}

async def test_metadata_enrichment():
    # =========================================================================
    # 1. Setup authentication system
    # =========================================================================
    logger.info("1. Setting up authentication system...")
    
    auth_config = {
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
                "user_id": "admin1",
                "username": "admin_user",
                "role": "admin",
                "api_keys": ["admin1_api_key"]
            }
        ]
    }
    
    auth_manager = MetadataAuthManager(auth_config)
    
    # Create tokens for testing
    user_token = auth_manager.create_auth_token("user1")
    premium_token = auth_manager.create_auth_token("premium1")
    admin_token = auth_manager.create_auth_token("admin1")
    
    logger.info(f"Created test tokens: User: {user_token[:8]}..., Premium: {premium_token[:8]}..., Admin: {admin_token[:8]}...")
    
    # =========================================================================
    # 2. Setup optimized caching system
    # =========================================================================
    logger.info("2. Setting up optimized caching system...")
    
    cache_config = {
        "enabled": True,
        "memory_cache": {
            "enabled": True,
            "ttl": 3600,             # 1 hour in memory
            "max_size": 1000,        # Max 1000 entries
            "cleanup_interval": 300  # Clean every 5 minutes
        },
        "file_cache": {
            "enabled": True,
            "ttl": 86400,            # 24 hours on disk
            "directory": "/tmp/videntify_cache",
            "max_size_mb": 100       # Max 100MB
        },
        "source_ttls": {
            "file": 86400,           # File metadata rarely changes - 24 hours
            "local_db": 3600,        # Local database - 1 hour
            "tmdb": 604800,          # TMDB data - 1 week
            "youtube": 86400,        # YouTube data - 24 hours
            "custom": 43200          # Custom sources - 12 hours
        }
    }
    
    metadata_cache = MetadataCache(cache_config)
    
    # =========================================================================
    # 3. Configure enrichment system with custom enrichers
    # =========================================================================
    logger.info("3. Configuring metadata enrichment with custom enrichers...")
    
    # Configure all enrichers
    config = {
        "cache_enabled": True,
        "cache_ttl": 3600,
        "enrichers": {
            "file": {
                "enabled": True,
                "priority": EnrichmentPriority.LOW,
                "file_path_resolver": mock_file_path_resolver
            },
            "local_db": {
                "enabled": True,
                "priority": EnrichmentPriority.HIGH,
                "db_client": MockDatabaseClient()
            },
            "tmdb": {
                "enabled": True,
                "priority": EnrichmentPriority.MEDIUM,
                "api_key": "YOUR_TMDB_API_KEY"  # Replace with actual key for testing
            },
            "spotify": {
                "enabled": True,
                "priority": EnrichmentPriority.LOW,
                "client_id": "YOUR_SPOTIFY_CLIENT_ID",  # Replace for testing
                "client_secret": "YOUR_SPOTIFY_CLIENT_SECRET"  # Replace for testing
            },
            "wikipedia": {
                "enabled": True,
                "priority": EnrichmentPriority.MEDIUM
            },
            "locations": {
                "enabled": True,
                "priority": EnrichmentPriority.MEDIUM,
                "locations_db": LOCATIONS_DB,
                "mapbox_api_key": "YOUR_MAPBOX_API_KEY"  # Replace for testing
            },
            "content_analysis": {
                "enabled": True,
                "priority": EnrichmentPriority.HIGH,
                "themes_mapping": THEMES_MAPPING,
                "genres_to_themes": GENRES_TO_THEMES
            }
        }
    }
    
    # Initialize engine
    engine = MetadataEnrichmentEngine(config)
    
    # Add custom enrichers
    spotify_enricher = SpotifyEnricher(config["enrichers"]["spotify"])
    wikipedia_enricher = WikipediaEnricher(config["enrichers"]["wikipedia"])
    location_enricher = LocationEnricher(config["enrichers"]["locations"])
    content_analysis_enricher = ContentAnalysisEnricher(config["enrichers"]["content_analysis"])
    
    engine.add_custom_enricher(spotify_enricher)
    engine.add_custom_enricher(wikipedia_enricher)
    engine.add_custom_enricher(location_enricher)
    engine.add_custom_enricher(content_analysis_enricher)
    
    logger.info(f"Initialized enrichment engine with {len(engine.enrichers)} enrichers")
    
    # =========================================================================
    # 4. Test the full system with different user roles
    # =========================================================================
    logger.info("4. Testing full metadata enrichment system with different user roles...")
    
    # Function to test with a specific user
    async def test_with_user(user_role, auth_header):
        print(f"\n=== Testing with {user_role} role ===\n")
        
        # Authenticate the user
        user = auth_manager.authenticate(auth_header=auth_header)
        print(f"Authenticated as: {user.username} with role {user.role}")
        print(f"Scopes: {', '.join(s.value for s in user.scopes)}")
        
        total_time = 0
        results = {}
        
        # Process each sample content
        for content in SAMPLE_CONTENTS:
            content_id = content["content_id"]
            print(f"\nProcessing {content['title']} (ID: {content_id})")
            
            # Check cache first
            cache_key = f"{content_id}:{user.role}"
            cached_result = metadata_cache.get(content_id, str(user.role))
            
            if cached_result:
                print(f"  ✓ Retrieved from cache")
                results[content_id] = cached_result
                continue
            
            # Start timing
            start_time = time.time()
            
            # Create base metadata
            base_metadata = {
                "content_id": content_id,
                "title": content["title"],
                "content_type": content["type"]
            }
            
            # Enrich metadata
            try:
                enriched_metadata = await engine.enrich_metadata(content_id, base_metadata)
                
                # Filter metadata based on user permissions
                filtered_metadata = auth_manager.filter_metadata_fields(enriched_metadata, user)
                
                # Store in cache
                metadata_cache.set(content_id, filtered_metadata, str(user.role))
                
                # Add to results
                results[content_id] = filtered_metadata
                
                # Calculate time
                process_time = time.time() - start_time
                total_time += process_time
                
                # Print information
                field_count = len(filtered_metadata)
                fields_accessible = ", ".join(list(filtered_metadata.keys())[:5]) + ("..." if field_count > 5 else "")
                
                print(f"  ✓ Enriched with {field_count} fields in {process_time:.2f}s")
                print(f"  ✓ Fields: {fields_accessible}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        if results:
            print(f"\nCompleted processing {len(results)} items in {total_time:.2f}s total")
            print(f"Average time per item: {total_time/len(results):.2f}s")
        
        # Return results for UI
        return results
    
    # Test with different users
    guest_results = await test_with_user("Guest", None)  # No auth header
    user_results = await test_with_user("Regular User", f"Bearer {user_token}")
    premium_results = await test_with_user("Premium User", f"Bearer {premium_token}")
    admin_results = await test_with_user("Admin", f"Bearer {admin_token}")
    
    # =========================================================================
    # 5. Output UI-ready format for one example
    # =========================================================================
    logger.info("5. Preparing UI-ready format for demo display...")
    
    # Take the first premium user result as an example
    example_content_id = "vid001"  # The Matrix
    ui_data = premium_results.get(example_content_id)
    
    if ui_data:
        print("\n=== Sample UI-Ready Data for 'The Matrix' (Premium User View) ===\n")
        
        # Convert to JSON for use in UI
        ui_json = json.dumps(ui_data, indent=2)
        
        # Save to a file for UI testing
        ui_file_path = "/tmp/videntify_ui_sample.json"
        with open(ui_file_path, "w") as f:
            f.write(ui_json)
            
        print(f"Saved UI-ready data to {ui_file_path}")
        print("\nSample structure:")
        
        # Print key sections for demo
        if "title" in ui_data:
            print(f"Title: {ui_data['title']}")
        if "overview" in ui_data:
            print(f"Overview: {ui_data['overview'][:100]}..." if len(ui_data.get('overview', '')) > 100 else ui_data.get('overview', ''))
        if "genres" in ui_data:
            print(f"Genres: {', '.join(ui_data['genres'])}")
        if "themes" in ui_data:
            print(f"Themes: {', '.join(ui_data['themes'])}")
        if "filming_locations" in ui_data:
            locations = [loc.get('name', 'Unknown') for loc in ui_data['filming_locations']]
            print(f"Filming Locations: {', '.join(locations)}")
    
    # =========================================================================
    # 6. Cache performance statistics
    # =========================================================================
    logger.info("6. Cache performance statistics...")
    
    cache_stats = metadata_cache.get_stats()
    print("\n=== Cache Statistics ===\n")
    pprint(cache_stats)
    
    # Test cache hit performance
    print("\n=== Cache Performance Test ===\n")
    
    # Time cached vs non-cached access
    start_time = time.time()
    cached_admin_result = await test_with_user("Admin (Cached)", f"Bearer {admin_token}")
    cached_time = time.time() - start_time
    
    # Clear memory cache only
    metadata_cache.memory_cache = {}
    
    start_time = time.time()
    disk_cached_admin_result = await test_with_user("Admin (Disk Cache)", f"Bearer {admin_token}")
    disk_cache_time = time.time() - start_time
    
    print(f"\nMemory cache access time: {cached_time:.3f}s")
    print(f"Disk cache access time: {disk_cache_time:.3f}s")
    print(f"Speed improvement: {disk_cache_time/max(0.001, cached_time):.1f}x faster from memory cache")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_metadata_enrichment())
