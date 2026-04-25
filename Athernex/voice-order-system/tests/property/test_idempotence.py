"""
Property 8: Idempotence

Validates Requirement 12.9.

Property: Processing the same utterance multiple times through the
deterministic parts of the pipeline (LLM parsing, confidence scoring,
data merging) produces identical StructuredOrderData.

Since the actual LLM and STT services are external, we test idempotence
on the deterministic components:
- ConfidenceAnalyzer: same inputs → same outputs
- ClarificationManager._merge_data: same inputs → same merged data
- StructuredOrderData serialization: same data → same JSON
"""

import json
import sys
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm.base import StructuredOrderData, Intent, OrderItem
from confidence.analyzer import ConfidenceAnalyzer
from pipeline.clarification import ClarificationManager


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

intent_st = st.sampled_from(list(Intent))
item_st = st.builds(
    OrderItem,
    name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))),
    quantity=st.integers(min_value=1, max_value=50),
    unit=st.one_of(st.none(), st.sampled_from(["kg", "piece", "L"])),
    special_instructions=st.none(),
)
items_st = st.lists(item_st, min_size=0, max_size=5)
confidence_st = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
missing_fields_st = st.lists(
    st.sampled_from(["items", "delivery_time", "order_id"]),
    min_size=0, max_size=3, unique=True,
)
word_list_st = st.lists(
    st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L",))),
    min_size=0, max_size=5,
)


def make_order(intent, items, confidence, missing_fields) -> StructuredOrderData:
    return StructuredOrderData(
        intent=intent,
        items=items,
        confidence=confidence,
        missing_fields=missing_fields,
    )


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

class TestConfidenceAnalyzerIdempotence:

    @given(
        stt_conf=confidence_st,
        llm_conf=confidence_st,
        intent=intent_st,
        items=items_st,
        missing=missing_fields_st,
        low_words=word_list_st,
    )
    def test_same_inputs_produce_same_output(
        self, stt_conf, llm_conf, intent, items, missing, low_words
    ):
        """Property: ConfidenceAnalyzer is deterministic — same inputs → same result."""
        analyzer = ConfidenceAnalyzer()
        order = make_order(intent, items, llm_conf, missing)

        result1 = analyzer.analyze(stt_conf, order, low_words)
        result2 = analyzer.analyze(stt_conf, order, low_words)

        assert result1.should_clarify == result2.should_clarify
        assert result1.reason == result2.reason
        assert result1.missing_fields == result2.missing_fields
        assert result1.low_confidence_items == result2.low_confidence_items

    @given(
        stt_conf=confidence_st,
        llm_conf=confidence_st,
        intent=intent_st,
        items=items_st,
        missing=missing_fields_st,
        low_words=word_list_st,
        n=st.integers(min_value=2, max_value=5),
    )
    def test_repeated_calls_are_idempotent(
        self, stt_conf, llm_conf, intent, items, missing, low_words, n
    ):
        """Property: Calling analyze() n times with same inputs always gives same result."""
        analyzer = ConfidenceAnalyzer()
        order = make_order(intent, items, llm_conf, missing)

        results = [analyzer.analyze(stt_conf, order, low_words) for _ in range(n)]

        for r in results[1:]:
            assert r.should_clarify == results[0].should_clarify
            assert r.reason == results[0].reason


class TestClarificationMergeIdempotence:

    @given(
        intent=intent_st,
        orig_items=items_st,
        new_items=items_st,
        orig_conf=confidence_st,
        new_conf=confidence_st,
    )
    def test_merge_is_deterministic(self, intent, orig_items, new_items, orig_conf, new_conf):
        """Property: Merging the same two StructuredOrderData objects always gives the same result."""
        original = make_order(intent, orig_items, orig_conf, [])
        clarification = make_order(intent, new_items, new_conf, [])

        merged1 = ClarificationManager._merge_data(deepcopy(original), deepcopy(clarification))
        merged2 = ClarificationManager._merge_data(deepcopy(original), deepcopy(clarification))

        assert merged1.intent == merged2.intent
        assert merged1.confidence == merged2.confidence
        assert len(merged1.items) == len(merged2.items)
        for i1, i2 in zip(merged1.items, merged2.items):
            assert i1.name == i2.name
            assert i1.quantity == i2.quantity

    @given(
        intent=intent_st,
        items=items_st,
        conf=confidence_st,
    )
    def test_merge_with_empty_clarification_is_identity(self, intent, items, conf):
        """Property: Merging with an empty clarification leaves original data unchanged."""
        original = make_order(intent, items, conf, [])
        empty_clarification = make_order(intent, [], 0.0, [])

        merged = ClarificationManager._merge_data(deepcopy(original), empty_clarification)

        assert merged.intent == original.intent
        assert len(merged.items) == len(original.items)
        for m, o in zip(merged.items, original.items):
            assert m.name == o.name
            assert m.quantity == o.quantity


class TestSerializationIdempotence:

    @given(
        intent=intent_st,
        items=items_st,
        confidence=confidence_st,
        missing=missing_fields_st,
    )
    def test_serialization_is_idempotent(self, intent, items, confidence, missing):
        """Property: Serializing StructuredOrderData multiple times gives the same JSON."""
        order = make_order(intent, items, confidence, missing)

        json1 = json.dumps(asdict(order), sort_keys=True, default=str)
        json2 = json.dumps(asdict(order), sort_keys=True, default=str)

        assert json1 == json2

    @given(
        intent=intent_st,
        items=items_st,
        confidence=confidence_st,
        missing=missing_fields_st,
    )
    def test_deserialize_serialize_is_stable(self, intent, items, confidence, missing):
        """Property: Deserializing then re-serializing produces the same JSON (stable round-trip)."""
        original = make_order(intent, items, confidence, missing)
        json1 = json.dumps(asdict(original), sort_keys=True, default=str)

        # Deserialize
        d = json.loads(json1)
        reconstructed = StructuredOrderData(
            intent=Intent(d["intent"]),
            items=[OrderItem(**i) for i in d.get("items", [])],
            confidence=d.get("confidence", 0.0),
            missing_fields=d.get("missing_fields", []),
            delivery_time=d.get("delivery_time"),
            special_instructions=d.get("special_instructions"),
            order_id=d.get("order_id"),
        )

        json2 = json.dumps(asdict(reconstructed), sort_keys=True, default=str)
        assert json1 == json2
