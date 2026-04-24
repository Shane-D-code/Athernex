"""
MetricsCollector — Task 18.2
Tracks latency percentiles, error rates, cache hits, and request counts.
Thread-safe, in-memory, Prometheus-compatible export.
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import statistics


@dataclass
class RequestMetric:
    session_id: str
    timestamp: float
    stt_ms: float
    llm_ms: float
    confidence_ms: float
    tts_ms: float
    total_ms: float
    language: str
    intent: Optional[str]
    clarification_needed: bool
    error: Optional[str]


class MetricsCollector:
    """
    Collects and aggregates runtime metrics for the voice pipeline.
    Keeps a rolling window of the last 1000 requests.
    Thread-safe via a single lock.
    """

    MAX_HISTORY = 1000

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: deque = deque(maxlen=self.MAX_HISTORY)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._intent_counts: Dict[str, int] = defaultdict(int)
        self._language_counts: Dict[str, int] = defaultdict(int)
        self._cache_hits: Dict[str, int] = defaultdict(int)   # llm / tts
        self._cache_total: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
        self._total_requests = 0

    # ── Record ─────────────────────────────────────────────────────────────

    def record_request(
        self,
        session_id: str,
        stt_ms: float,
        llm_ms: float,
        confidence_ms: float,
        tts_ms: float,
        total_ms: float,
        language: str = "en",
        intent: Optional[str] = None,
        clarification_needed: bool = False,
        error: Optional[str] = None,
    ):
        m = RequestMetric(
            session_id=session_id,
            timestamp=time.time(),
            stt_ms=stt_ms,
            llm_ms=llm_ms,
            confidence_ms=confidence_ms,
            tts_ms=tts_ms,
            total_ms=total_ms,
            language=language,
            intent=intent,
            clarification_needed=clarification_needed,
            error=error,
        )
        with self._lock:
            self._requests.append(m)
            self._total_requests += 1
            if error:
                self._error_counts["pipeline"] += 1
            if intent:
                self._intent_counts[intent] += 1
            self._language_counts[language] += 1

    def record_cache_event(self, cache_type: str, hit: bool):
        """Record a cache hit or miss for 'llm' or 'tts'."""
        with self._lock:
            self._cache_total[cache_type] += 1
            if hit:
                self._cache_hits[cache_type] += 1

    def record_error(self, component: str):
        with self._lock:
            self._error_counts[component] += 1

    # ── Compute ────────────────────────────────────────────────────────────

    def _percentiles(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        s = sorted(values)
        def p(pct):
            idx = max(0, int(len(s) * pct / 100) - 1)
            return round(s[idx], 1)
        return {"p50": p(50), "p95": p(95), "p99": p(99), "avg": round(statistics.mean(s), 1)}

    def get_summary(self) -> dict:
        with self._lock:
            reqs = list(self._requests)

        if not reqs:
            return self._empty_summary()

        total = [r.total_ms for r in reqs]
        stt   = [r.stt_ms   for r in reqs]
        llm   = [r.llm_ms   for r in reqs]
        tts   = [r.tts_ms   for r in reqs]
        errors = sum(1 for r in reqs if r.error)
        clarifications = sum(1 for r in reqs if r.clarification_needed)

        uptime_s = round(time.time() - self._start_time)

        cache_summary = {}
        with self._lock:
            for k in self._cache_total:
                total_c = self._cache_total[k]
                hits_c  = self._cache_hits[k]
                cache_summary[k] = {
                    "hit_rate": round(hits_c / total_c, 3) if total_c else 0.0,
                    "hits": hits_c,
                    "total": total_c,
                }

        return {
            "uptime_seconds": uptime_s,
            "total_requests": self._total_requests,
            "window_size": len(reqs),
            "error_rate": round(errors / len(reqs), 3),
            "clarification_rate": round(clarifications / len(reqs), 3),
            "latency_ms": {
                "total":      self._percentiles(total),
                "stt":        self._percentiles(stt),
                "llm":        self._percentiles(llm),
                "tts":        self._percentiles(tts),
            },
            "intents": dict(self._intent_counts),
            "languages": dict(self._language_counts),
            "errors_by_component": dict(self._error_counts),
            "cache": cache_summary,
        }

    def _empty_summary(self) -> dict:
        return {
            "uptime_seconds": round(time.time() - self._start_time),
            "total_requests": 0,
            "window_size": 0,
            "error_rate": 0.0,
            "clarification_rate": 0.0,
            "latency_ms": {},
            "intents": {},
            "languages": {},
            "errors_by_component": {},
            "cache": {},
        }

    def prometheus_text(self) -> str:
        """Export metrics in Prometheus text format."""
        s = self.get_summary()
        lines = [
            "# HELP athernex_requests_total Total pipeline requests",
            "# TYPE athernex_requests_total counter",
            f"athernex_requests_total {s['total_requests']}",
            "",
            "# HELP athernex_error_rate Pipeline error rate (0-1)",
            "# TYPE athernex_error_rate gauge",
            f"athernex_error_rate {s['error_rate']}",
            "",
            "# HELP athernex_clarification_rate Clarification trigger rate",
            "# TYPE athernex_clarification_rate gauge",
            f"athernex_clarification_rate {s['clarification_rate']}",
            "",
            "# HELP athernex_uptime_seconds Server uptime",
            "# TYPE athernex_uptime_seconds counter",
            f"athernex_uptime_seconds {s['uptime_seconds']}",
            "",
        ]
        lat = s.get("latency_ms", {})
        for component, perc in lat.items():
            for pname, val in perc.items():
                lines.append(f'athernex_latency_ms{{component="{component}",quantile="{pname}"}} {val}')
        lines.append("")
        for intent, count in s.get("intents", {}).items():
            lines.append(f'athernex_intent_total{{intent="{intent}"}} {count}')
        lines.append("")
        for lang, count in s.get("languages", {}).items():
            lines.append(f'athernex_language_total{{language="{lang}"}} {count}')
        return "\n".join(lines) + "\n"


# Singleton
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
