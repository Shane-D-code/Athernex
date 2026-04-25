"""
Unit tests for MetricsCollector — Task 18.2
"""
import time
import pytest
from monitoring.metrics_collector import MetricsCollector


@pytest.fixture
def mc():
    return MetricsCollector()


def _record(mc, n=5, error=False, intent="place_order", lang="hi"):
    for i in range(n):
        mc.record_request(
            session_id=f"sess-{i}",
            stt_ms=120.0, llm_ms=800.0, confidence_ms=5.0, tts_ms=300.0, total_ms=1250.0,
            language=lang, intent=intent,
            clarification_needed=False,
            error="oops" if error else None,
        )


def test_empty_summary(mc):
    s = mc.get_summary()
    assert s["total_requests"] == 0
    assert s["error_rate"] == 0.0


def test_records_count(mc):
    _record(mc, 10)
    s = mc.get_summary()
    assert s["total_requests"] == 10
    assert s["window_size"] == 10


def test_error_rate(mc):
    _record(mc, 8, error=False)
    _record(mc, 2, error=True)
    s = mc.get_summary()
    assert s["error_rate"] == pytest.approx(0.2, abs=0.01)


def test_latency_percentiles(mc):
    _record(mc, 20)
    s = mc.get_summary()
    lat = s["latency_ms"]
    assert "total" in lat
    assert lat["total"]["p50"] > 0
    assert lat["total"]["p95"] >= lat["total"]["p50"]


def test_intent_distribution(mc):
    _record(mc, 3, intent="place_order")
    _record(mc, 2, intent="cancel_order")
    s = mc.get_summary()
    assert s["intents"]["place_order"] == 3
    assert s["intents"]["cancel_order"] == 2


def test_language_distribution(mc):
    _record(mc, 4, lang="hi")
    _record(mc, 1, lang="en")
    s = mc.get_summary()
    assert s["languages"]["hi"] == 4
    assert s["languages"]["en"] == 1


def test_cache_hit_rate(mc):
    _record(mc, 1)  # need at least 1 request so summary window is non-empty
    mc.record_cache_event("llm", hit=True)
    mc.record_cache_event("llm", hit=True)
    mc.record_cache_event("llm", hit=False)
    s = mc.get_summary()
    assert s["cache"]["llm"]["hit_rate"] == pytest.approx(0.667, abs=0.01)


def test_prometheus_text(mc):
    _record(mc, 3)
    text = mc.prometheus_text()
    assert "athernex_requests_total" in text
    assert "athernex_error_rate" in text
    assert "athernex_latency_ms" in text


def test_max_window(mc):
    # Fill beyond MAX_HISTORY — should not grow unbounded
    for i in range(1100):
        mc.record_request(f"s{i}", 100, 500, 5, 200, 850)
    assert mc.get_summary()["window_size"] == MetricsCollector.MAX_HISTORY
