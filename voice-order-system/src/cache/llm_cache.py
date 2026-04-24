"""
LLM response cache with LRU eviction and TTL expiration.

Validates Requirements 20.1, 20.3, 20.5.
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LLMCache:
    """
    LRU cache for LLM responses keyed by SHA-256 of the input text.

    Requirements:
    - 20.1: Cache identical transcribed text within 1 hour
    - 20.3: Cache up to 1000 most recent responses
    - 20.5: Reduce latency by at least 50% on cache hit
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0

    @staticmethod
    def _make_key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[Any]:
        """Return cached response for text, or None if missing/expired."""
        key = self._make_key(text)
        entry = self._cache.get(key)
        if entry is None:
            self._miss_count += 1
            return None

        value, expires_at = entry
        if time.time() > expires_at:
            del self._cache[key]
            self._miss_count += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hit_count += 1
        logger.debug("LLM cache hit for key %s…", key[:8])
        return value

    def put(self, text: str, response: Any) -> None:
        """Store a response in the cache."""
        key = self._make_key(text)
        expires_at = time.time() + self.ttl_seconds

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (response, expires_at)

        # Evict oldest entry if over capacity
        while len(self._cache) > self.max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("LLM cache evicted key %s…", evicted_key[:8])

    def invalidate(self) -> None:
        """Clear all cache entries (e.g. on config change)."""
        self._cache.clear()
        logger.info("LLM cache invalidated")

    @property
    def hit_count(self) -> int:
        return self._hit_count

    @property
    def miss_count(self) -> int:
        return self._miss_count

    @property
    def size(self) -> int:
        return len(self._cache)
