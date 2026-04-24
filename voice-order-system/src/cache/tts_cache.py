"""
TTS audio cache with FIFO eviction and TTL expiration.

Validates Requirements 20.2, 20.4, 20.5.
"""

import logging
import time
import zlib
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger(__name__)


class TTSCache:
    """
    FIFO cache for TTS audio outputs keyed by language:voice:text.

    Requirements:
    - 20.2: Cache identical text responses within 1 hour
    - 20.4: Cache up to 500 most recent audio outputs
    - 20.5: Reduce latency by at least 50% on cache hit
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # OrderedDict preserves insertion order for FIFO eviction
        self._cache: OrderedDict[str, tuple[bytes, float]] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0

    @staticmethod
    def _make_key(language: str, voice: str, text: str) -> str:
        return f"{language}:{voice}:{text}"

    def get(self, language: str, voice: str, text: str) -> Optional[bytes]:
        """Return cached audio bytes, or None if missing/expired."""
        key = self._make_key(language, voice, text)
        entry = self._cache.get(key)
        if entry is None:
            self._miss_count += 1
            return None

        compressed, expires_at = entry
        if time.time() > expires_at:
            del self._cache[key]
            self._miss_count += 1
            return None

        self._hit_count += 1
        logger.debug("TTS cache hit for '%s:%s'", language, voice)
        return zlib.decompress(compressed)

    def put(self, language: str, voice: str, text: str, audio: bytes) -> None:
        """Store audio bytes in the cache (compressed)."""
        key = self._make_key(language, voice, text)
        compressed = zlib.compress(audio, level=1)  # fast compression
        expires_at = time.time() + self.ttl_seconds

        if key in self._cache:
            del self._cache[key]  # remove to re-insert at end (refresh)

        self._cache[key] = (compressed, expires_at)

        # FIFO eviction: remove oldest entry
        while len(self._cache) > self.max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("TTS cache evicted key: %s", evicted_key[:40])

    def invalidate(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("TTS cache invalidated")

    @property
    def hit_count(self) -> int:
        return self._hit_count

    @property
    def miss_count(self) -> int:
        return self._miss_count

    @property
    def size(self) -> int:
        return len(self._cache)
