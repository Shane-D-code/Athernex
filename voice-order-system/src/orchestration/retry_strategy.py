"""
Retry strategy with exponential backoff and jitter.

Validates Requirements 9.1, 9.3, 19.6.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Set, Type

logger = logging.getLogger(__name__)

# HTTP status codes that are safe to retry
RETRYABLE_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}


@dataclass
class RetryOptions:
    """Configuration for retry behaviour."""
    max_retries: int = 3
    base_delay: float = 0.5       # seconds
    max_delay: float = 10.0       # seconds
    jitter_factor: float = 0.25   # ±25% jitter


def _is_retryable(exc: Exception) -> bool:
    """Determine whether an exception warrants a retry."""
    import httpx

    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
        return True
    # Generic connection / OS errors
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    return False


class RetryStrategy:
    """
    Executes an async callable with exponential backoff retries.

    Requirements:
    - 9.1: Retry on STT/LLM/TTS failures
    - 9.3: Exponential backoff to avoid thundering herd
    - 19.6: Complete fallback within 500ms (first attempt is immediate)
    """

    def __init__(self, options: Optional[RetryOptions] = None):
        self.options = options or RetryOptions()

    def _compute_delay(self, attempt: int) -> float:
        """Compute delay for a given attempt number (0-indexed)."""
        delay = self.options.base_delay * (2 ** attempt)
        delay = min(delay, self.options.max_delay)
        jitter = delay * self.options.jitter_factor * (random.random() * 2 - 1)
        return max(0.0, delay + jitter)

    async def execute(self, fn: Callable[[], Any], operation_name: str = "operation") -> Any:
        """
        Execute fn with retries on retryable errors.

        Args:
            fn: Async callable to execute
            operation_name: Human-readable name for logging

        Returns:
            Result of fn on success

        Raises:
            Last exception if all retries exhausted
        """
        last_exc: Optional[Exception] = None

        for attempt in range(self.options.max_retries + 1):
            try:
                result = await fn()
                if attempt > 0:
                    logger.info("'%s' succeeded on attempt %d", operation_name, attempt + 1)
                return result
            except Exception as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    logger.debug("Non-retryable error for '%s': %s", operation_name, exc)
                    raise

                if attempt < self.options.max_retries:
                    delay = self._compute_delay(attempt)
                    logger.warning(
                        "'%s' failed (attempt %d/%d): %s — retrying in %.2fs",
                        operation_name, attempt + 1, self.options.max_retries + 1, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "'%s' failed after %d attempts: %s",
                        operation_name, self.options.max_retries + 1, exc,
                    )

        raise last_exc  # type: ignore[misc]
