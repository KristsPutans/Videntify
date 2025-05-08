"""Metadata Enrichment System

This module provides functionality to enrich video metadata with additional information
from various sources such as content databases, external APIs, and local metadata stores.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MetadataSource(str, Enum):
    """Enumeration of metadata sources."""
    LOCAL_DB = "local_db"         # Local database
    CONTENT_API = "content_api"   # Content provider API
    IMDB = "imdb"                 # IMDB data
    TMDB = "tmdb"                 # The Movie Database
    YOUTUBE = "youtube"           # YouTube metadata
    USER_TAGS = "user_tags"       # User-provided tags/metadata
    FILE_METADATA = "file"        # Metadata extracted from the file itself
    CUSTOM = "custom"             # Custom source


class EnrichmentPriority(int, Enum):
    """Priority levels for metadata enrichment."""
    LOW = 0        # Nice to have, but not essential
    MEDIUM = 1     # Somewhat important
    HIGH = 2       # High priority
    CRITICAL = 3   # Critical information that must be included


class MetadataField(BaseModel):
    """Model for a metadata field."""
    name: str
    value: Any
    source: MetadataSource
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: EnrichmentPriority = EnrichmentPriority.MEDIUM
    
    class Config:
        arbitrary_types_allowed = True


class EnhancedMetadata(BaseModel):
    """Model for enhanced metadata."""
    content_id: str
    title: Optional[str] = None
    fields: Dict[str, MetadataField] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_field(self, name: str, value: Any, source: MetadataSource, 
                 confidence: float = 1.0, priority: EnrichmentPriority = EnrichmentPriority.MEDIUM):
        """Add a field to the metadata.
        
        Args:
            name: Field name
            value: Field value
            source: Source of the metadata
            confidence: Confidence score (0-1)
            priority: Priority level
        """
        self.fields[name] = MetadataField(
            name=name,
            value=value,
            source=source,
            confidence=confidence,
            priority=priority
        )
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a simple dictionary."""
        result = {
            "content_id": self.content_id,
            "title": self.title,
            "last_updated": self.last_updated.isoformat()
        }
        
        # Add all fields, using field names as keys
        for name, field in self.fields.items():
            result[name] = field.value
            
        # Add metadata about the sources
        result["_sources"] = {}
        for name, field in self.fields.items():
            result["_sources"][name] = {
                "source": field.source,
                "confidence": field.confidence,
                "timestamp": field.timestamp.isoformat()
            }
            
        return result


