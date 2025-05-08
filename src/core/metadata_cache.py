"""Metadata Enrichment Cache System

This module provides an optimized caching system for the metadata enrichment process
to improve performance and reduce external API requests.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """Cache levels for different types of data."""
    IN_MEMORY = "memory"     # Fast in-memory cache
    LOCAL_FILE = "file"      # Local file-based cache
    REDIS = "redis"          # Redis-based cache for distributed systems


class CachePriority(int, Enum):
    """Priority levels for cache entries."""
    LOW = 0      # Less important, can be evicted first
    MEDIUM = 1   # Standard priority
    HIGH = 2     # High priority, should be kept longer
    CRITICAL = 3 # Critical data, rarely evicted


class CacheConfig:
    """Configuration for metadata cache."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cache configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.enabled = config.get("enabled", True)
        
        # Memory cache settings
        memory_config = config.get("memory_cache", {})
        self.memory_cache_enabled = memory_config.get("enabled", True)
        self.memory_cache_ttl = memory_config.get("ttl", 3600)  # Default 1 hour
        self.memory_cache_max_size = memory_config.get("max_size", 1000)  # Max entries
        self.memory_cache_cleanup_interval = memory_config.get("cleanup_interval", 300)  # 5 minutes
        
        # File cache settings
        file_config = config.get("file_cache", {})
        self.file_cache_enabled = file_config.get("enabled", True)
        self.file_cache_ttl = file_config.get("ttl", 86400)  # Default 24 hours
        self.file_cache_dir = file_config.get("directory", "/tmp/videntify_cache")
        self.file_cache_max_size_mb = file_config.get("max_size_mb", 100)  # Max size in MB
        
        # Redis cache settings
        redis_config = config.get("redis_cache", {})
        self.redis_cache_enabled = redis_config.get("enabled", False)
        self.redis_host = redis_config.get("host", "localhost")
        self.redis_port = redis_config.get("port", 6379)
        self.redis_db = redis_config.get("db", 0)
        self.redis_password = redis_config.get("password")
        self.redis_ttl = redis_config.get("ttl", 604800)  # Default 1 week
        self.redis_key_prefix = redis_config.get("key_prefix", "videntify:metadata:")
        
        # Source-specific TTLs
        self.source_ttls = config.get("source_ttls", {
            "file": 86400,          # File metadata rarely changes - 24 hours
            "local_db": 3600,       # Local database - 1 hour
            "tmdb": 604800,         # TMDB data - 1 week
            "youtube": 86400,       # YouTube data - 24 hours
            "custom": 43200         # Custom sources - 12 hours
        })
        
        # Cache invalidation settings
        self.auto_invalidation_enabled = config.get("auto_invalidation", {}).get("enabled", True)
        self.invalidation_patterns = config.get("auto_invalidation", {}).get("patterns", [])


class CacheEntry:
    """A single cache entry with metadata."""
    
    def __init__(self, key: str, value: Any, ttl: int = 3600, priority: CachePriority = CachePriority.MEDIUM):
        """Initialize a cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl: Time to live in seconds
            priority: Cache priority level
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.expiry = self.created_at + ttl
        self.access_count = 0
        self.priority = priority
    
    def is_expired(self) -> bool:
        """Check if the entry is expired.
        
        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expiry
    
    def access(self):
        """Record an access to this cache entry."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def get_age(self) -> float:
        """Get the age of the entry in seconds.
        
        Returns:
            Age in seconds
        """
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """Get the idle time (time since last access) in seconds.
        
        Returns:
            Idle time in seconds
        """
        return time.time() - self.last_accessed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to a dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "expiry": self.expiry,
            "access_count": self.access_count,
            "priority": self.priority.value if isinstance(self.priority, CachePriority) else self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create a cache entry from a dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            CacheEntry instance
        """
        entry = cls(data["key"], data["value"])
        entry.created_at = data.get("created_at", time.time())
        entry.last_accessed = data.get("last_accessed", time.time())
        entry.expiry = data.get("expiry", time.time() + 3600)
        entry.access_count = data.get("access_count", 0)
        entry.priority = CachePriority(data.get("priority", CachePriority.MEDIUM.value))
        return entry


