# app/core/cache.py
"""
In-memory caching module with TTL support.

Provides a simple but effective caching layer for frequently accessed data
like resume lookups, reducing database load.
"""
import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, TypeVar

from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""

    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return datetime.utcnow() > self.expires_at


class TTLCache:
    """
    Thread-safe in-memory cache with TTL support.

    Features:
    - Configurable default TTL
    - Automatic cleanup of expired entries
    - Cache statistics for monitoring
    - Key prefix support for namespacing
    """

    def __init__(
        self,
        default_ttl_seconds: int = 300,
        max_size: int = 1000,
        cleanup_interval_seconds: int = 60,
    ):
        """
        Initialize cache.

        Args:
            default_ttl_seconds: Default time-to-live for entries (5 minutes)
            max_size: Maximum number of entries before eviction
            cleanup_interval_seconds: Interval for background cleanup
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = timedelta(seconds=default_ttl_seconds)
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval_seconds
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

        # Statistics
        self._hits = 0
        self._misses = 0

    async def start(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info(
                "Cache cleanup task started",
                extra={
                    "event_type": "cache_started",
                    "cleanup_interval": self._cleanup_interval,
                },
            )

    async def stop(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped", extra={"event_type": "cache_stopped"})

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Cache cleanup error",
                    extra={"event_type": "cache_cleanup_error", "error": str(e)},
                )

    async def _cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(
                    "Cleaned up expired cache entries",
                    extra={
                        "event_type": "cache_cleanup",
                        "removed_count": len(expired_keys),
                        "remaining_count": len(self._cache),
                    },
                )

            return len(expired_keys)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return entry.value

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses default if not specified)
        """
        ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self._default_ttl
        expires_at = datetime.utcnow() + ttl

        async with self._lock:
            # Evict oldest entries if at max size
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()

            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def _evict_oldest(self) -> None:
        """Evict oldest entries when cache is full."""
        if not self._cache:
            return

        # Sort by creation time and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        evict_count = max(1, len(sorted_keys) // 10)

        for key in sorted_keys[:evict_count]:
            del self._cache[key]

        logger.debug(
            "Evicted oldest cache entries",
            extra={"event_type": "cache_eviction", "evicted_count": evict_count},
        )

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern prefix.

        Args:
            pattern: Key prefix to match

        Returns:
            Number of keys invalidated
        """
        async with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    async def clear(self) -> None:
        """Clear all entries from cache."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared", extra={"event_type": "cache_cleared"})

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, size, and hit ratio
        """
        total = self._hits + self._misses
        hit_ratio = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_ratio": round(hit_ratio, 4),
        }


# Global cache instance
_cache: Optional[TTLCache] = None


def get_cache() -> TTLCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = TTLCache(
            default_ttl_seconds=300,  # 5 minutes
            max_size=1000,
            cleanup_interval_seconds=60,
        )
    return _cache


def cache_key(*args: Any, prefix: str = "") -> str:
    """
    Generate a cache key from arguments.

    Args:
        *args: Values to include in key
        prefix: Optional prefix for namespacing

    Returns:
        Hash-based cache key
    """
    key_data = ":".join(str(arg) for arg in args)
    if prefix:
        key_data = f"{prefix}:{key_data}"
    return hashlib.md5(key_data.encode()).hexdigest()


async def cached(
    key: str,
    getter: Callable[[], Any],
    ttl_seconds: Optional[int] = None,
) -> Any:
    """
    Get value from cache or compute it.

    Args:
        key: Cache key
        getter: Async function to compute value if not cached
        ttl_seconds: Optional custom TTL

    Returns:
        Cached or computed value
    """
    cache = get_cache()
    value = await cache.get(key)

    if value is not None:
        return value

    # Compute and cache the value
    if asyncio.iscoroutinefunction(getter):
        value = await getter()
    else:
        value = getter()

    await cache.set(key, value, ttl_seconds)
    return value
