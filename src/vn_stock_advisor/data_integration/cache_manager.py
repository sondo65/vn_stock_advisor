"""
Cache Manager - Phase 3

High-performance caching system for financial data with:
- Multi-level caching (memory, disk, distributed)
- TTL-based expiration
- Cache invalidation strategies
- Performance optimization
"""

import asyncio
import json
import pickle
import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from threading import RLock
from collections import OrderedDict

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available, using memory cache only")

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.created_at

@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    memory_usage_bytes: int = 0
    disk_usage_bytes: int = 0
    average_access_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests * 100

class CacheManager:
    """Advanced caching system for financial data."""
    
    def __init__(self, 
                 max_memory_size: int = 100 * 1024 * 1024,  # 100MB
                 max_disk_size: int = 1024 * 1024 * 1024,   # 1GB
                 cache_dir: str = ".cache",
                 redis_url: Optional[str] = None,
                 default_ttl: int = 3600):  # 1 hour
        """
        Initialize cache manager.
        
        Args:
            max_memory_size: Maximum memory cache size in bytes
            max_disk_size: Maximum disk cache size in bytes
            cache_dir: Directory for disk cache
            redis_url: Redis connection URL for distributed cache
            default_ttl: Default TTL in seconds
        """
        self.max_memory_size = max_memory_size
        self.max_disk_size = max_disk_size
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)
        
        # Memory cache (LRU)
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.memory_lock = RLock()
        
        # Disk cache
        self.cache_dir.mkdir(exist_ok=True)
        self.disk_cache_index: Dict[str, Dict] = {}
        self._load_disk_index()
        
        # Redis cache
        self.redis_client = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                self.logger.info("Redis cache connected")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
        
        # Statistics
        self.stats = CacheStats()
        
        # Cache levels priority
        self.cache_levels = ['memory', 'disk', 'redis'] if self.redis_client else ['memory', 'disk']
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with multi-level lookup.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        start_time = time.time()
        
        try:
            self.stats.total_requests += 1
            
            # Try memory cache first
            value = await self._get_from_memory(key)
            if value is not None:
                self.stats.hits += 1
                self._update_access_time(start_time)
                return value
            
            # Try disk cache
            value = await self._get_from_disk(key)
            if value is not None:
                # Promote to memory cache
                await self._set_to_memory(key, value, ttl=self.default_ttl)
                self.stats.hits += 1
                self._update_access_time(start_time)
                return value
            
            # Try Redis cache
            if self.redis_client:
                value = await self._get_from_redis(key)
                if value is not None:
                    # Promote to memory and disk
                    await self._set_to_memory(key, value, ttl=self.default_ttl)
                    await self._set_to_disk(key, value, ttl=self.default_ttl)
                    self.stats.hits += 1
                    self._update_access_time(start_time)
                    return value
            
            # Cache miss
            self.stats.misses += 1
            self._update_access_time(start_time)
            return default
            
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
        """
        Set value in cache with multi-level storage.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Cache tags for grouping
            
        Returns:
            True if successfully cached
        """
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            if tags is None:
                tags = []
            
            # Set in all cache levels
            success_memory = await self._set_to_memory(key, value, ttl, tags)
            success_disk = await self._set_to_disk(key, value, ttl, tags)
            success_redis = True
            
            if self.redis_client:
                success_redis = await self._set_to_redis(key, value, ttl, tags)
            
            return success_memory or success_disk or success_redis
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from all cache levels.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was found and deleted
        """
        try:
            deleted = False
            
            # Delete from memory
            with self.memory_lock:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    deleted = True
            
            # Delete from disk
            disk_path = self._get_disk_path(key)
            if disk_path.exists():
                disk_path.unlink()
                if key in self.disk_cache_index:
                    del self.disk_cache_index[key]
                deleted = True
            
            # Delete from Redis
            if self.redis_client:
                redis_deleted = self.redis_client.delete(key)
                if redis_deleted:
                    deleted = True
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def clear(self, tags: Optional[List[str]] = None) -> int:
        """
        Clear cache entries, optionally by tags.
        
        Args:
            tags: Clear only entries with these tags
            
        Returns:
            Number of entries cleared
        """
        try:
            cleared_count = 0
            
            if tags is None:
                # Clear all
                with self.memory_lock:
                    cleared_count += len(self.memory_cache)
                    self.memory_cache.clear()
                
                # Clear disk cache
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                    cleared_count += 1
                self.disk_cache_index.clear()
                
                # Clear Redis
                if self.redis_client:
                    self.redis_client.flushdb()
            
            else:
                # Clear by tags
                keys_to_delete = []
                
                # Find keys with matching tags in memory
                with self.memory_lock:
                    for key, entry in self.memory_cache.items():
                        if any(tag in entry.tags for tag in tags):
                            keys_to_delete.append(key)
                
                # Delete found keys
                for key in keys_to_delete:
                    if await self.delete(key):
                        cleared_count += 1
            
            self.logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return 0
    
    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None, tags: List[str] = None) -> Any:
        """
        Get value from cache or set it using factory function.
        
        Args:
            key: Cache key
            factory: Function to generate value if not cached
            ttl: Time to live in seconds
            tags: Cache tags
            
        Returns:
            Cached or generated value
        """
        try:
            # Try to get from cache first
            value = await self.get(key)
            if value is not None:
                return value
            
            # Generate value using factory
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            # Cache the generated value
            await self.set(key, value, ttl, tags)
            return value
            
        except Exception as e:
            self.logger.error(f"Error in get_or_set for key {key}: {e}")
            # Try to return cached value even if factory fails
            return await self.get(key)
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        # Update memory usage
        with self.memory_lock:
            self.stats.memory_usage_bytes = sum(
                entry.size_bytes for entry in self.memory_cache.values()
            )
        
        # Update disk usage
        try:
            self.stats.disk_usage_bytes = sum(
                f.stat().st_size for f in self.cache_dir.glob("*.cache")
            )
        except Exception:
            pass
        
        return self.stats
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        try:
            cleaned_count = 0
            now = datetime.now()
            
            # Clean memory cache
            with self.memory_lock:
                expired_keys = [
                    key for key, entry in self.memory_cache.items()
                    if entry.expires_at and entry.expires_at < now
                ]
                
                for key in expired_keys:
                    del self.memory_cache[key]
                    cleaned_count += 1
            
            # Clean disk cache
            expired_disk_keys = []
            for key, metadata in self.disk_cache_index.items():
                if 'expires_at' in metadata:
                    expires_at = datetime.fromisoformat(metadata['expires_at'])
                    if expires_at < now:
                        expired_disk_keys.append(key)
            
            for key in expired_disk_keys:
                disk_path = self._get_disk_path(key)
                if disk_path.exists():
                    disk_path.unlink()
                del self.disk_cache_index[key]
                cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired cache entries")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    async def _get_from_memory(self, key: str) -> Any:
        """Get value from memory cache."""
        try:
            with self.memory_lock:
                if key not in self.memory_cache:
                    return None
                
                entry = self.memory_cache[key]
                
                # Check expiration
                if entry.expires_at and entry.expires_at < datetime.now():
                    del self.memory_cache[key]
                    return None
                
                # Update access info
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                
                # Move to end (LRU)
                self.memory_cache.move_to_end(key)
                
                return entry.value
                
        except Exception as e:
            self.logger.error(f"Error getting from memory cache: {e}")
            return None
    
    async def _set_to_memory(self, key: str, value: Any, ttl: int, tags: List[str] = None) -> bool:
        """Set value in memory cache."""
        try:
            with self.memory_lock:
                # Calculate size
                size_bytes = len(pickle.dumps(value))
                
                # Check if we need to evict
                while (len(self.memory_cache) > 0 and 
                       sum(entry.size_bytes for entry in self.memory_cache.values()) + size_bytes > self.max_memory_size):
                    # Remove least recently used
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                    self.stats.evictions += 1
                
                # Create cache entry
                expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size_bytes=size_bytes,
                    tags=tags or []
                )
                
                self.memory_cache[key] = entry
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting to memory cache: {e}")
            return False
    
    async def _get_from_disk(self, key: str) -> Any:
        """Get value from disk cache."""
        try:
            if key not in self.disk_cache_index:
                return None
            
            metadata = self.disk_cache_index[key]
            
            # Check expiration
            if 'expires_at' in metadata:
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                if expires_at < datetime.now():
                    # Clean up expired entry
                    await self.delete(key)
                    return None
            
            # Load from disk
            disk_path = self._get_disk_path(key)
            if not disk_path.exists():
                return None
            
            with open(disk_path, 'rb') as f:
                value = pickle.load(f)
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting from disk cache: {e}")
            return None
    
    async def _set_to_disk(self, key: str, value: Any, ttl: int, tags: List[str] = None) -> bool:
        """Set value in disk cache."""
        try:
            # Check disk space
            current_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
            if current_size > self.max_disk_size:
                # TODO: Implement disk cache eviction
                pass
            
            disk_path = self._get_disk_path(key)
            
            # Save to disk
            with open(disk_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Update index
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            self.disk_cache_index[key] = {
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
                'tags': tags or [],
                'size_bytes': disk_path.stat().st_size
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting to disk cache: {e}")
            return False
    
    async def _get_from_redis(self, key: str) -> Any:
        """Get value from Redis cache."""
        try:
            if not self.redis_client:
                return None
            
            data = self.redis_client.get(key)
            if data is None:
                return None
            
            return pickle.loads(data)
            
        except Exception as e:
            self.logger.error(f"Error getting from Redis cache: {e}")
            return None
    
    async def _set_to_redis(self, key: str, value: Any, ttl: int, tags: List[str] = None) -> bool:
        """Set value in Redis cache."""
        try:
            if not self.redis_client:
                return False
            
            data = pickle.dumps(value)
            result = self.redis_client.setex(key, ttl, data)
            
            # Set tags if provided
            if tags:
                for tag in tags:
                    self.redis_client.sadd(f"tag:{tag}", key)
                    self.redis_client.expire(f"tag:{tag}", ttl)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error setting to Redis cache: {e}")
            return False
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk path for cache key."""
        # Hash key to create safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _load_disk_index(self):
        """Load disk cache index."""
        try:
            index_path = self.cache_dir / "index.json"
            if index_path.exists():
                with open(index_path, 'r') as f:
                    self.disk_cache_index = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load disk cache index: {e}")
            self.disk_cache_index = {}
    
    def _save_disk_index(self):
        """Save disk cache index."""
        try:
            index_path = self.cache_dir / "index.json"
            with open(index_path, 'w') as f:
                json.dump(self.disk_cache_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save disk cache index: {e}")
    
    def _update_access_time(self, start_time: float):
        """Update average access time statistics."""
        access_time_ms = (time.time() - start_time) * 1000
        if self.stats.total_requests == 1:
            self.stats.average_access_time_ms = access_time_ms
        else:
            # Running average
            self.stats.average_access_time_ms = (
                (self.stats.average_access_time_ms * (self.stats.total_requests - 1) + access_time_ms) 
                / self.stats.total_requests
            )
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self._save_disk_index()
        except Exception:
            pass

# Example usage and testing
async def test_cache_manager():
    """Test the cache manager."""
    cache = CacheManager(max_memory_size=1024*1024, default_ttl=60)
    
    print("Testing cache operations...")
    
    # Test set/get
    await cache.set("test_key", {"data": "test_value", "number": 42})
    value = await cache.get("test_key")
    print(f"Cached value: {value}")
    
    # Test get_or_set
    def expensive_operation():
        return {"computed": "expensive_result", "timestamp": datetime.now().isoformat()}
    
    result = await cache.get_or_set("computed_key", expensive_operation, ttl=30)
    print(f"Computed result: {result}")
    
    # Test cache hit
    cached_result = await cache.get("computed_key")
    print(f"Cache hit: {cached_result}")
    
    # Test statistics
    stats = cache.get_stats()
    print(f"Cache stats: Hit rate: {stats.hit_rate:.1f}%, Memory: {stats.memory_usage_bytes} bytes")
    
    # Cleanup
    await cache.cleanup_expired()

if __name__ == "__main__":
    asyncio.run(test_cache_manager())
