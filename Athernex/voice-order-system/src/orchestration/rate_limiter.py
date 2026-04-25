"""
Rate limiter implementation for API service management.

This module provides sliding window rate limiting with per-service request tracking,
exponential backoff, and usage monitoring as specified in Requirements 18.1, 18.2, 18.4.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Supported service types for rate limiting."""
    WHISPER = "whisper"
    OLLAMA = "ollama" 
    PIPER = "piper"


@dataclass
class RateLimit:
    """Rate limit configuration for a service."""
    max_requests: int
    window_ms: int
    
    
@dataclass
class UsageStats:
    """Usage statistics for a service."""
    current_requests: int
    max_requests: int
    usage_percentage: float
    window_start_time: float
    

class RateLimiter:
    """
    Sliding window rate limiter with per-service request tracking.
    
    Implements sliding window algorithm to track requests within time windows
    and provides exponential backoff when limits are exceeded.
    
    Service Limits:
    - Whisper STT: 10 requests/minute
    - Ollama LLM: 5 requests/minute  
    - Piper TTS: 50 requests/minute
    """
    
    def __init__(self):
        """Initialize rate limiter with default service limits."""
        self.requests: Dict[str, List[float]] = {}
        self.limits: Dict[str, RateLimit] = {
            ServiceType.WHISPER.value: RateLimit(max_requests=10, window_ms=60000),  # 10/min
            ServiceType.OLLAMA.value: RateLimit(max_requests=5, window_ms=60000),    # 5/min
            ServiceType.PIPER.value: RateLimit(max_requests=50, window_ms=60000),    # 50/min
        }
        self._warning_threshold = 0.8  # Warn at 80% usage
        
    def check_limit(self, service: str) -> bool:
        """
        Check if service is within rate limit.
        
        Args:
            service: Service name (whisper, ollama, piper)
            
        Returns:
            True if request can proceed, False if rate limited
        """
        limit = self.limits.get(service)
        if not limit:
            logger.warning(f"No rate limit configured for service: {service}")
            return True
            
        now = time.time() * 1000  # Convert to milliseconds
        window_start = now - limit.window_ms
        
        # Get requests in current window
        service_requests = self.requests.get(service, [])
        service_requests = [t for t in service_requests if t > window_start]
        
        # Check if under limit
        if len(service_requests) >= limit.max_requests:
            logger.debug(f"Rate limit exceeded for {service}: {len(service_requests)}/{limit.max_requests}")
            return False
            
        # Record this request
        service_requests.append(now)
        self.requests[service] = service_requests
        
        # Check for warning threshold
        usage_pct = len(service_requests) / limit.max_requests
        if usage_pct >= self._warning_threshold:
            logger.warning(
                f"Rate limit warning for {service}: {usage_pct:.1%} usage "
                f"({len(service_requests)}/{limit.max_requests} requests)"
            )
            
        return True
        
    async def wait_for_slot(self, service: str, max_wait_seconds: float = 30.0) -> bool:
        """
        Wait for an available slot using exponential backoff.
        
        Args:
            service: Service name to wait for
            max_wait_seconds: Maximum time to wait before giving up
            
        Returns:
            True if slot became available, False if timed out
        """
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait_seconds:
            if self.check_limit(service):
                return True
                
            # Exponential backoff with jitter
            delay = min(0.1 * (2 ** attempt), 2.0)  # Max 2 second delay
            jitter = delay * 0.1 * (0.5 - time.time() % 1)  # ±10% jitter
            total_delay = delay + jitter
            
            logger.debug(f"Rate limited for {service}, waiting {total_delay:.2f}s (attempt {attempt + 1})")
            await asyncio.sleep(total_delay)
            attempt += 1
            
        logger.error(f"Timeout waiting for rate limit slot for {service} after {max_wait_seconds}s")
        return False
        
    def get_usage_percentage(self, service: str) -> float:
        """
        Get current usage percentage for a service.
        
        Args:
            service: Service name
            
        Returns:
            Usage percentage (0.0 to 100.0)
        """
        limit = self.limits.get(service)
        if not limit:
            return 0.0
            
        now = time.time() * 1000
        window_start = now - limit.window_ms
        service_requests = self.requests.get(service, [])
        active_requests = [t for t in service_requests if t > window_start]
        
        return (len(active_requests) / limit.max_requests) * 100.0
        
    def get_usage_stats(self, service: str) -> Optional[UsageStats]:
        """
        Get detailed usage statistics for a service.
        
        Args:
            service: Service name
            
        Returns:
            UsageStats object or None if service not configured
        """
        limit = self.limits.get(service)
        if not limit:
            return None
            
        now = time.time() * 1000
        window_start = now - limit.window_ms
        service_requests = self.requests.get(service, [])
        active_requests = [t for t in service_requests if t > window_start]
        
        return UsageStats(
            current_requests=len(active_requests),
            max_requests=limit.max_requests,
            usage_percentage=(len(active_requests) / limit.max_requests) * 100.0,
            window_start_time=window_start / 1000.0
        )
        
    def get_all_usage_stats(self) -> Dict[str, UsageStats]:
        """
        Get usage statistics for all configured services.
        
        Returns:
            Dictionary mapping service names to UsageStats
        """
        stats = {}
        for service in self.limits.keys():
            stats[service] = self.get_usage_stats(service)
        return stats
        
    def update_limits(self, service: str, max_requests: int, window_ms: int) -> None:
        """
        Update rate limits for a service.
        
        Args:
            service: Service name
            max_requests: Maximum requests allowed
            window_ms: Time window in milliseconds
        """
        self.limits[service] = RateLimit(max_requests=max_requests, window_ms=window_ms)
        logger.info(f"Updated rate limit for {service}: {max_requests} requests per {window_ms}ms")
        
    def reset_service_requests(self, service: str) -> None:
        """
        Reset request history for a service.
        
        Args:
            service: Service name to reset
        """
        if service in self.requests:
            del self.requests[service]
            logger.info(f"Reset request history for service: {service}")
            
    def cleanup_expired_requests(self) -> int:
        """
        Clean up expired request records to prevent memory leaks.
        
        Returns:
            Number of expired requests removed
        """
        now = time.time() * 1000
        total_removed = 0
        
        for service, limit in self.limits.items():
            if service in self.requests:
                window_start = now - limit.window_ms
                original_count = len(self.requests[service])
                self.requests[service] = [t for t in self.requests[service] if t > window_start]
                removed = original_count - len(self.requests[service])
                total_removed += removed
                
        if total_removed > 0:
            logger.debug(f"Cleaned up {total_removed} expired request records")
            
        return total_removed
        
    def is_service_available(self, service: str) -> Tuple[bool, Optional[float]]:
        """
        Check if service is available and estimate wait time if not.
        
        Args:
            service: Service name
            
        Returns:
            Tuple of (is_available, estimated_wait_seconds)
        """
        if self.check_limit(service):
            return True, None
            
        # Estimate wait time based on oldest request in window
        limit = self.limits.get(service)
        if not limit:
            return True, None
            
        service_requests = self.requests.get(service, [])
        if not service_requests:
            return True, None
            
        now = time.time() * 1000
        oldest_request = min(service_requests)
        window_end = oldest_request + limit.window_ms
        wait_time = max(0, (window_end - now) / 1000.0)
        
        return False, wait_time