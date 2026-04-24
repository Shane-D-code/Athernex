# 🔄 Athernex Merge Plan

**Date**: 2026-04-25  
**Goal**: Merge Athernex and Athernex-main, keeping the best from both

---

## 📊 Analysis Summary

**Athernex-main** is the newer, production-ready version with:
- ✅ Advanced caching (LRU + FIFO)
- ✅ Prometheus monitoring
- ✅ Service orchestration with auto-failover
- ✅ Property-based testing
- ✅ Better API structure
- ✅ Cleaner codebase (no build artifacts)

**Athernex** contains:
- ✅ Task-specific documentation (development history)
- ✅ Android app troubleshooting guides
- ✅ Build artifacts (can be removed)
- ✅ Test verification scripts

---

## 🎯 Merge Strategy

### Phase 1: Copy Advanced Features from Athernex-main
1. Advanced backend modules (monitoring, caching, orchestration)
2. Property-based test suites
3. Advanced scripts
4. demo.html web UI
5. main.py entry point
6. Enhanced documentation

### Phase 2: Archive Task Artifacts from Athernex
1. Task documentation (TASK*.md)
2. Test verification scripts
3. Android troubleshooting guides
4. Build scripts

### Phase 3: Clean Build Artifacts
1. Remove Android build folders
2. Remove Python cache
3. Remove redundant files

### Phase 4: Verify Integration
1. Run tests
2. Check imports
3. Verify server starts

---

## 📋 Files to Copy (from Athernex-main)

### Backend Modules
- `src/monitoring/metrics_collector.py`
- `src/cache/llm_cache.py`
- `src/cache/tts_cache.py`
- `src/cache/cached_llm.py`
- `src/cache/cached_tts.py`
- `src/orchestration/service_orchestrator.py`
- `src/orchestration/quota_manager.py`
- `src/orchestration/retry_strategy.py`
- `src/emotion/detector.py`
- `src/pipeline/clarification.py`
- `src/pipeline/streaming.py`
- `src/pipeline/voice_pipeline.py`
- `src/api/app.py`
- `src/api/dependencies.py`
- `src/api/routes/`
- `src/error_handler.py`
- `src/order_manager.py`
- `src/audio/barge_in_handler.py`
- `src/audio/barge_in.py`

### Test Suites
- `tests/property/` (all files)
- `tests/unit/` (all files)
- `tests/integration/test_pipeline.py`

### Scripts
- `scripts/checkpoint1_validation.py`
- `scripts/checkpoint2_validation.py`
- `scripts/run_brutal_tests.py`
- `scripts/setup_models.py`
- `scripts/start_ollama.py`
- `scripts/start_vosk.py`
- `scripts/start_whisper.py`
- `scripts/test_integration.py`
- `scripts/test_ollama.py`
- `scripts/test_tts.py`
- `scripts/validate_hardware.py`

### Other Files
- `main.py`
- `demo.html`
- `Dockerfile`
- `docs/PERFORMANCE.md`
- `docs/SETUP.md`
- `docs/SIH_SUBMISSION.md`
- `docker/piper/`
- `src/config/`

---

## 🗑️ Files to Archive (from Athernex)

### Task Documentation
- `TASK1_COMPLETE_SUMMARY.md`
- `TASK1_FASTTEXT_OPTIMIZATION.md`
- `TASK1_FASTTEXT_COMPLETE.md`
- `NEXT_STEPS.md`
- `SMOKE_TEST_RESULTS.md`
- `GITHUB_PUSH_SUMMARY.md`

### Test Scripts
- `test_server.py`
- `test_quick.py`
- `verify_task1.py`
- `verify_trained_detector.py`
- `test_android_integration.py`

### Android Guides
- `VyapaarSetuAITester/GRADLE_QUICK_FIX.md`
- `VyapaarSetuAITester/SPEED_UP_GRADLE.md`
- `VyapaarSetuAITester/BUILD_SUCCESS.md`
- `VyapaarSetuAITester/FIX_GRADLE_ERROR.md`
- `VyapaarSetuAITester/FIX_NO_RUN_BUTTON.md`
- `VyapaarSetuAITester/TROUBLESHOOTING.md`
- `VyapaarSetuAITester/QUICK_OPEN_GUIDE.md`
- `VyapaarSetuAITester/ANDROID_STUDIO_SETUP.md`
- `VyapaarSetuAITester/START_HERE.md`

### Utility Scripts
- `VyapaarSetuAITester/fix_models.ps1`
- `VyapaarSetuAITester/generate_icons.py`
- `VyapaarSetuAITester/download-gradle-wrapper.ps1`

---

## 🧹 Files to Delete

### Build Artifacts
- `VyapaarSetuAITester/build/`
- `VyapaarSetuAITester/.gradle/`
- `VyapaarSetuAITester/.idea/`
- `VyapaarSetuAITester/app/build/`
- `VyapaarSetuAITester/app/.gradle/`
- `VyapaarSetuAITester/app/.idea/`
- `VyapaarSetuAITester/build_log.txt`
- `VyapaarSetuAITester/build_output.txt`
- `VyapaarSetuAITester/local.properties`

### Python Cache
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`

### Redundant Files
- `README_NEW.md`
- `REORGANIZATION_PLAN.md`

---

## ✅ Expected Result

A single, clean, production-ready codebase with:
- ✅ All advanced features from Athernex-main
- ✅ Task documentation archived for reference
- ✅ No build artifacts
- ✅ Clean directory structure
- ✅ All tests passing
- ✅ Server starts successfully

---

## ✅ Merge Status: COMPLETE

### Phase 1-6: ✅ Complete
All advanced modules, tests, and documentation copied from Athernex-main.

### Additional Files Copied (Phase 7):
- `src/orchestration/quota_manager.py`
- `src/orchestration/rate_limiter.py`
- `src/orchestration/retry_strategy.py`
- `src/orchestration/service_orchestrator.py`
- `src/api/app.py`
- `src/api/dependencies.py`
- `src/api/routes/` (all files)
- `src/dialogue/anaphora_resolver.py`
- `src/dialogue/state.py`
- `src/dialogue/tracker.py`
- `src/audio/barge_in_handler.py`
- `src/audio/barge_in.py`
- `tests/integration/test_pipeline.py`
- `tests/conftest.py`

### Next: Verification
Run tests and verify server starts successfully.