class MetadataCache:
    """Cache manager for metadata enrichment system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the cache manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = CacheConfig(config)
        
        # Initialize caches
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.last_memory_cleanup = time.time()
        
        # Initialize file cache directory
        if self.config.file_cache_enabled:
            os.makedirs(self.config.file_cache_dir, exist_ok=True)
        
        # Initialize Redis connection if enabled
        self.redis_client = None
        if self.config.redis_cache_enabled:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    password=self.config.redis_password
                )
                # Test the connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.config.redis_cache_enabled = False
                self.redis_client = None
        
        logger.info("Initialized MetadataCache")
        if self.config.enabled:
            logger.info(f"Cache configuration: Memory: {self.config.memory_cache_enabled}, "
                       f"File: {self.config.file_cache_enabled}, "
                       f"Redis: {self.config.redis_cache_enabled}")
    
    def _generate_key(self, content_id: str, source: Optional[str] = None) -> str:
        """Generate a cache key.
        
        Args:
            content_id: Content ID
            source: Optional source identifier
            
        Returns:
            Cache key
        """
        if source:
            return f"{content_id}:{source}"
        return content_id
    
    def _get_file_path(self, key: str) -> str:
        """Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            File path
        """
        # Create a safe filename by replacing invalid characters
        safe_key = key.replace(":", "_").replace("/", "_")
        return os.path.join(self.config.file_cache_dir, f"{safe_key}.json")
    
    def _get_redis_key(self, key: str) -> str:
        """Get the Redis key for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Redis key
        """
        return f"{self.config.redis_key_prefix}{key}"
    
    def _check_memory_cache(self, key: str) -> Optional[Any]:
        """Check if a key exists in memory cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if not self.config.memory_cache_enabled:
            return None
            
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not entry.is_expired():
                # Update access metadata
                entry.access()
                return entry.value
            else:
                # Remove expired entry
                del self.memory_cache[key]
                
        return None
    
    def _check_file_cache(self, key: str) -> Optional[Any]:
        """Check if a key exists in file cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if not self.config.file_cache_enabled:
            return None
            
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    entry_data = json.load(f)
                    entry = CacheEntry.from_dict(entry_data)
                    
                    if not entry.is_expired():
                        # Update access metadata and save back
                        entry.access()
                        with open(file_path, 'w') as f:
                            json.dump(entry.to_dict(), f)
                        return entry.value
                    else:
                        # Remove expired file
                        os.remove(file_path)
            except Exception as e:
                logger.error(f"Error reading file cache: {e}")
                try:
                    # Remove corrupted file
                    os.remove(file_path)
                except:
                    pass
                
        return None
    
    def _check_redis_cache(self, key: str) -> Optional[Any]:
        """Check if a key exists in Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        if not self.config.redis_cache_enabled or not self.redis_client:
            return None
            
        try:
            redis_key = self._get_redis_key(key)
            cached_data = self.redis_client.get(redis_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error checking Redis cache: {e}")
            
        return None
    
    def get(self, content_id: str, source: Optional[str] = None) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            content_id: Content ID
            source: Optional source identifier
            
        Returns:
            Cached value if found, None otherwise
        """
        if not self.config.enabled:
            return None
            
        key = self._generate_key(content_id, source)
        
        # Check memory cache first (fastest)
        memory_result = self._check_memory_cache(key)
        if memory_result is not None:
            logger.debug(f"Memory cache hit for {key}")
            return memory_result
            
        # Check file cache second
        file_result = self._check_file_cache(key)
        if file_result is not None:
            logger.debug(f"File cache hit for {key}")
            # Add to memory cache for faster access next time
            if self.config.memory_cache_enabled:
                ttl = self.config.source_ttls.get(source, self.config.memory_cache_ttl)
                self.memory_cache[key] = CacheEntry(key, file_result, ttl)
            return file_result
            
        # Check Redis cache last (slowest but distributed)
        redis_result = self._check_redis_cache(key)
        if redis_result is not None:
            logger.debug(f"Redis cache hit for {key}")
            # Add to memory cache for faster access next time
            if self.config.memory_cache_enabled:
                ttl = self.config.source_ttls.get(source, self.config.memory_cache_ttl)
                self.memory_cache[key] = CacheEntry(key, redis_result, ttl)
            return redis_result
            
        logger.debug(f"Cache miss for {key}")
        return None
    
    def set(self, content_id: str, value: Any, source: Optional[str] = None, 
            priority: CachePriority = CachePriority.MEDIUM):
        """Set a value in cache.
        
        Args:
            content_id: Content ID
            value: Value to cache
            source: Optional source identifier (affects TTL)
            priority: Cache priority level
        """
        if not self.config.enabled or value is None:
            return
            
        key = self._generate_key(content_id, source)
        
        # Determine TTL based on source
        ttl = self.config.source_ttls.get(source, self.config.memory_cache_ttl)
        
        # Add to memory cache
        if self.config.memory_cache_enabled:
            # Check if we need to clean up first
            self._maybe_cleanup_memory_cache()
            
            # Add to memory cache
            self.memory_cache[key] = CacheEntry(key, value, ttl, priority)
            
        # Add to file cache
        if self.config.file_cache_enabled:
            try:
                file_path = self._get_file_path(key)
                entry = CacheEntry(key, value, self.config.file_cache_ttl, priority)
                with open(file_path, 'w') as f:
                    json.dump(entry.to_dict(), f)
            except Exception as e:
                logger.error(f"Error writing to file cache: {e}")
                
        # Add to Redis cache
        if self.config.redis_cache_enabled and self.redis_client:
            try:
                redis_key = self._get_redis_key(key)
                serialized = json.dumps(value)
                self.redis_client.setex(redis_key, self.config.redis_ttl, serialized)
            except Exception as e:
                logger.error(f"Error writing to Redis cache: {e}")
    
    def invalidate(self, content_id: str, source: Optional[str] = None):
        """Invalidate a cache entry.
        
        Args:
            content_id: Content ID
            source: Optional source identifier
        """
        key = self._generate_key(content_id, source)
        
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            
        # Remove from file cache
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing file cache: {e}")
                
        # Remove from Redis cache
        if self.config.redis_cache_enabled and self.redis_client:
            try:
                redis_key = self._get_redis_key(key)
                self.redis_client.delete(redis_key)
            except Exception as e:
                logger.error(f"Error removing from Redis cache: {e}")
    
    def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match against keys
        """
        import re
        regex = re.compile(pattern)
        
        # Invalidate memory cache entries
        keys_to_remove = []
        for key in self.memory_cache.keys():
            if regex.search(key):
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.memory_cache[key]
            
        # Invalidate file cache entries
        if self.config.file_cache_enabled and os.path.exists(self.config.file_cache_dir):
            for filename in os.listdir(self.config.file_cache_dir):
                if filename.endswith(".json"):
                    # Convert filename back to key format
                    key = filename[:-5].replace("_", ":")
                    if regex.search(key):
                        try:
                            os.remove(os.path.join(self.config.file_cache_dir, filename))
                        except Exception as e:
                            logger.error(f"Error removing file cache: {e}")
                            
        # Invalidate Redis cache entries (more complex, requires scan)
        if self.config.redis_cache_enabled and self.redis_client:
            try:
                # Use Redis SCAN to find matching keys
                prefix = self.config.redis_key_prefix
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
                    for redis_key in keys:
                        # Convert to our key format
                        key = redis_key.decode("utf-8").replace(prefix, "")
                        if regex.search(key):
                            self.redis_client.delete(redis_key)
                            
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Error scanning Redis cache: {e}")
    
    def clear(self):
        """Clear all cache data."""
        # Clear memory cache
        self.memory_cache = {}
        
        # Clear file cache
        if self.config.file_cache_enabled and os.path.exists(self.config.file_cache_dir):
            for filename in os.listdir(self.config.file_cache_dir):
                if filename.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.config.file_cache_dir, filename))
                    except Exception as e:
                        logger.error(f"Error removing file cache: {e}")
                        
        # Clear Redis cache
        if self.config.redis_cache_enabled and self.redis_client:
            try:
                # Delete all keys with our prefix
                prefix = self.config.redis_key_prefix
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
                    if keys:
                        self.redis_client.delete(*keys)
                        
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")
    
    def _maybe_cleanup_memory_cache(self):
        """Check if memory cache needs cleanup and perform if necessary."""
        # Check if it's time for a cleanup
        current_time = time.time()
        if (current_time - self.last_memory_cleanup < self.config.memory_cache_cleanup_interval and
                len(self.memory_cache) < self.config.memory_cache_max_size):
            return
            
        self.last_memory_cleanup = current_time
        
        # Find expired entries and remove them
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if entry.is_expired():
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.memory_cache[key]
            
        # If we're still over the size limit, use eviction strategy
        if len(self.memory_cache) > self.config.memory_cache_max_size:
            self._evict_from_memory_cache()
    
    def _evict_from_memory_cache(self):
        """Evict entries from memory cache based on priority and usage."""
        # Calculate how many entries to evict
        target_size = int(self.config.memory_cache_max_size * 0.8)  # Reduce to 80%
        to_evict = len(self.memory_cache) - target_size
        
        if to_evict <= 0:
            return
            
        # Score entries for eviction
        scored_entries = []
        for key, entry in self.memory_cache.items():
            # Calculate a score based on priority, access count, and idle time
            # Lower score = more likely to be evicted
            priority_factor = (entry.priority.value + 1) * 10 if isinstance(entry.priority, CachePriority) else 10
            access_factor = min(10, entry.access_count)  # Cap at 10
            idle_factor = min(100, entry.get_idle_time()) / 10  # Higher idle time = lower score
            
            score = priority_factor + access_factor - idle_factor
            scored_entries.append((key, score))
            
        # Sort by score (ascending)
        scored_entries.sort(key=lambda x: x[1])
        
        # Evict the lowest scoring entries
        for key, _ in scored_entries[:to_evict]:
            del self.memory_cache[key]
            
        logger.debug(f"Evicted {to_evict} entries from memory cache")
    
    def _cleanup_file_cache(self):
        """Clean up file cache to stay within size limits and remove expired entries."""
        if not self.config.file_cache_enabled or not os.path.exists(self.config.file_cache_dir):
            return
            
        try:
            # Get all cache files with their size and metadata
            cache_files = []
            total_size = 0
            
            for filename in os.listdir(self.config.file_cache_dir):
                if not filename.endswith(".json"):
                    continue
                    
                file_path = os.path.join(self.config.file_cache_dir, filename)
                size = os.path.getsize(file_path)
                total_size += size
                
                # Load metadata to check expiry
                try:
                    with open(file_path, 'r') as f:
                        entry_data = json.load(f)
                        entry = CacheEntry.from_dict(entry_data)
                        
                        cache_files.append({
                            "path": file_path,
                            "size": size,
                            "entry": entry
                        })
                except Exception:
                    # If we can't load the file, mark it for deletion
                    cache_files.append({
                        "path": file_path,
                        "size": size,
                        "entry": None
                    })
            
            # Remove expired entries
            for file_info in cache_files[:]:  # Use a copy for iteration
                entry = file_info.get("entry")
                if entry is None or entry.is_expired():
                    os.remove(file_info["path"])
                    cache_files.remove(file_info)
                    total_size -= file_info["size"]
            
            # Check if we're over the size limit
            max_size_bytes = self.config.file_cache_max_size_mb * 1024 * 1024
            if total_size > max_size_bytes:
                # Sort by priority and last accessed time
                def sort_key(file_info):
                    entry = file_info.get("entry")
                    if not entry:
                        return (0, 0)  # Lowest priority
                    
                    priority = entry.priority.value if isinstance(entry.priority, CachePriority) else 0
                    return (priority, entry.last_accessed)
                
                cache_files.sort(key=sort_key)
                
                # Remove files until we're under the limit
                while total_size > max_size_bytes and cache_files:
                    file_info = cache_files.pop(0)  # Remove the lowest priority
                    os.remove(file_info["path"])
                    total_size -= file_info["size"]
        except Exception as e:
            logger.error(f"Error cleaning up file cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "enabled": self.config.enabled,
            "memory_cache": {
                "enabled": self.config.memory_cache_enabled,
                "entries": len(self.memory_cache),
                "max_size": self.config.memory_cache_max_size,
                "ttl": self.config.memory_cache_ttl
            },
            "file_cache": {
                "enabled": self.config.file_cache_enabled,
                "directory": self.config.file_cache_dir,
                "max_size_mb": self.config.file_cache_max_size_mb,
                "ttl": self.config.file_cache_ttl
            },
            "redis_cache": {
                "enabled": self.config.redis_cache_enabled,
                "connected": self.redis_client is not None,
                "ttl": self.config.redis_ttl
            }
        }
        
        # Add file cache stats
        if self.config.file_cache_enabled and os.path.exists(self.config.file_cache_dir):
            try:
                files = [f for f in os.listdir(self.config.file_cache_dir) if f.endswith(".json")]
                total_size = sum(os.path.getsize(os.path.join(self.config.file_cache_dir, f)) for f in files)
                stats["file_cache"]["entries"] = len(files)
                stats["file_cache"]["size_mb"] = total_size / (1024 * 1024)
            except Exception as e:
                logger.error(f"Error getting file cache stats: {e}")
                
        # Add Redis cache stats
        if self.config.redis_cache_enabled and self.redis_client:
            try:
                prefix = self.config.redis_key_prefix
                cursor = 0
                count = 0
                
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
                    count += len(keys)
                    
                    if cursor == 0:
                        break
                        
                stats["redis_cache"]["entries"] = count
                
                # Get memory usage if available
                try:
                    info = self.redis_client.info("memory")
                    stats["redis_cache"]["used_memory_mb"] = info.get("used_memory", 0) / (1024 * 1024)
                except:
                    pass
            except Exception as e:
                logger.error(f"Error getting Redis cache stats: {e}")
                
        return stats
