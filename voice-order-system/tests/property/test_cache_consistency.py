"""
Property 7: Cache consistency

Validates Requirements 20.1, 20.2.

Properties tested:
- Cached LLM results are identical to the original result
- Cached TTS audio is identical to the original audio
- Cache invalidation removes all entries
- TTL expiration removes stale entries
"""

import time
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cache.llm_cache import LLMCache
from cache.tts_cache import TTSCache


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

text_st = st.text(min_size=1, max_size=200).filter(lambda t: t.strip())
language_st = st.sampled_from(["en", "hi", "kn", "mr"])
voice_st = st.sampled_from(["default", "hi-IN-SwaraNeural", "en-IN-NeerjaNeural"])
audio_st = st.binary(min_size=100, max_size=4096)
response_st = st.fixed_dictionaries({
    "intent": st.sampled_from(["place_order", "modify_order", "cancel_order"]),
    "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
})


# ---------------------------------------------------------------------------
# LLM Cache properties
# ---------------------------------------------------------------------------

class TestLLMCacheConsistency:

    @given(text=text_st, response=response_st)
    def test_cached_result_equals_original(self, text, response):
        """Property: get() after put() returns the same object."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        cache.put(text, response)
        result = cache.get(text)
        assert result == response

    @given(text=text_st, response=response_st)
    def test_cache_miss_returns_none(self, text, response):
        """Property: get() on empty cache always returns None."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        assert cache.get(text) is None

    @given(text=text_st, response=response_st)
    def test_invalidation_clears_all_entries(self, text, response):
        """Property: after invalidate(), all gets return None."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        cache.put(text, response)
        cache.invalidate()
        assert cache.get(text) is None
        assert cache.size == 0

    @given(texts=st.lists(text_st, min_size=2, max_size=10, unique=True),
           response=response_st)
    def test_lru_eviction_respects_max_size(self, texts, response):
        """Property: cache never exceeds max_size."""
        max_size = max(1, len(texts) // 2)
        cache = LLMCache(max_size=max_size, ttl_seconds=3600)
        for text in texts:
            cache.put(text, response)
        assert cache.size <= max_size

    def test_ttl_expiration_removes_entry(self):
        """Property: entries expire after TTL."""
        cache = LLMCache(max_size=100, ttl_seconds=1)
        cache.put("hello world", {"intent": "place_order"})
        assert cache.get("hello world") is not None
        time.sleep(1.1)
        assert cache.get("hello world") is None

    @given(text=text_st, r1=response_st, r2=response_st)
    def test_put_overwrites_existing_entry(self, text, r1, r2):
        """Property: second put() for same key returns latest value."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        cache.put(text, r1)
        cache.put(text, r2)
        assert cache.get(text) == r2


# ---------------------------------------------------------------------------
# TTS Cache properties
# ---------------------------------------------------------------------------

class TestTTSCacheConsistency:

    @given(language=language_st, voice=voice_st, text=text_st, audio=audio_st)
    def test_cached_audio_equals_original(self, language, voice, text, audio):
        """Property: get() after put() returns identical audio bytes."""
        cache = TTSCache(max_size=100, ttl_seconds=3600)
        cache.put(language, voice, text, audio)
        result = cache.get(language, voice, text)
        assert result == audio

    @given(language=language_st, voice=voice_st, text=text_st)
    def test_cache_miss_returns_none(self, language, voice, text):
        """Property: get() on empty cache returns None."""
        cache = TTSCache(max_size=100, ttl_seconds=3600)
        assert cache.get(language, voice, text) is None

    @given(language=language_st, voice=voice_st, text=text_st, audio=audio_st)
    def test_invalidation_clears_all_entries(self, language, voice, text, audio):
        """Property: after invalidate(), all gets return None."""
        cache = TTSCache(max_size=100, ttl_seconds=3600)
        cache.put(language, voice, text, audio)
        cache.invalidate()
        assert cache.get(language, voice, text) is None
        assert cache.size == 0

    @given(entries=st.lists(
        st.tuples(language_st, voice_st, text_st, audio_st),
        min_size=2, max_size=10,
    ))
    def test_fifo_eviction_respects_max_size(self, entries):
        """Property: cache never exceeds max_size."""
        max_size = max(1, len(entries) // 2)
        cache = TTSCache(max_size=max_size, ttl_seconds=3600)
        for lang, voice, text, audio in entries:
            cache.put(lang, voice, text, audio)
        assert cache.size <= max_size

    def test_ttl_expiration_removes_entry(self):
        """Property: entries expire after TTL."""
        cache = TTSCache(max_size=100, ttl_seconds=1)
        cache.put("en", "default", "hello", b"\x00" * 200)
        assert cache.get("en", "default", "hello") is not None
        time.sleep(1.1)
        assert cache.get("en", "default", "hello") is None

    @given(language=language_st, voice=voice_st, text=text_st,
           audio1=audio_st, audio2=audio_st)
    def test_put_overwrites_existing_entry(self, language, voice, text, audio1, audio2):
        """Property: second put() for same key returns latest audio."""
        cache = TTSCache(max_size=100, ttl_seconds=3600)
        cache.put(language, voice, text, audio1)
        cache.put(language, voice, text, audio2)
        assert cache.get(language, voice, text) == audio2
