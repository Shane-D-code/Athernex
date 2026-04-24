"""
Service Orchestrator with fallback logic, rate limiting, and retry strategy.

Manages primary and fallback services for STT, LLM, and TTS.
Implements circuit breaker pattern and health-aware routing.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum

from stt.base import STTEngine, TranscriptionResult
from llm.base import LLMProcessor, LLMResponse
from tts.base import TTSEngine, SynthesisResult

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceHealth(str, Enum):
    """Health status of a service."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ServiceInstance:
    """Wrapper for a service with health tracking."""
    name: str
    service: Any
    priority: int  # Lower = higher priority
    health: ServiceHealth = ServiceHealth.HEALTHY
    last_check: float = 0.0
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_latency: float = 0.0

    @property
    def is_available(self) -> bool:
        return self.health != ServiceHealth.UNHEALTHY

    def record_success(self, latency: float):
        self.consecutive_failures = 0
        self.total_requests += 1
        # Exponential moving average for latency
        self.avg_latency = 0.9 * self.avg_latency + 0.1 * latency if self.avg_latency > 0 else latency

    def record_failure(self):
        self.consecutive_failures += 1
        self.total_requests += 1
        self.failed_requests += 1
        if self.consecutive_failures >= 3:
            self.health = ServiceHealth.UNHEALTHY
        elif self.consecutive_failures >= 1:
            self.health = ServiceHealth.DEGRADED


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int):
        self.tokens = float(requests_per_minute)
        self.max_tokens = float(requests_per_minute)
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        logger.info("RateLimiter: %d requests/minute", requests_per_minute)

    async def acquire(self) -> bool:
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            # Replenish tokens (per minute)
            self.tokens = min(self.max_tokens, self.tokens + elapsed * (self.max_tokens / 60.0))
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    async def wait_for_token(self, timeout: float = 30.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        return False


class ServiceOrchestrator:
    """
    Orchestrates STT, LLM, and TTS services with automatic fallbacks.
    
    Features:
    - Priority-based service selection
    - Health checks and circuit breaker
    - Rate limiting per service
    - Retry with exponential backoff
    - Latency tracking
    """

    def __init__(
        self,
        stt_engines: List[STTEngine],
        llm_processors: List[LLMProcessor],
        tts_engines: List[TTSEngine],
        rate_limits: Optional[Dict[str, int]] = None,
    ):
        self.stt_instances: List[ServiceInstance] = []
        self.llm_instances: List[ServiceInstance] = []
        self.tts_instances: List[ServiceInstance] = []
        self.rate_limiters: Dict[str, RateLimiter] = {}

        rate_limits = rate_limits or {}

        # Register STT engines
        for i, engine in enumerate(stt_engines):
            instance = ServiceInstance(
                name=engine.name,
                service=engine,
                priority=i,
            )
            self.stt_instances.append(instance)
            self.rate_limiters[engine.name] = RateLimiter(
                rate_limits.get("stt", 60)
            )

        # Register LLM processors
        for i, processor in enumerate(llm_processors):
            instance = ServiceInstance(
                name=processor.name,
                service=processor,
                priority=i,
            )
            self.llm_instances.append(instance)
            self.rate_limiters[processor.name] = RateLimiter(
                rate_limits.get("llm", 10)
            )

        # Register TTS engines
        for i, engine in enumerate(tts_engines):
            instance = ServiceInstance(
                name=engine.name,
                service=engine,
                priority=i,
            )
            self.tts_instances.append(instance)
            self.rate_limiters[engine.name] = RateLimiter(
                rate_limits.get("tts", 60)
            )

        logger.info(
            "ServiceOrchestrator initialized: %d STT, %d LLM, %d TTS",
            len(self.stt_instances), len(self.llm_instances), len(self.tts_instances)
        )

    def _get_available_instances(self, instances: List[ServiceInstance]) -> List[ServiceInstance]:
        """Get instances sorted by priority, filtering out unhealthy."""
        available = [inst for inst in instances if inst.is_available]
        return sorted(available, key=lambda x: (x.priority, x.avg_latency))

    async def _execute_with_fallback(
        self,
        instances: List[ServiceInstance],
        operation: str,
        *args,
        max_retries: int = 2,
        **kwargs
    ) -> Any:
        """Execute operation on best available instance with fallback."""
        available = self._get_available_instances(instances)
        
        if not available:
            # Try to revive unhealthy instances as last resort
            available = sorted(instances, key=lambda x: x.priority)
            logger.warning("All services unhealthy, trying degraded instances")

        last_error = None
        
        for instance in available:
            # Rate limiting
            limiter = self.rate_limiters.get(instance.name)
            if limiter and not await limiter.wait_for_token(timeout=5.0):
                logger.warning("Rate limit exceeded for %s", instance.name)
                continue

            # Retry loop
            for attempt in range(max_retries + 1):
                try:
                    start = time.time()
                    service = instance.service
                    
                    # Call the appropriate method based on operation
                    if operation == "transcribe":
                        result = await service.transcribe(*args, **kwargs)
                    elif operation == "process_utterance":
                        result = await service.process_utterance(*args, **kwargs)
                    elif operation == "synthesize":
                        result = await service.synthesize(*args, **kwargs)
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                    
                    latency = time.time() - start
                    instance.record_success(latency)
                    instance.health = ServiceHealth.HEALTHY
                    logger.debug("%s succeeded on %s (%.2fs)", operation, instance.name, latency)
                    return result
                    
                except Exception as e:
                    latency = time.time() - start
                    instance.record_failure()
                    last_error = e
                    logger.warning(
                        "%s failed on %s (attempt %d/%d): %s",
                        operation, instance.name, attempt + 1, max_retries + 1, e
                    )
                    
                    if attempt < max_retries:
                        wait = 2 ** attempt  # Exponential backoff
                        await asyncio.sleep(wait)

        # All instances failed
        raise RuntimeError(f"All services failed for {operation}: {last_error}")

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio with automatic fallback."""
        return await self._execute_with_fallback(
            self.stt_instances, "transcribe", audio_bytes, sample_rate=sample_rate
        )

    async def process_utterance(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Process utterance with LLM fallback."""
        return await self._execute_with_fallback(
            self.llm_instances, "process_utterance", text, context=context
        )

    async def synthesize(
        self, text: str, language: str = "en", voice: Optional[str] = None
    ) -> SynthesisResult:
        """Synthesize speech with TTS fallback."""
        return await self._execute_with_fallback(
            self.tts_instances, "synthesize", text, language=language, voice=voice
        )

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all services."""
        results = {"stt": {}, "llm": {}, "tts": {}}
        
        async def check_instance(instance: ServiceInstance, category: str):
            try:
                healthy = await instance.service.health_check()
                instance.health = ServiceHealth.HEALTHY if healthy else ServiceHealth.UNHEALTHY
                instance.last_check = time.time()
                results[category][instance.name] = {
                    "status": instance.health.value,
                    "healthy": healthy,
                    "avg_latency": instance.avg_latency,
                    "total_requests": instance.total_requests,
                    "failed_requests": instance.failed_requests,
                }
            except Exception as e:
                instance.health = ServiceHealth.UNHEALTHY
                results[category][instance.name] = {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": str(e),
                }

        tasks = []
        for inst in self.stt_instances:
            tasks.append(check_instance(inst, "stt"))
        for inst in self.llm_instances:
            tasks.append(check_instance(inst, "llm"))
        for inst in self.tts_instances:
            tasks.append(check_instance(inst, "tts"))

        await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        def inst_stats(instances):
            return [
                {
                    "name": i.name,
                    "health": i.health.value,
                    "priority": i.priority,
                    "total_requests": i.total_requests,
                    "failed_requests": i.failed_requests,
                    "avg_latency": i.avg_latency,
                }
                for i in instances
            ]

        return {
            "stt": inst_stats(self.stt_instances),
            "llm": inst_stats(self.llm_instances),
            "tts": inst_stats(self.tts_instances),
        }

    async def close_all(self):
        """Close all service connections."""
        for inst in self.stt_instances + self.llm_instances + self.tts_instances:
            if hasattr(inst.service, 'close'):
                try:
                    await inst.service.close()
                except Exception as e:
                    logger.warning("Error closing %s: %s", inst.name, e)

