"""Custom Metadata Enrichers

This module provides specialized metadata enrichers for unique data sources.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

import aiohttp
from pydantic import BaseModel

from src.core.metadata_enrichment import (
    BaseMetadataEnricher, 
    EnhancedMetadata, 
    MetadataSource, 
    EnrichmentPriority
)

logger = logging.getLogger(__name__)


class SpotifyEnricher(BaseMetadataEnricher):
    """Enricher that fetches soundtrack and music information from Spotify API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.CUSTOM
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.token = None
        self.token_expiry = None
        
    async def _get_token(self):
        """Get an access token from Spotify API."""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        if not self.client_id or not self.client_secret:
            logger.error("Spotify client ID or secret not configured")
            return None
            
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode("utf-8")
            auth_base64 = "Basic " + auth_bytes.encode("base64").decode("utf-8").strip()
            
            url = "https://accounts.spotify.com/api/token"
            headers = {
                "Authorization": auth_base64,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"grant_type": "client_credentials"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get("access_token")
                        expires_in = result.get("expires_in", 3600)
                        self.token_expiry = datetime.now() + datetime.timedelta(seconds=expires_in - 60)  # Buffer of 60 seconds
                        return self.token
        except Exception as e:
            logger.error(f"Error getting Spotify token: {e}")
            
        return None
    
    async def _search_soundtrack(self, title: str) -> Optional[Dict[str, Any]]:
        """Search for a soundtrack on Spotify."""
        token = await self._get_token()
        if not token:
            return None
            
        try:
            # Clean up the title for search
            search_query = f"{title} soundtrack"
            
            url = "https://api.spotify.com/v1/search"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "q": search_query,
                "type": "album,playlist",
                "limit": 5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check albums first
                        albums = result.get("albums", {}).get("items", [])
                        if albums:
                            for album in albums:
                                # Check if it looks like a soundtrack
                                if "soundtrack" in album.get("name", "").lower():
                                    return album
                            
                            # If no explicit soundtrack found, return the first album
                            return albums[0]
                        
                        # Check playlists if no albums found
                        playlists = result.get("playlists", {}).get("items", [])
                        if playlists:
                            for playlist in playlists:
                                if "soundtrack" in playlist.get("name", "").lower():
                                    return playlist
                            
                            # Return the first playlist if no explicit soundtrack found
                            return playlists[0]
        except Exception as e:
            logger.error(f"Error searching Spotify: {e}")
            
        return None
    
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Fetch soundtrack information from Spotify."""
        if not metadata.title:
            return metadata
            
        try:
            soundtrack = await self._search_soundtrack(metadata.title)
            if soundtrack:
                # Determine if it's an album or playlist
                item_type = soundtrack.get("type")
                
                if item_type == "album":
                    metadata.add_field("soundtrack_type", "album", self.source)
                    metadata.add_field("soundtrack_name", soundtrack.get("name"), self.source)
                    metadata.add_field("soundtrack_url", soundtrack.get("external_urls", {}).get("spotify"), self.source)
                    metadata.add_field("soundtrack_image", soundtrack.get("images", [{}])[0].get("url") if soundtrack.get("images") else None, self.source)
                    metadata.add_field("soundtrack_artists", [artist.get("name") for artist in soundtrack.get("artists", [])], self.source)
                    metadata.add_field("soundtrack_release_date", soundtrack.get("release_date"), self.source)
                    
                elif item_type == "playlist":
                    metadata.add_field("soundtrack_type", "playlist", self.source)
                    metadata.add_field("soundtrack_name", soundtrack.get("name"), self.source)
                    metadata.add_field("soundtrack_url", soundtrack.get("external_urls", {}).get("spotify"), self.source)
                    metadata.add_field("soundtrack_image", soundtrack.get("images", [{}])[0].get("url") if soundtrack.get("images") else None, self.source)
                    metadata.add_field("soundtrack_track_count", soundtrack.get("tracks", {}).get("total"), self.source)
                    
        except Exception as e:
            logger.error(f"Error enriching with Spotify data: {e}")
            
        return metadata


class WikipediaEnricher(BaseMetadataEnricher):
    """Enricher that fetches additional information from Wikipedia."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.CUSTOM
        self.api_url = "https://en.wikipedia.org/w/api.php"
        
    async def _search_wikipedia(self, query: str) -> Optional[str]:
        """Search Wikipedia for a page title."""
        try:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_results = data.get("query", {}).get("search", [])
                        if search_results:
                            return search_results[0].get("title")
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            
        return None
    
    async def _get_wikipedia_extract(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a Wikipedia page extract."""
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info|pageimages",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "pithumbsize": 500,
                "titles": title
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = data.get("query", {}).get("pages", {})
                        if pages:
                            # Wikipedia API returns an object with page IDs as keys
                            page_id = next(iter(pages))
                            return pages[page_id]
        except Exception as e:
            logger.error(f"Error fetching Wikipedia page: {e}")
            
        return None
    
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Fetch information from Wikipedia."""
        if not metadata.title:
            return metadata
            
        try:
            # Add movie/tv show indicator if known
            search_query = metadata.title
            if "content_type" in metadata.fields:
                content_type = metadata.fields["content_type"].value
                if content_type in ["movie", "tv"]:
                    search_query = f"{search_query} {content_type}"
            
            # Search for the page
            page_title = await self._search_wikipedia(search_query)
            if not page_title:
                return metadata
                
            # Get the page extract
            page = await self._get_wikipedia_extract(page_title)
            if page:
                # Add Wikipedia information
                if "extract" in page:
                    # Clean up and truncate the extract
                    extract = page["extract"]
                    # Limit to a reasonable length (first few paragraphs)
                    if len(extract) > 1000:
                        paragraphs = extract.split("\n\n")
                        if len(paragraphs) > 1:
                            extract = "\n\n".join(paragraphs[:2])
                        else:
                            extract = extract[:1000] + "..."
                    
                    metadata.add_field("wikipedia_extract", extract, self.source)
                    
                if "fullurl" in page:
                    metadata.add_field("wikipedia_url", page["fullurl"], self.source)
                    
                if "thumbnail" in page and "source" in page["thumbnail"]:
                    metadata.add_field("wikipedia_image", page["thumbnail"]["source"], self.source)
        except Exception as e:
            logger.error(f"Error enriching with Wikipedia data: {e}")
            
        return metadata


class LocationEnricher(BaseMetadataEnricher):
    """Enricher that identifies and provides information about filming locations."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.CUSTOM
        self.api_key = config.get("mapbox_api_key")
        self.locations_db = config.get("locations_db", {})
        
    def _get_known_locations(self, content_id: str, title: str) -> List[Dict[str, Any]]:
        """Get known filming locations from the database."""
        locations = []
        
        # Check for locations by content ID
        if content_id in self.locations_db:
            locations = self.locations_db[content_id]
        
        # If no locations found, try to find by title
        if not locations:
            for db_id, db_locations in self.locations_db.items():
                if title.lower() in self.locations_db.get(db_id, {}).get("title", "").lower():
                    locations = db_locations.get("locations", [])
                    break
        
        return locations
    
    async def _geocode_location(self, location_name: str) -> Optional[Dict[str, Any]]:
        """Geocode a location name using Mapbox API."""
        if not self.api_key:
            return None
            
        try:
            # URL encode the location name
            encoded_location = location_name.replace(" ", "%20")
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_location}.json?access_token={self.api_key}&limit=1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        features = data.get("features", [])
                        if features:
                            feature = features[0]
                            return {
                                "name": location_name,
                                "place_name": feature.get("place_name"),
                                "coordinates": feature.get("center")  # [longitude, latitude]
                            }
        except Exception as e:
            logger.error(f"Error geocoding location: {e}")
            
        return None
    
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Add filming location information."""
        if not metadata.title:
            return metadata
            
        try:
            # Get known locations from the database
            locations = self._get_known_locations(content_id, metadata.title)
            
            if not locations:
                return metadata
                
            # Geocode locations if coordinates not available
            enriched_locations = []
            for location in locations:
                if isinstance(location, str):
                    # Simple string location, needs geocoding
                    geocoded = await self._geocode_location(location)
                    if geocoded:
                        enriched_locations.append(geocoded)
                elif isinstance(location, dict):
                    # Location dict, may already have coordinates
                    if "coordinates" in location:
                        enriched_locations.append(location)
                    else:
                        geocoded = await self._geocode_location(location.get("name", ""))
                        if geocoded:
                            # Merge with existing data
                            merged = {**location, **geocoded}
                            enriched_locations.append(merged)
            
            if enriched_locations:
                metadata.add_field("filming_locations", enriched_locations, self.source)
                
                # Add a static map image URL if Mapbox API key is available
                if self.api_key and len(enriched_locations) > 0:
                    # Create a static map with markers for all locations
                    markers = ""
                    for location in enriched_locations:
                        if "coordinates" in location:
                            lon, lat = location["coordinates"]
                            markers += f"pin-s({lon},{lat})/"
                    
                    if markers:
                        # Remove the trailing slash
                        markers = markers[:-1]
                        map_url = f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/{markers}/auto/500x300?access_token={self.api_key}"
                        metadata.add_field("locations_map_url", map_url, self.source)
                
        except Exception as e:
            logger.error(f"Error enriching with location data: {e}")
            
        return metadata


class ContentAnalysisEnricher(BaseMetadataEnricher):
    """Enricher that analyzes content to extract themes, mood, and other attributes."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source = MetadataSource.CUSTOM
        self.themes_mapping = config.get("themes_mapping", {})
        self.genres_to_themes = config.get("genres_to_themes", {})
        self.keywords_to_themes = config.get("keywords_to_themes", {})
        
    def _extract_themes(self, metadata: EnhancedMetadata) -> List[str]:
        """Extract themes based on genres, keywords, and description."""
        themes = set()
        
        # Extract from genres
        genres = metadata.fields.get("genres", {}).value if "genres" in metadata.fields else []
        if isinstance(genres, list):
            for genre in genres:
                if genre in self.genres_to_themes:
                    themes.update(self.genres_to_themes[genre])
        
        # Extract from keywords
        keywords = metadata.fields.get("keywords", {}).value if "keywords" in metadata.fields else []
        if isinstance(keywords, list):
            for keyword in keywords:
                if keyword in self.keywords_to_themes:
                    themes.update(self.keywords_to_themes[keyword])
                    
        # Extract from description if available
        description = metadata.fields.get("overview", {}).value if "overview" in metadata.fields else ""
        if description:
            for theme, indicators in self.themes_mapping.items():
                if any(indicator.lower() in description.lower() for indicator in indicators):
                    themes.add(theme)
        
        return list(themes)
    
    def _analyze_mood(self, metadata: EnhancedMetadata) -> Optional[str]:
        """Analyze the mood of the content based on genres and description."""
        # Simple mood mapping from genres
        mood_mapping = {
            "Comedy": "light-hearted",
            "Horror": "tense",
            "Thriller": "suspenseful",
            "Drama": "emotional",
            "Action": "exciting",
            "Romance": "romantic",
            "Sci-Fi": "cerebral",
            "Fantasy": "whimsical",
            "Documentary": "informative",
            "Animation": "imaginative"
        }
        
        # Check genres first
        genres = metadata.fields.get("genres", {}).value if "genres" in metadata.fields else []
        if isinstance(genres, list):
            for genre in genres:
                if genre in mood_mapping:
                    return mood_mapping[genre]
        
        # Fallback to keywords
        keywords = metadata.fields.get("keywords", {}).value if "keywords" in metadata.fields else []
        for keyword in keywords:
            # Map some common keywords to moods
            if keyword.lower() in ["dark", "gritty", "bleak"]:
                return "dark"
            elif keyword.lower() in ["uplifting", "inspirational"]:
                return "uplifting"
            elif keyword.lower() in ["funny", "comedy", "humorous"]:
                return "light-hearted"
        
        return None
    
    def _extract_time_period(self, metadata: EnhancedMetadata) -> Optional[str]:
        """Extract the time period of the content."""
        # Try to extract from release year
        release_date = None
        for field_name in ["release_date", "first_air_date"]:
            if field_name in metadata.fields:
                release_date = metadata.fields[field_name].value
                break
        
        if release_date and isinstance(release_date, str):
            # Extract just the year
            year_match = re.search(r'\d{4}', release_date)
            if year_match:
                year = int(year_match.group(0))
                
                # Map to time periods
                if year < 1920:
                    return "pre-1920s"
                elif year < 1930:
                    return "1920s"
                elif year < 1940:
                    return "1930s"
                elif year < 1950:
                    return "1940s"
                elif year < 1960:
                    return "1950s"
                elif year < 1970:
                    return "1960s"
                elif year < 1980:
                    return "1970s"
                elif year < 1990:
                    return "1980s"
                elif year < 2000:
                    return "1990s"
                elif year < 2010:
                    return "2000s"
                elif year < 2020:
                    return "2010s"
                else:
                    return "2020s"
        
        # Look for period indicators in keywords
        keywords = metadata.fields.get("keywords", {}).value if "keywords" in metadata.fields else []
        for keyword in keywords:
            if "medieval" in keyword.lower():
                return "medieval"
            elif "victorian" in keyword.lower():
                return "victorian"
            elif "world war ii" in keyword.lower() or "ww2" in keyword.lower():
                return "world war II"
            elif "future" in keyword.lower() or "futuristic" in keyword.lower():
                return "future"
        
        return None
    
    async def _enrich_implementation(self, content_id: str, metadata: EnhancedMetadata) -> EnhancedMetadata:
        """Analyze content and extract additional attributes."""
        try:
            # Extract themes
            themes = self._extract_themes(metadata)
            if themes:
                metadata.add_field("themes", themes, self.source, confidence=0.8)
            
            # Analyze mood
            mood = self._analyze_mood(metadata)
            if mood:
                metadata.add_field("mood", mood, self.source, confidence=0.7)
            
            # Extract time period
            time_period = self._extract_time_period(metadata)
            if time_period:
                metadata.add_field("time_period", time_period, self.source, confidence=0.7)
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            
        return metadata