class BaseMetadataEnricher:
    """Base class for metadata enrichment providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the enricher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.source = MetadataSource.CUSTOM  # Override in subclasses
        self.enabled = config.get("enabled", True)
        self.priority = EnrichmentPriority(config.get("priority", EnrichmentPriority.MEDIUM))
        
    async def enrich(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Enrich the provided metadata.
        
        Args:
            content_id: Content ID to enrich metadata for
            metadata: Existing metadata to enhance
            
        Returns:
            Enhanced metadata
        """
        if not self.enabled:
            return metadata
            
        try:
            return await self._enrich_implementation(content_id, metadata)
        except Exception as e:
            logger.error(f"Error enriching metadata with {self.__class__.__name__}: {e}")
            return metadata
    
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Implement the actual enrichment logic in subclasses.
        
        Args:
            content_id: Content ID to enrich metadata for
            metadata: Existing metadata to enhance
            
        Returns:
            Enhanced metadata
        """
        raise NotImplementedError("Subclasses must implement this method")


class FileMetadataEnricher(BaseMetadataEnricher):
    """Enricher that extracts metadata from the video file itself."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.FILE_METADATA
        self.file_path_resolver = config.get("file_path_resolver")
        
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Extract metadata from the file."""
        if not self.file_path_resolver:
            return metadata
            
        try:
            # Resolve file path from content ID
            file_path = self.file_path_resolver(content_id)
            if not file_path or not os.path.exists(file_path):
                return metadata
                
            # Extract file metadata
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime)
            created_time = datetime.fromtimestamp(file_stats.st_ctime)
            
            # Add file metadata
            metadata.add_field("file_size", file_size, self.source)
            metadata.add_field("file_modified", modified_time.isoformat(), self.source)
            metadata.add_field("file_created", created_time.isoformat(), self.source)
            metadata.add_field("file_path", file_path, self.source)
            
            # Extract media metadata using a media library if available
            try:
                import ffmpeg
                probe_result = ffmpeg.probe(file_path)
                if probe_result:
                    # Extract video streams info
                    video_streams = [s for s in probe_result.get('streams', []) if s.get('codec_type') == 'video']
                    if video_streams:
                        video_info = video_streams[0]
                        metadata.add_field("width", video_info.get('width'), self.source)
                        metadata.add_field("height", video_info.get('height'), self.source)
                        metadata.add_field("codec", video_info.get('codec_name'), self.source)
                        metadata.add_field("duration", float(probe_result.get('format', {}).get('duration', 0)), self.source)
                        metadata.add_field("bitrate", int(probe_result.get('format', {}).get('bit_rate', 0)), self.source)
                    
                    # Extract audio streams info
                    audio_streams = [s for s in probe_result.get('streams', []) if s.get('codec_type') == 'audio']
                    if audio_streams:
                        audio_info = audio_streams[0]
                        metadata.add_field("audio_codec", audio_info.get('codec_name'), self.source)
                        metadata.add_field("audio_channels", audio_info.get('channels'), self.source)
                        metadata.add_field("audio_sample_rate", audio_info.get('sample_rate'), self.source)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not extract detailed media metadata: {e}")
                
        except Exception as e:
            logger.error(f"Error extracting file metadata: {e}")
            
        return metadata


class LocalDatabaseEnricher(BaseMetadataEnricher):
    """Enricher that fetches metadata from a local database."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.LOCAL_DB
        self.db_client = config.get("db_client")
        
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Fetch metadata from the local database."""
        if not self.db_client or not hasattr(self.db_client, 'get_content_metadata'):
            return metadata
            
        try:
            # Fetch metadata from database
            db_metadata = await self.db_client.get_content_metadata(content_id)
            if not db_metadata:
                return metadata
                
            # Add all fields from the database
            for key, value in db_metadata.items():
                if key not in ["content_id", "_id"]:
                    metadata.add_field(key, value, self.source)
                    
            # Set title if available and not already set
            if "title" in db_metadata and not metadata.title:
                metadata.title = db_metadata["title"]
                
        except Exception as e:
            logger.error(f"Error fetching metadata from local database: {e}")
            
        return metadata


class TMDBEnricher(BaseMetadataEnricher):
    """Enricher that fetches metadata from The Movie Database (TMDB) API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.TMDB
        self.api_key = config.get("api_key")
        self.base_url = "https://api.themoviedb.org/3"
        self.search_url = f"{self.base_url}/search/multi"
        self.movie_url = f"{self.base_url}/movie"
        self.tv_url = f"{self.base_url}/tv"
        
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Fetch metadata from TMDB API."""
        if not self.api_key:
            return metadata
            
        try:
            # First check if we have a TMDB ID in the existing metadata
            tmdb_id = None
            content_type = None
            
            if "tmdb_id" in metadata.fields:
                tmdb_id = metadata.fields["tmdb_id"].value
                if "content_type" in metadata.fields:
                    content_type = metadata.fields["content_type"].value
            
            # If we don't have a TMDB ID but have a title, search for it
            if not tmdb_id and metadata.title:
                tmdb_info = await self._search_tmdb(metadata.title)
                if tmdb_info:
                    tmdb_id = tmdb_info.get("id")
                    content_type = tmdb_info.get("media_type")
                    
            # If we have an ID, fetch full metadata
            if tmdb_id and content_type:
                tmdb_data = await self._fetch_tmdb_details(tmdb_id, content_type)
                if tmdb_data:
                    self._apply_tmdb_data(metadata, tmdb_data, content_type)
                
        except Exception as e:
            logger.error(f"Error fetching metadata from TMDB: {e}")
            
        return metadata
    
    async def _search_tmdb(self, query: str) -> Optional[Dict[str, Any]]:
        """Search TMDB for content."""
        params = {
            "api_key": self.api_key,
            "query": query,
            "language": "en-US",
            "page": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    if results:
                        # Return the first result
                        return results[0]
                        
        return None
    
    async def _fetch_tmdb_details(self, tmdb_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed info from TMDB."""
        if media_type not in ["movie", "tv"]:
            return None
            
        url = f"{self.movie_url}/{tmdb_id}" if media_type == "movie" else f"{self.tv_url}/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "append_to_response": "credits,keywords"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                    
        return None
    
    def _apply_tmdb_data(self, metadata: EnhancedMetadata, tmdb_data: Dict[str, Any], media_type: str):
        """Apply TMDB data to metadata."""
        # Add basic info
        metadata.add_field("tmdb_id", tmdb_data.get("id"), self.source)
        metadata.add_field("title", tmdb_data.get("title" if media_type == "movie" else "name"), self.source)
        metadata.add_field("original_title", tmdb_data.get("original_title" if media_type == "movie" else "original_name"), self.source)
        metadata.add_field("overview", tmdb_data.get("overview"), self.source)
        metadata.add_field("popularity", tmdb_data.get("popularity"), self.source)
        metadata.add_field("vote_average", tmdb_data.get("vote_average"), self.source)
        metadata.add_field("vote_count", tmdb_data.get("vote_count"), self.source)
        metadata.add_field("content_type", media_type, self.source)
        
        # Add release info
        if media_type == "movie":
            metadata.add_field("release_date", tmdb_data.get("release_date"), self.source)
            metadata.add_field("runtime", tmdb_data.get("runtime"), self.source)
        else:  # TV
            metadata.add_field("first_air_date", tmdb_data.get("first_air_date"), self.source)
            metadata.add_field("last_air_date", tmdb_data.get("last_air_date"), self.source)
            metadata.add_field("number_of_seasons", tmdb_data.get("number_of_seasons"), self.source)
            metadata.add_field("number_of_episodes", tmdb_data.get("number_of_episodes"), self.source)
            metadata.add_field("episode_run_time", tmdb_data.get("episode_run_time"), self.source)
            
        # Add genre information
        if "genres" in tmdb_data:
            genres = [genre.get("name") for genre in tmdb_data.get("genres", [])]
            metadata.add_field("genres", genres, self.source)
            
        # Add cast and crew information
        if "credits" in tmdb_data:
            cast = [
                {"name": person.get("name"), "character": person.get("character"), "order": person.get("order")}
                for person in tmdb_data.get("credits", {}).get("cast", [])[:5]  # Limit to top 5 cast members
            ]
            metadata.add_field("cast", cast, self.source)
            
            directors = [
                person.get("name") for person in tmdb_data.get("credits", {}).get("crew", [])
                if person.get("job") == "Director"
            ]
            metadata.add_field("directors", directors, self.source)
            
        # Add keywords/tags
        if "keywords" in tmdb_data:
            keywords = [keyword.get("name") for keyword in tmdb_data.get("keywords", {}).get("keywords", [])]
            metadata.add_field("keywords", keywords, self.source)
            
        # Add poster and backdrop paths
        if tmdb_data.get("poster_path"):
            metadata.add_field("poster_url", f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path')}", self.source)
        if tmdb_data.get("backdrop_path"):
            metadata.add_field("backdrop_url", f"https://image.tmdb.org/t/p/original{tmdb_data.get('backdrop_path')}", self.source)


class MetadataEnrichmentEngine:
    """Engine for enriching content metadata from multiple sources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the metadata enrichment engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.enrichers = []
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_ttl = config.get("cache_ttl", 3600)  # Cache TTL in seconds
        self.cache = {}
        self.cache_timestamps = {}
        
        # Initialize enrichers
        self._setup_enrichers()
        
        # Sort enrichers by priority
        self.enrichers.sort(key=lambda e: e.priority, reverse=True)
        
        logger.info(f"Initialized MetadataEnrichmentEngine with {len(self.enrichers)} enrichers")
        
    def _setup_enrichers(self):
        """Set up the available metadata enrichers."""
        enricher_configs = self.config.get("enrichers", {})
        
        # Set up file metadata enricher
        if "file" in enricher_configs and enricher_configs["file"].get("enabled", True):
            self.enrichers.append(FileMetadataEnricher(enricher_configs["file"]))
            
        # Set up local database enricher
        if "local_db" in enricher_configs and enricher_configs["local_db"].get("enabled", True):
            self.enrichers.append(LocalDatabaseEnricher(enricher_configs["local_db"]))
            
        # Set up TMDB enricher
        if "tmdb" in enricher_configs and enricher_configs["tmdb"].get("enabled", True):
            self.enrichers.append(TMDBEnricher(enricher_configs["tmdb"]))
            
        # Add custom enrichers from configuration
        for name, enricher_class in self.config.get("custom_enrichers", {}).items():
            if name in enricher_configs and enricher_configs[name].get("enabled", True):
                self.enrichers.append(enricher_class(enricher_configs[name]))
    
    def _clean_cache(self):
        """Clean expired cache entries."""
        if not self.cache_enabled:
            return
            
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
    
    async def enrich_metadata(self, content_id: str, base_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enrich metadata for a content item from all available sources.
        
        Args:
            content_id: Content ID to enrich
            base_metadata: Optional base metadata to start with
            
        Returns:
            Enriched metadata as a dictionary
        """
        # Check cache first
        if self.cache_enabled:
            cache_key = content_id
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        # Start with provided base metadata or create new metadata object
        metadata = EnhancedMetadata(content_id=content_id)
        if base_metadata:
            metadata.title = base_metadata.get("title")
            for key, value in base_metadata.items():
                if key not in ["content_id", "title"]:
                    metadata.add_field(key, value, MetadataSource.CUSTOM)
        
        # Apply each enricher in sequence
        for enricher in self.enrichers:
            metadata = await enricher.enrich(content_id, metadata)
        
        # Convert to dictionary
        result = metadata.to_dict()
        
        # Cache the result
        if self.cache_enabled:
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = time.time()
            self._clean_cache()
        
        return result
    
    async def batch_enrich_metadata(self, content_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Enrich metadata for multiple content items in batch.
        
        Args:
            content_ids: List of content IDs to enrich
            
        Returns:
            Dictionary mapping content IDs to enriched metadata
        """
        results = {}
        
        # Process in parallel using gather
        tasks = [self.enrich_metadata(content_id) for content_id in content_ids]
        enriched_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to content IDs
        for i, content_id in enumerate(content_ids):
            if isinstance(enriched_results[i], Exception):
                logger.error(f"Error enriching metadata for {content_id}: {enriched_results[i]}")
                results[content_id] = {"content_id": content_id, "error": str(enriched_results[i])}
            else:
                results[content_id] = enriched_results[i]
        
        return results
    
    def add_custom_enricher(self, enricher: BaseMetadataEnricher):
        """Add a custom enricher to the engine.
        
        Args:
            enricher: Enricher to add
        """
        self.enrichers.append(enricher)
        # Re-sort by priority
        self.enrichers.sort(key=lambda e: e.priority, reverse=True)
        
    def clear_cache(self):
        """Clear the metadata cache."""
        self.cache = {}
        self.cache_timestamps = {}


# Add some additional useful enrichers

class YouTubeEnricher(BaseMetadataEnricher):
    """Enricher that fetches metadata from YouTube API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.YOUTUBE
        self.api_key = config.get("api_key")
        self.youtube_id_resolver = config.get("youtube_id_resolver")
        
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Fetch metadata from YouTube API."""
        if not self.api_key:
            return metadata
            
        try:
            # First try to get YouTube ID
            youtube_id = None
            
            # Check if we already have a YouTube ID in metadata
            if "youtube_id" in metadata.fields:
                youtube_id = metadata.fields["youtube_id"].value
                
            # If not, try to resolve from content ID
            if not youtube_id and self.youtube_id_resolver:
                youtube_id = self.youtube_id_resolver(content_id)
                
            if not youtube_id:
                return metadata
                
            # Fetch YouTube metadata
            youtube_data = await self._fetch_youtube_data(youtube_id)
            if youtube_data:
                self._apply_youtube_data(metadata, youtube_data)
                
        except Exception as e:
            logger.error(f"Error fetching metadata from YouTube: {e}")
            
        return metadata
    
    async def _fetch_youtube_data(self, youtube_id: str) -> Optional[Dict[str, Any]]:
        """Fetch data from YouTube API."""
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": youtube_id,
            "key": self.api_key,
            "part": "snippet,contentDetails,statistics"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    if items:
                        return items[0]
                        
        return None
    
    def _apply_youtube_data(self, metadata: EnhancedMetadata, youtube_data: Dict[str, Any]):
        """Apply YouTube data to metadata."""
        youtube_id = youtube_data.get("id")
        metadata.add_field("youtube_id", youtube_id, self.source)
        metadata.add_field("video_url", f"https://www.youtube.com/watch?v={youtube_id}", self.source)
        
        # Add snippet information
        snippet = youtube_data.get("snippet", {})
        metadata.add_field("title", snippet.get("title"), self.source)
        metadata.add_field("description", snippet.get("description"), self.source)
        metadata.add_field("published_at", snippet.get("publishedAt"), self.source)
        metadata.add_field("channel_title", snippet.get("channelTitle"), self.source)
        metadata.add_field("channel_id", snippet.get("channelId"), self.source)
        metadata.add_field("tags", snippet.get("tags", []), self.source)
        metadata.add_field("category_id", snippet.get("categoryId"), self.source)
        
        # Add thumbnails
        if "thumbnails" in snippet:
            thumbnails = snippet["thumbnails"]
            for size, thumb_data in thumbnails.items():
                metadata.add_field(f"thumbnail_{size}_url", thumb_data.get("url"), self.source)
            
        # Add content details
        content_details = youtube_data.get("contentDetails", {})
        metadata.add_field("duration", content_details.get("duration"), self.source)
        metadata.add_field("definition", content_details.get("definition"), self.source)
        
        # Add statistics
        statistics = youtube_data.get("statistics", {})
        metadata.add_field("view_count", statistics.get("viewCount"), self.source)
        metadata.add_field("like_count", statistics.get("likeCount"), self.source)
        metadata.add_field("comment_count", statistics.get("commentCount"), self.source)
