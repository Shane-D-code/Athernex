"""
Caching layer for LLM responses and TTS audio.

Implements:
- LRU cache for LLM responses (Task 13)
- FIFO cache for TTS audio segments
- TTL-based cache invalidation
"""

import logging
import time
import hashlib
from typing import Dict, Optional, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple in-memory LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        logger.info("LRUCache initialized: max_size=%d, ttl=%ds", max_size, ttl_seconds)

    def _make_key(self, *args, **kwargs) -> str:
        """Create a hash key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if present and not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        # Check TTL
        if time.time() - entry["created_at"] > self.ttl_seconds:
            del self._cache[key]
            logger.debug("Cache entry expired: %s", key[:8])
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        logger.debug("Cache hit: %s", key[:8])
        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        """Store value in cache."""
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug("Cache evicted: %s", oldest_key[:8])
        
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
        }
        self._cache.move_to_end(key)
        logger.debug("Cache stored: %s", key[:8])

    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self._cache) / self.max_size,
        }


class FIFOCache:
    """Simple in-memory FIFO cache for audio/data blobs."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        logger.info("FIFOCache initialized: max_size=%d, ttl=%ds", max_size, ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """Get value if present and not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if time.time() - entry["created_at"] > self.ttl_seconds:
            del self._cache[key]
            return None
        
        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        """Store value, evicting oldest if at capacity."""
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
        }

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization": len(self._cache) / self.max_size,
        }


class CacheManager:
    """
    Unified cache manager for the voice order system.
    
    Provides separate caches for:
    - LLM responses (LRU, frequent reuse)
    - TTS audio (FIFO, large blobs)
    """

    def __init__(
        self,
        llm_cache_size: int = 1000,
        tts_cache_size: int = 500,
        cache_ttl_seconds: int = 3600,
    ):
        self.llm_cache = LRUCache(max_size=llm_cache_size, ttl_seconds=cache_ttl_seconds)
        self.tts_cache = FIFOCache(max_size=tts_cache_size, ttl_seconds=cache_ttl_seconds * 24)
        logger.info("CacheManager initialized")

    def get_llm_cache_key(self, text: str, model: str, context: Optional[Any] = None) -> str:
        """Generate cache key for LLM request."""
        key_data = f"{model}:{text}"
        if context:
            key_data += f":{str(context)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get_tts_cache_key(self, text: str, language: str, voice: Optional[str] = None) -> str:
        """Generate cache key for TTS request."""
        key_data = f"{language}:{voice or 'default'}:{text}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def cache_llm_response(self, key: str, response: Any) -> None:
        """Cache an LLM response."""
        self.llm_cache.set(key, response)

    def get_cached_llm_response(self, key: str) -> Optional[Any]:
        """Retrieve cached LLM response."""
        return self.llm_cache.get(key)

    def cache_tts_audio(self, key: str, audio_bytes: bytes) -> None:
        """Cache TTS audio bytes."""
        self.tts_cache.set(key, audio_bytes)

    def get_cached_tts_audio(self, key: str) -> Optional[bytes]:
        """Retrieve cached TTS audio."""
        return self.tts_cache.get(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        return {
            "llm_cache": self.llm_cache.get_stats(),
            "tts_cache": self.tts_cache.get_stats(),
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self.llm_cache.clear()
        self.tts_cache.clear()
        logger.info("All caches cleared")

