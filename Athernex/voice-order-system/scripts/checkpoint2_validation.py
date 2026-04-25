"""
Checkpoint 2 Validation Script.

Verifies pipeline integration:
- Dialogue state tracking
- Order management
- Service orchestration with fallbacks
- Caching layer
- End-to-end pipeline (text mode)
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestration.orchestrator import ServiceOrchestrator
from orchestration.pipeline import VoicePipeline
from orchestration.order_manager import OrderManager
from orchestration.cache import CacheManager
from dialogue.manager import DialogueManager
from llm import OllamaLLMProcessor
from tts import EdgeTTSEngine


async def main():
    print("\n" + "=" * 70)
    print("CHECKPOINT 2: Pipeline Integration Validation")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Service Orchestrator
    print("\n[1/6] Testing Service Orchestrator...")
    try:
        llm = OllamaLLMProcessor(model="phi3:latest")
        tts = EdgeTTSEngine()
        
        orchestrator = ServiceOrchestrator(
            stt_engines=[],
            llm_processors=[llm],
            tts_engines=[tts],
        )
        
        health = await orchestrator.health_check_all()
        print(f"  LLM healthy: {health['llm'].get(list(health['llm'].keys())[0], {}).get('healthy', False) if health['llm'] else 'N/A'}")
        print(f"  TTS healthy: {health['tts'].get(list(health['tts'].keys())[0], {}).get('healthy', False) if health['tts'] else 'N/A'}")
        results['orchestrator'] = True
    except Exception as e:
        print(f"  ✗ Orchestrator error: {e}")
        results['orchestrator'] = False
    
    # Test 2: Dialogue Manager
    print("\n[2/6] Testing Dialogue Manager...")
    try:
        dm = DialogueManager()
        session = dm.create_session("test-session", language="en")
        
        # Simulate conversation
        session = dm.update_session(
            session_id="test-session",
            user_utterance="I want 2 pizzas",
            bot_response="What else would you like?",
        )
        
        # Test anaphora resolution
        resolved = dm.resolve_anaphora(session, "add one more")
        print(f"  Anaphora resolved: '{resolved}'")
        
        # Test state inference
        from llm.base import StructuredOrderData, Intent, OrderItem
        test_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="pizza", quantity=2)],
            confidence=0.9,
            missing_fields=[],
        )
        state = dm._infer_state(session, test_data)
        print(f"  Inferred state: {state.value}")
        
        # Test expired session cleanup
        dm.cleanup_expired_sessions()
        print(f"  Active sessions: {dm.get_active_session_count()}")
        
        results['dialogue'] = True
    except Exception as e:
        print(f"  ✗ Dialogue error: {e}")
        results['dialogue'] = False
    
    # Test 3: Order Manager
    print("\n[3/6] Testing Order Manager...")
    try:
        om = OrderManager()
        
        from llm.base import OrderItem
        order = om.create_order(
            session_id="test-session",
            items=[
                OrderItem(name="pizza", quantity=2),
                OrderItem(name="coke", quantity=1),
            ],
            delivery_time="2026-04-24T19:00:00",
            language="en",
        )
        print(f"  Created order: {order.order_id}")
        
        # Test modification
        om.modify_order(
            order_id=order.order_id,
            add_items=[OrderItem(name="garlic bread", quantity=1)],
        )
        updated = om.get_order(order.order_id)
        print(f"  Modified items: {len(updated.items)}")
        
        # Test status
        om.confirm_order(order.order_id)
        print(f"  Status after confirm: {om.get_order(order.order_id).status.value}")
        
        # Test stats
        stats = om.get_order_statistics()
        print(f"  Total orders: {stats['total_orders']}")
        
        results['order_manager'] = True
    except Exception as e:
        print(f"  ✗ Order Manager error: {e}")
        results['order_manager'] = False
    
    # Test 4: Cache Manager
    print("\n[4/6] Testing Cache Manager...")
    try:
        cache = CacheManager(llm_cache_size=10, tts_cache_size=10)
        
        # Test LLM cache
        cache.cache_llm_response("test-key", {"intent": "place_order"})
        cached = cache.get_cached_llm_response("test-key")
        print(f"  LLM cache hit: {cached is not None}")
        
        # Test TTS cache
        cache.cache_tts_audio("audio-key", b"fake-audio-data")
        audio = cache.get_cached_tts_audio("audio-key")
        print(f"  TTS cache hit: {audio is not None}")
        
        # Test stats
        stats = cache.get_stats()
        print(f"  Cache utilization: LLM={stats['llm_cache']['size']}/{stats['llm_cache']['max_size']}")
        
        results['cache'] = True
    except Exception as e:
        print(f"  ✗ Cache error: {e}")
        results['cache'] = False
    
    # Test 5: End-to-End Pipeline (Text Mode)
    print("\n[5/6] Testing End-to-End Pipeline (Text Mode)...")
    try:
        llm = OllamaLLMProcessor(model="phi3:latest")
        tts = EdgeTTSEngine()
        
        orchestrator = ServiceOrchestrator(
            stt_engines=[],
            llm_processors=[llm],
            tts_engines=[tts],
        )
        
        pipeline = VoicePipeline(
            orchestrator=orchestrator,
            dialogue_manager=DialogueManager(),
            order_manager=OrderManager(),
            cache_manager=CacheManager(),
        )
        
        result = await pipeline.process_text(
            text="I want to order 2 pizzas for delivery at 7pm",
            session_id="pipeline-test",
            language="en",
        )
        
        print(f"  Success: {result.success}")
        print(f"  Intent: {result.intent}")
        print(f"  Order ID: {result.order_id}")
        print(f"  Bot response: {result.bot_text[:60] if result.bot_text else 'N/A'}...")
        print(f"  Processing time: {result.processing_time_ms:.0f}ms")
        print(f"  Audio synthesized: {result.audio_bytes is not None}")
        
        results['pipeline'] = result.success
    except Exception as e:
        print(f"  ✗ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        results['pipeline'] = False
    
    # Test 6: Session Info & Stats
    print("\n[6/6] Testing Session Info & System Stats...")
    try:
        info = pipeline.get_session_info("pipeline-test")
        print(f"  Session state: {info['state']}")
        print(f"  Turn count: {info['turn_count']}")
        print(f"  Orders in session: {len(info['orders'])}")
        
        stats = pipeline.get_system_stats()
        print(f"  Active sessions: {stats['active_sessions']}")
        print(f"  Total orders: {stats['orders']['total_orders']}")
        
        results['stats'] = True
    except Exception as e:
        print(f"  ✗ Stats error: {e}")
        results['stats'] = False
    
    # Cleanup
    try:
        await orchestrator.close_all()
    except:
        pass
    
    # Summary
    print("\n" + "=" * 70)
    print("CHECKPOINT 2 RESULTS:")
    print("=" * 70)
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {component.upper():25s} {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ CHECKPOINT 2 PASSED - Pipeline integration functional")
    else:
        print("✗ CHECKPOINT 2 PARTIAL - Some components need attention")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

