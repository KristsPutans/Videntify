"""Metadata Field Permission Definitions.

This module defines the permission structure for metadata fields,
allowing for granular access control based on content types and user roles.
"""

from enum import Enum
from typing import Dict, List, Set, Any

from src.core.metadata_auth import MetadataScope


class ContentType(str, Enum):
    """Content types for permission mapping."""
    VIDEO = "video"
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    EPISODE = "episode"
    MUSIC_VIDEO = "music_video"
    SHORT = "short"
    DOCUMENTARY = "documentary"
    COMMERCIAL = "commercial"
    OTHER = "other"
    

class FieldCategory(str, Enum):
    """Categories for metadata fields."""
    BASIC = "basic"            # Basic identification fields
    MEDIA = "media"            # Media-related fields (images, posters)
    CONTENT = "content"        # Content descriptions, overviews
    PEOPLE = "people"          # Cast, crew, directors
    TECHNICAL = "technical"    # Technical details, codecs, duration
    COMMERCIAL = "commercial"  # Commercial info (revenue, availability)
    EXTERNAL = "external"      # External service IDs and links
    ADMIN = "admin"            # Administrative fields


# Mapping of field categories to scopes for permission control
CATEGORY_TO_SCOPE = {
    FieldCategory.BASIC: MetadataScope.PUBLIC,
    FieldCategory.MEDIA: MetadataScope.PUBLIC,
    FieldCategory.CONTENT: MetadataScope.BASIC_INFO,
    FieldCategory.PEOPLE: MetadataScope.BASIC_INFO,
    FieldCategory.TECHNICAL: MetadataScope.BASIC_INFO,
    FieldCategory.COMMERCIAL: MetadataScope.SENSITIVE,
    FieldCategory.EXTERNAL: MetadataScope.EXTERNAL_API,
    FieldCategory.ADMIN: MetadataScope.ADMIN
}


# Define field categories for better organization
FIELD_CATEGORIES = {
    FieldCategory.BASIC: [
        "content_id", "title", "type", "release_date", "genres", "runtime", 
        "vote_average", "vote_count", "language"
    ],
    FieldCategory.MEDIA: [
        "poster_url", "backdrop_url", "thumbnail_url", "thumbnail_medium_url", 
        "thumbnail_small_url", "logo_url", "banner_url"
    ],
    FieldCategory.CONTENT: [
        "overview", "tagline", "wikipedia_extract", "themes", "mood", 
        "time_period", "keywords", "plot_summary", "description"
    ],
    FieldCategory.PEOPLE: [
        "cast", "directors", "producers", "writers", "crew", "actors", 
        "creator", "host", "guest"
    ],
    FieldCategory.TECHNICAL: [
        "duration", "width", "height", "codec", "bitrate", "frame_rate", 
        "audio_codec", "audio_channels", "audio_sample_rate", "file_size", 
        "aspect_ratio", "resolution", "timestamp", "formatted_timestamp"
    ],
    FieldCategory.COMMERCIAL: [
        "revenue", "budget", "availability", "streaming_services", "purchase_options", 
        "theatrical_release", "home_release", "box_office", "production_companies"
    ],
    FieldCategory.EXTERNAL: [
        "tmdb_id", "imdb_id", "youtube_id", "spotify_id", "video_url", 
        "soundtrack", "soundtrack_url", "soundtrack_artists", "wikipedia_url", 
        "filming_locations", "locations_map_url", "youtube_statistics"
    ],
    FieldCategory.ADMIN: [
        "enriched_metadata", "_sources", "content_hash", "file_path", 
        "file_created", "file_modified", "indexing_status", "enrichment_status", 
        "sensitivity_flags", "internal_notes", "access_log"
    ]
}


# Content-specific field mappings
# This defines fields that are only relevant to certain content types
CONTENT_TYPE_FIELDS = {
    ContentType.MOVIE: {
        "add": [
            "director", "box_office", "budget", "revenue", "production_companies",
            "theatrical_release", "home_release"
        ],
        "remove": ["episodes", "seasons", "network"]
    },
    ContentType.TV_SHOW: {
        "add": ["creator", "episodes", "seasons", "network", "first_air_date", "last_air_date"],
        "remove": ["director", "box_office"]
    },
    ContentType.EPISODE: {
        "add": ["show_title", "season_number", "episode_number", "air_date", "guest_stars"],
        "remove": ["box_office", "revenue"]
    },
    ContentType.MUSIC_VIDEO: {
        "add": ["artist", "album", "record_label", "release_year", "music_genre"],
        "remove": ["box_office", "revenue", "director"]
    },
    ContentType.DOCUMENTARY: {
        "add": ["subjects", "narrators", "historical_period", "rating"],
        "remove": ["box_office"]
    }
}


# TTL (Time-To-Live) values for different content types in seconds
CONTENT_TYPE_TTL = {
    ContentType.VIDEO: 3600,         # 1 hour
    ContentType.MOVIE: 86400 * 7,    # 7 days (movies change rarely)
    ContentType.TV_SHOW: 86400 * 2,  # 2 days (may be updated with new episodes)
    ContentType.EPISODE: 86400 * 3,  # 3 days
    ContentType.MUSIC_VIDEO: 86400 * 14,  # 14 days (change infrequently)
    ContentType.SHORT: 3600 * 12,    # 12 hours
    ContentType.DOCUMENTARY: 86400 * 14,  # 14 days (rarely change)
    ContentType.COMMERCIAL: 3600 * 4,  # 4 hours (may be updated frequently)
    ContentType.OTHER: 86400         # 1 day default
}


# Define what fields require premium permission
PREMIUM_ONLY_FIELDS = [
    "soundtrack", "soundtrack_url", "filming_locations", "locations_map_url",
    "availability", "streaming_services", "purchase_options", "youtube_statistics",
    "historical_period", "sensitive_content_flags"
]


# Source-specific TTL values in seconds
SOURCE_TTL = {
    "file": 86400 * 7,          # File metadata rarely changes - 7 days
    "local_db": 3600 * 12,      # Local database - 12 hours
    "tmdb": 86400 * 7,          # TMDB data - 7 days
    "youtube": 86400,           # YouTube data - 1 day
    "spotify": 86400 * 3,       # Spotify data - 3 days
    "wikipedia": 86400 * 5,     # Wikipedia data - 5 days
    "location": 86400 * 10,     # Location data - 10 days (rarely changes)
    "content_analysis": 86400 * 30  # Content analysis - 30 days (doesn't change)
}


def get_field_scope(field_name: str) -> MetadataScope:
    """Get the required scope for a given field.
    
    Args:
        field_name: The metadata field name
        
    Returns:
        The MetadataScope required to access this field
    """
    for category, fields in FIELD_CATEGORIES.items():
        if field_name in fields:
            return CATEGORY_TO_SCOPE[category]
            
    # Premium fields need special handling
    if field_name in PREMIUM_ONLY_FIELDS:
        return MetadataScope.SENSITIVE
        
    # Default to admin scope for unknown fields
    return MetadataScope.ADMIN


def get_content_type_ttl(content_type: str) -> int:
    """Get the TTL for a content type.
    
    Args:
        content_type: The type of content
        
    Returns:
        TTL in seconds
    """
    try:
        return CONTENT_TYPE_TTL[ContentType(content_type)]
    except (KeyError, ValueError):
        return CONTENT_TYPE_TTL[ContentType.OTHER]  # Default


def get_source_ttl(source: str) -> int:
    """Get the TTL for a metadata source.
    
    Args:
        source: The metadata source name
        
    Returns:
        TTL in seconds
    """
    return SOURCE_TTL.get(source, 3600)  # Default to 1 hour
