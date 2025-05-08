"""Test script for the Metadata Enrichment System

This script demonstrates the functionality of the metadata enrichment system
by enriching sample video metadata from various sources.
"""

import asyncio
import json
import logging
import os
import sys
from pprint import pprint

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.metadata_enrichment import (
    MetadataEnrichmentEngine, 
    FileMetadataEnricher,
    LocalDatabaseEnricher,
    TMDBEnricher,
    YouTubeEnricher,
    MetadataSource, 
    EnrichmentPriority
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample movie IDs for testing
SAMPLE_CONTENTS = [
    {
        "content_id": "vid001",
        "title": "The Matrix",
        "type": "movie",
        "file_path": "/sample/path/matrix.mp4"
    },
    {
        "content_id": "vid002",
        "title": "Inception",
        "type": "movie",
        "file_path": "/sample/path/inception.mp4"
    },
    {
        "content_id": "vid003",
        "title": "Breaking Bad",
        "type": "tv",
        "file_path": "/sample/path/breaking_bad.mp4"
    }
]

# Mock database client for testing
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

# Mock YouTube ID resolver
def mock_youtube_id_resolver(content_id):
    # Map content IDs to YouTube IDs (these are made up for this example)
    youtube_map = {
        "vid001": "dQw4w9WgXcQ",  # Just using a well-known YouTube ID for testing
        "vid002": "8hP9D6kZseM",
        "vid003": "HhesaQXLuRY"
    }
    return youtube_map.get(content_id)

async def test_metadata_enrichment():
    # Configure enrichers
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
                "api_key": "YOUR_TMDB_API_KEY"  # Replace with actual API key for real testing
            },
            "youtube": {
                "enabled": True,
                "priority": EnrichmentPriority.LOW,
                "api_key": "YOUR_YOUTUBE_API_KEY",  # Replace with actual API key for real testing
                "youtube_id_resolver": mock_youtube_id_resolver
            }
        }
    }
    
    # Initialize the engine
    engine = MetadataEnrichmentEngine(config)
    
    # Add YouTube enricher manually (as it's not in the default list)
    youtube_enricher = YouTubeEnricher(config["enrichers"]["youtube"])
    engine.add_custom_enricher(youtube_enricher)
    
    logger.info("Starting metadata enrichment test...")
    
    # Test individual enrichment
    for content in SAMPLE_CONTENTS:
        content_id = content["content_id"]
        logger.info(f"Enriching metadata for {content_id} - {content['title']}")
        
        # Start with basic metadata
        base_metadata = {
            "title": content["title"],
            "content_type": content["type"]
        }
        
        # Enrich metadata
        enriched = await engine.enrich_metadata(content_id, base_metadata)
        
        # Print results
        print(f"\n=== Enriched Metadata for {content['title']} ===\n")
        pprint(enriched)
        print("\n")
    
    # Test batch enrichment
    logger.info("Testing batch enrichment...")
    content_ids = [content["content_id"] for content in SAMPLE_CONTENTS]
    batch_results = await engine.batch_enrich_metadata(content_ids)
    
    # Print batch results summary
    print("\n=== Batch Enrichment Results ===\n")
    for content_id, metadata in batch_results.items():
        print(f"{content_id}: {metadata.get('title')} - {len(metadata)} fields")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_metadata_enrichment())
