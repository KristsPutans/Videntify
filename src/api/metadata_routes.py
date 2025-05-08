"""API routes for metadata enrichment with authentication.

This module provides FastAPI routes that handle metadata enrichment requests,
applying proper authentication, optimized caching, and access controls.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional, List
import logging

from src.core.metadata_enrichment import MetadataEnrichmentEngine
from src.core.metadata_auth import MetadataAuthManager, UserInfo
from src.core.metadata_cache import MetadataCache
from src.core.config import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/metadata", tags=["metadata"])

# Initialize OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Configuration for metadata services
config = ConfigManager().get_config("metadata")

# Initialize core services
auth_manager = MetadataAuthManager(config.get("auth", {}))
metadata_cache = MetadataCache(config.get("cache", {}))
enrichment_engine = MetadataEnrichmentEngine(config.get("enrichment", {}))

# Load custom enrichers if configured
if config.get("load_custom_enrichers", True):
    from src.core.custom_enrichers import (
        SpotifyEnricher,
        WikipediaEnricher,
        LocationEnricher,
        ContentAnalysisEnricher
    )
    
    # Initialize and add custom enrichers
    enrichers_config = config.get("enrichers", {})
    
    if enrichers_config.get("spotify", {}).get("enabled", False):
        enrichment_engine.add_custom_enricher(SpotifyEnricher(enrichers_config.get("spotify", {})))
        
    if enrichers_config.get("wikipedia", {}).get("enabled", False):
        enrichment_engine.add_custom_enricher(WikipediaEnricher(enrichers_config.get("wikipedia", {})))
        
    if enrichers_config.get("locations", {}).get("enabled", False):
        enrichment_engine.add_custom_enricher(LocationEnricher(enrichers_config.get("locations", {})))
        
    if enrichers_config.get("content_analysis", {}).get("enabled", False):
        enrichment_engine.add_custom_enricher(ContentAnalysisEnricher(enrichers_config.get("content_analysis", {})))


# Authentication dependency
async def get_current_user(
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> UserInfo:
    """Authenticate the user from request headers.
    
    Args:
        authorization: OAuth2 Bearer token header
        api_key: API key header
        
    Returns:
        UserInfo object with authenticated user details
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_manager.authenticate(auth_header=authorization, api_key_header=api_key)
    
    if not user:
        # Default to guest user if no authentication provided
        user = auth_manager.get_guest_user()
    
    return user


@router.get("/")
async def get_metadata_status():
    """Get metadata service status."""
    return {
        "status": "active",
        "enrichers": len(enrichment_engine.enrichers),
        "custom_enrichers": len(enrichment_engine.custom_enrichers),
        "cache_enabled": metadata_cache.enabled
    }


@router.get("/{content_id}")
async def get_enriched_metadata(
    content_id: str,
    user: UserInfo = Depends(get_current_user),
    force_refresh: bool = Query(False, description="Force refresh cached metadata")
) -> Dict[str, Any]:
    """Get enriched metadata for a content item.
    
    Args:
        content_id: ID of the content to retrieve metadata for
        user: Authenticated user information
        force_refresh: Whether to bypass cache and force a refresh
        
    Returns:
        Dictionary containing enriched metadata
        
    Raises:
        HTTPException: If content ID is invalid or server error occurs
    """
    logger.info(f"Metadata request for content_id={content_id} by user={user.username} (role={user.role})")
    
    # Check if we have a cached version for this user role
    if not force_refresh:
        cache_key = f"{content_id}:{user.role}"
        cached_data = metadata_cache.get(content_id, str(user.role))
        
        if cached_data:
            logger.info(f"Returning cached metadata for {content_id}")
            return cached_data
    
    try:
        # Get base metadata (could be from database or minimal info)
        # In a real system, you'd fetch this from a database
        base_metadata = {"content_id": content_id}
        
        # Enrich metadata
        enriched_metadata = await enrichment_engine.enrich_metadata(content_id, base_metadata)
        
        # Filter metadata based on user permissions
        filtered_metadata = auth_manager.filter_metadata_fields(enriched_metadata, user)
        
        # Store in cache with TTL based on content type
        content_type = enriched_metadata.get("content_type", "video")
        ttl = config.get("cache", {}).get("content_ttls", {}).get(content_type, 3600)  # Default 1 hour
        
        metadata_cache.set(content_id, filtered_metadata, str(user.role), ttl=ttl)
        
        return filtered_metadata
        
    except Exception as e:
        logger.error(f"Error enriching metadata for {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enrich metadata: {str(e)}")


@router.get("/{content_id}/sources")
async def get_metadata_sources(
    content_id: str,
    user: UserInfo = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get available metadata sources for a content item.
    
    This endpoint returns information about which enrichers are available
    for this content item based on the user's permissions.
    
    Args:
        content_id: ID of the content to check sources for
        user: Authenticated user information
        
    Returns:
        List of available metadata sources
    """
    # Only premium and above users can access this endpoint
    if user.role not in ["premium", "staff", "admin"]:
        raise HTTPException(status_code=403, detail="Premium subscription required")
    
    # Get all available enrichers
    sources = enrichment_engine.get_available_sources(content_id)
    
    # Filter based on user permissions
    filtered_sources = auth_manager.filter_metadata_sources(sources, user)
    
    return filtered_sources


@router.post("/{content_id}/refresh")
async def refresh_metadata(
    content_id: str,
    user: UserInfo = Depends(get_current_user),
    sources: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Force refresh metadata for a content item.
    
    Args:
        content_id: ID of the content to refresh metadata for
        user: Authenticated user information
        sources: Optional list of specific sources to refresh (else all)
        
    Returns:
        Refreshed metadata dictionary
        
    Raises:
        HTTPException: If refresh fails or user lacks permissions
    """
    # Only staff and admin users can force a refresh
    if user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Staff permissions required")
    
    try:
        # Clear cache for this content ID
        metadata_cache.delete(content_id)
        
        # Get base metadata
        base_metadata = {"content_id": content_id}
        
        # Refresh metadata from specific or all sources
        refreshed_metadata = await enrichment_engine.enrich_metadata(
            content_id, 
            base_metadata,
            sources=sources,
            force_refresh=True
        )
        
        # Filter based on user permissions
        filtered_metadata = auth_manager.filter_metadata_fields(refreshed_metadata, user)
        
        # Store refreshed data in cache
        metadata_cache.set(content_id, filtered_metadata, str(user.role))
        
        return filtered_metadata
        
    except Exception as e:
        logger.error(f"Error refreshing metadata for {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh metadata: {str(e)}")        
