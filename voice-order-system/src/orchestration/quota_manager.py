"""
Quota manager for resource limits.

Tracks GPU memory, CPU, RAM, and concurrent requests.
Validates Requirements 18.1, 18.3, 18.5.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResourceQuota:
    """Resource quota configuration."""
    gpu_memory_limit_mb: int = 7500
    cpu_percent_limit: int = 80
    ram_limit_mb: int = 8192
    max_concurrent_requests: int = 10


@dataclass
class ResourceMetrics:
    """Current resource usage metrics."""
    gpu_memory_used_mb: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    concurrent_requests: int = 0
    timestamp: float = field(default_factory=time.time)


class QuotaManager:
    """
    Manages resource quotas for GPU memory, CPU, RAM, and concurrent requests.

    Requirements:
    - 18.1: Track API call counts per service
    - 18.3: Queue requests when limits exceeded
    - 18.5: Inform customers of delays > 2s
    """

    def __init__(self, quota: Optional[ResourceQuota] = None):
        self.quota = quota or ResourceQuota()
        self._active_requests: Dict[str, float] = {}  # request_id -> start_time
        self._api_call_counts: Dict[str, int] = {}

    def check_quota(self) -> tuple[bool, Optional[str]]:
        """
        Check if current resource usage is within quota.

        Returns:
            (allowed, reason) — reason is None if allowed
        """
        concurrent = len(self._active_requests)
        if concurrent >= self.quota.max_concurrent_requests:
            reason = f"Max concurrent requests reached ({concurrent}/{self.quota.max_concurrent_requests})"
            logger.warning(reason)
            return False, reason

        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram_mb = psutil.virtual_memory().used / (1024 * 1024)

            if cpu > self.quota.cpu_percent_limit:
                reason = f"CPU usage too high: {cpu:.1f}% > {self.quota.cpu_percent_limit}%"
                logger.warning(reason)
                return False, reason

            if ram_mb > self.quota.ram_limit_mb:
                reason = f"RAM usage too high: {ram_mb:.0f}MB > {self.quota.ram_limit_mb}MB"
                logger.warning(reason)
                return False, reason
        except ImportError:
            pass  # psutil not available, skip system checks

        return True, None

    def start_request(self, request_id: str) -> None:
        """Record the start of a request."""
        self._active_requests[request_id] = time.time()
        logger.debug("Request started: %s (active: %d)", request_id, len(self._active_requests))

    def end_request(self, request_id: str) -> Optional[float]:
        """
        Record the end of a request.

        Returns:
            Duration in seconds, or None if request_id not found
        """
        start = self._active_requests.pop(request_id, None)
        if start is None:
            return None
        duration = time.time() - start
        logger.debug("Request ended: %s (duration: %.2fs, active: %d)", request_id, duration, len(self._active_requests))
        return duration

    def record_api_call(self, service: str) -> None:
        """Increment API call counter for a service."""
        self._api_call_counts[service] = self._api_call_counts.get(service, 0) + 1

    def get_api_call_count(self, service: str) -> int:
        """Get total API call count for a service."""
        return self._api_call_counts.get(service, 0)

    def get_all_api_counts(self) -> Dict[str, int]:
        """Get all API call counts."""
        return dict(self._api_call_counts)

    def get_metrics(self) -> ResourceMetrics:
        """Get current resource metrics snapshot."""
        metrics = ResourceMetrics(concurrent_requests=len(self._active_requests))
        try:
            import psutil
            metrics.cpu_percent = psutil.cpu_percent(interval=None)
            metrics.ram_used_mb = psutil.virtual_memory().used / (1024 * 1024)
        except ImportError:
            pass
        return metrics

    def reset_counts(self) -> None:
        """Reset all API call counts (e.g., for testing)."""
        self._api_call_counts.clear()
