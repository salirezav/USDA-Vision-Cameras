"""
Streaming Cache Implementations.

In-memory and file-based caching for video streaming optimization.
"""

import asyncio
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import hashlib

from ..domain.interfaces import StreamingCache
from ..domain.models import StreamRange


class InMemoryStreamingCache(StreamingCache):
    """In-memory cache for video streaming"""
    
    def __init__(self, max_size_mb: int = 100, max_age_minutes: int = 30):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_age = timedelta(minutes=max_age_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Cache storage: {cache_key: (data, timestamp, size)}
        self._cache: Dict[str, Tuple[bytes, datetime, int]] = {}
        self._current_size = 0
        self._lock = asyncio.Lock()
    
    async def get_cached_range(
        self,
        file_id: str,
        range_request: StreamRange
    ) -> Optional[bytes]:
        """Get cached byte range"""
        cache_key = self._generate_cache_key(file_id, range_request)
        
        async with self._lock:
            if cache_key in self._cache:
                data, timestamp, size = self._cache[cache_key]
                
                # Check if cache entry is still valid
                if datetime.now() - timestamp <= self.max_age:
                    self.logger.debug(f"Cache hit for {file_id} range {range_request.start}-{range_request.end}")
                    return data
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
                    self._current_size -= size
                    self.logger.debug(f"Cache entry expired for {file_id}")
            
            return None
    
    async def cache_range(
        self,
        file_id: str,
        range_request: StreamRange,
        data: bytes
    ) -> None:
        """Cache byte range data"""
        cache_key = self._generate_cache_key(file_id, range_request)
        data_size = len(data)
        
        async with self._lock:
            # Check if we need to make space
            while self._current_size + data_size > self.max_size_bytes and self._cache:
                await self._evict_oldest()
            
            # Add to cache
            self._cache[cache_key] = (data, datetime.now(), data_size)
            self._current_size += data_size
            
            self.logger.debug(f"Cached {data_size} bytes for {file_id} range {range_request.start}-{range_request.end}")
    
    async def invalidate_file(self, file_id: str) -> None:
        """Invalidate all cached data for a file"""
        async with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{file_id}:")]
            
            for key in keys_to_remove:
                _, _, size = self._cache[key]
                del self._cache[key]
                self._current_size -= size
            
            if keys_to_remove:
                self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries for {file_id}")
    
    async def cleanup_cache(self, max_size_mb: int = 100) -> int:
        """Clean up cache to stay under size limit"""
        target_size = max_size_mb * 1024 * 1024
        entries_removed = 0
        
        async with self._lock:
            # Remove expired entries first
            current_time = datetime.now()
            expired_keys = [
                key for key, (_, timestamp, _) in self._cache.items()
                if current_time - timestamp > self.max_age
            ]
            
            for key in expired_keys:
                _, _, size = self._cache[key]
                del self._cache[key]
                self._current_size -= size
                entries_removed += 1
            
            # Remove oldest entries if still over limit
            while self._current_size > target_size and self._cache:
                await self._evict_oldest()
                entries_removed += 1
        
        if entries_removed > 0:
            self.logger.info(f"Cache cleanup removed {entries_removed} entries")
        
        return entries_removed
    
    async def _evict_oldest(self) -> None:
        """Evict the oldest cache entry"""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        _, _, size = self._cache[oldest_key]
        del self._cache[oldest_key]
        self._current_size -= size
        
        self.logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def _generate_cache_key(self, file_id: str, range_request: StreamRange) -> str:
        """Generate cache key for file and range"""
        range_str = f"{range_request.start}-{range_request.end}"
        return f"{file_id}:{range_str}"
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        async with self._lock:
            return {
                "entries": len(self._cache),
                "size_bytes": self._current_size,
                "size_mb": self._current_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "utilization_percent": (self._current_size / self.max_size_bytes) * 100
            }


class NoOpStreamingCache(StreamingCache):
    """No-operation cache that doesn't actually cache anything"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_cached_range(
        self,
        file_id: str,
        range_request: StreamRange
    ) -> Optional[bytes]:
        """Always return None (no cache)"""
        return None
    
    async def cache_range(
        self,
        file_id: str,
        range_request: StreamRange,
        data: bytes
    ) -> None:
        """No-op caching"""
        pass
    
    async def invalidate_file(self, file_id: str) -> None:
        """No-op invalidation"""
        pass
    
    async def cleanup_cache(self, max_size_mb: int = 100) -> int:
        """No-op cleanup"""
        return 0
