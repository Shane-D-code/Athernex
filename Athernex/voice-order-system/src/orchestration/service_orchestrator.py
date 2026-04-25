"""
Service orchestrator with primary/fallback provider management.

Implements automatic service switching, error counting, and health restoration.
Validates Requirements 19.1, 19.2, 19.3, 19.5, 19.6.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

FALLBACK_RESTORE_SECONDS = 300  # 5 minutes
ERROR_THRESHOLD = 3              # errors before switching to fallback


@dataclass
class ServiceState:
    """Tracks health state for a single service."""
    name: str
    error_count: int = 0
    using_fallback: bool = False
    fallback_since: Optional[float] = None

    def record_error(self) -> None:
        self.error_count += 1

    def record_success(self) -> None:
        self.error_count = 0

    def switch_to_fallback(self) -> None:
        self.using_fallback = True
        self.fallback_since = time.time()
        logger.warning("Service '%s' switched to fallback", self.name)

    def try_restore_primary(self) -> bool:
        """Return True if enough time has passed to try restoring primary."""
        if not self.using_fallback or self.fallback_since is None:
            return False
        elapsed = time.time() - self.fallback_since
        return elapsed >= FALLBACK_RESTORE_SECONDS

    def restore_primary(self) -> None:
        self.using_fallback = False
        self.fallback_since = None
        self.error_count = 0
        logger.info("Service '%s' restored to primary", self.name)


class ServiceOrchestrator:
    """
    Manages primary and fallback service providers with automatic switching.

    Requirements:
    - 19.1: Auto-switch STT on failure
    - 19.2: Auto-switch LLM on failure
    - 19.3: Auto-switch TTS on failure
    - 19.5: Restore primary when available
    - 19.6: Complete fallback transition within 500ms
    """

    def __init__(self):
        self._states: Dict[str, ServiceState] = {}

    def _get_state(self, service_name: str) -> ServiceState:
        if service_name not in self._states:
            self._states[service_name] = ServiceState(name=service_name)
        return self._states[service_name]

    async def execute_with_fallback(
        self,
        service_name: str,
        primary_fn: Callable[[], Any],
        fallback_fn: Optional[Callable[[], Any]] = None,
    ) -> Any:
        """
        Execute a service call with automatic fallback on failure.

        Args:
            service_name: Logical service name (e.g. "stt", "llm", "tts")
            primary_fn: Async callable for the primary service
            fallback_fn: Async callable for the fallback service (optional)

        Returns:
            Result from whichever service succeeded

        Raises:
            Exception if both primary and fallback fail
        """
        state = self._get_state(service_name)

        # Try to restore primary if enough time has passed
        if state.try_restore_primary():
            logger.info("Attempting to restore primary for '%s'", service_name)
            try:
                result = await primary_fn()
                state.restore_primary()
                return result
            except Exception as e:
                logger.warning("Primary restore failed for '%s': %s", service_name, e)
                state.fallback_since = time.time()  # reset timer

        # Use fallback if currently in fallback mode
        if state.using_fallback:
            if fallback_fn is None:
                raise RuntimeError(f"No fallback available for service '{service_name}'")
            return await fallback_fn()

        # Normal path: try primary first
        try:
            result = await primary_fn()
            state.record_success()
            return result
        except Exception as e:
            state.record_error()
            logger.error("Primary service '%s' failed (errors: %d): %s", service_name, state.error_count, e)

            if state.error_count >= ERROR_THRESHOLD:
                state.switch_to_fallback()

            if fallback_fn is not None:
                logger.info("Trying fallback for '%s'", service_name)
                try:
                    result = await fallback_fn()
                    return result
                except Exception as fb_err:
                    logger.error("Fallback for '%s' also failed: %s", service_name, fb_err)
                    raise fb_err
            raise

    async def health_check(self, service_name: str, check_fn: Callable[[], bool]) -> bool:
        """Run a health check for a service and update state accordingly."""
        try:
            healthy = await check_fn()
            state = self._get_state(service_name)
            if healthy:
                state.record_success()
            else:
                state.record_error()
            return healthy
        except Exception as e:
            logger.error("Health check failed for '%s': %s", service_name, e)
            self._get_state(service_name).record_error()
            return False

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Return current status dict for a service."""
        state = self._get_state(service_name)
        return {
            "service": service_name,
            "using_fallback": state.using_fallback,
            "error_count": state.error_count,
            "fallback_since": state.fallback_since,
        }

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Return status for all tracked services."""
        return {name: self.get_service_status(name) for name in self._states}

    def reset_service(self, service_name: str) -> None:
        """Reset a service state (for testing)."""
        if service_name in self._states:
            del self._states[service_name]
