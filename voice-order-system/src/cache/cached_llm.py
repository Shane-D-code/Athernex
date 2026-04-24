"""
Cached wrapper for LLM processors.

Adds transparent LLM response caching with cache invalidation support.
Validates Requirements 20.1, 20.6.
"""

import logging
from typing import Any, Dict, List, Optional

from llm.base import LLMProcessor, LLMResponse
from .llm_cache import LLMCache

logger = logging.getLogger(__name__)


class CachedLLMProcessor(LLMProcessor):
    """
    Wraps any LLMProcessor with transparent caching.

    Cache key is the raw utterance text. Context is not included in the key
    so that cached responses are reused across sessions for identical text.
    """

    def __init__(self, processor: LLMProcessor, cache: Optional[LLMCache] = None):
        self._processor = processor
        self._cache = cache or LLMCache()

    @property
    def name(self) -> str:
        return f"Cached({self._processor.name})"

    async def process_utterance(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        # Only cache when there is no session-specific context
        if context is None:
            cached = self._cache.get(text)
            if cached is not None:
                logger.debug("LLM cache hit for text: '%s…'", text[:30])
                return cached

        response = await self._processor.process_utterance(text, context)

        if context is None:
            self._cache.put(text, response)

        return response

    async def health_check(self) -> bool:
        return await self._processor.health_check()

    async def add_intent(self, intent: str, examples: List[str]) -> bool:
        # Invalidate cache when intents change
        self._cache.invalidate()
        return await self._processor.add_intent(intent, examples)

    def invalidate_cache(self) -> None:
        self._cache.invalidate()
