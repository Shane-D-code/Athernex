# Athernex - Master Project Structure

## Overview

This document provides the complete, organized structure of the Athernex project, which consists of:
1. **voice-order-system** - Python backend (multilingual voice AI)
2. **VyapaarSetuAITester** - Android app (testing harness)
3. **Root-level legacy code** - Old implementation (to be archived)

## Issues Identified

### 1. Duplicate Structures ❌
- `Athernex/src/` - Old implementation
- `Athernex/voice-order-system/src/` - Current implementation
- `Athernex/voice-order-system/Athernex/` - Nested duplicate (should be removed)

### 2. Scattered Documentation ❌
- Documentation files in multiple locations
- No clear hierarchy

### 3. Mixed Concerns ❌
- Root level has both old and new code
- Unclear which files belong to which project

## Recommended Structure

```
Athernex/
├── README.md                           # Master README
├── .gitignore                          # Root gitignore
├── PROJECT_STRUCTURE_MASTER.md         # This file
│
├── docs/                               # 📚 All Documentation
│   ├── README.md                       # Documentation index
│   ├── integration/                    # Integration guides
│   │   ├── INTEGRATION_OVERVIEW.md
│   │   ├── INTEGRATION_STATUS.md
│   │   └── COMPLETE_INTEGRATION_GUIDE.md
│   ├── backend/                        # Backend docs
│   │   ├── FINAL_STATUS.md
│   │   ├── QUICK_REFERENCE.md
│   │   ├── INSTALLATION_GUIDE.md
│   │   ├── WINDOWS_SETUP_GUIDE.md
│   │   ├── START_HERE.md
│   │   └── features/
│   │       ├── LANGUAGE_DETECTION_TEST_RESULTS.md
│   │       ├── FASTTEXT_INTEGRATION.md
│   │       ├── TELEPHONY_INTEGRATION_GUIDE.md
│   │       ├── TELEPHONY_QUICK_START.md
│   │       ├── TASK1_FASTTEXT_COMPLETE.md
│   │       └── TASK5_LANGUAGE_TRAINING_COMPLETE.md
│   └── android/                        # Android docs
│       ├── README.md
│       ├── QUICK_START.md
│       ├── IMPLEMENTATION_GUIDE.md
│       └── PROJECT_STRUCTURE.md
│
├── voice-order-system/                 # 🐍 Python Backend
│   ├── README.md
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── docker-compose.yml
│   │
│   ├── src/                            # Source code
│   │   ├── __init__.py
│   │   ├── api/                        # FastAPI endpoints
│   │   │   ├── main.py
│   │   │   ├── android_routes.py
│   │   │   └── telephony_routes.py
│   │   ├── language/                   # Language detection
│   │   │   ├── detector.py
│   │   │   ├── trained_detector.py
│   │   │   ├── hybrid_detector.py
│   │   │   └── fasttext_detector.py
│   │   ├── stt/                        # Speech-to-text
│   │   ├── tts/                        # Text-to-speech
│   │   ├── llm/                        # LLM processing
│   │   ├── telephony/                  # Twilio integration
│   │   ├── orchestration/              # Pipeline orchestration
│   │   ├── dialogue/                   # Dialogue management
│   │   ├── audio/                      # Audio processing
│   │   ├── confidence/                 # Confidence scoring
│   │   └── utils/                      # Utilities
│   │
│   ├── tests/                          # Test suite
│   │   ├── test_brutal_language_detection.py
│   │   ├── test_system_integration.py
│   │   ├── test_fasttext_detector.py
│   │   └── test_android_integration.py
│   │
│   ├── scripts/                        # Utility scripts
│   │   ├── setup_fasttext.py
│   │   ├── setup_ollama_and_fasttext.py
│   │   ├── quick_diagnostic.py
│   │   ├── comprehensive_diagnostic.py
│   │   └── auto_fix.py
│   │
│   └── config/                         # Configuration
│       └── config.py
│
├── VyapaarSetuAITester/                # 📱 Android App
│   ├── README.md
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   ├── local.properties.example
│   │
│   ├── app/
│   │   ├── build.gradle.kts
│   │   ├── proguard-rules.pro
│   │   └── src/
│   │       ├── main/
│   │       │   ├── AndroidManifest.xml
│   │       │   ├── java/com/vyapaarsetu/aitester/
│   │       │   │   ├── VyapaarSetuApp.kt
│   │       │   │   ├── MainActivity.kt
│   │       │   │   ├── data/
│   │       │   │   │   ├── model/
│   │       │   │   │   ├── repository/
│   │       │   │   │   ├── local/
│   │       │   │   │   └── remote/
│   │       │   │   ├── domain/
│   │       │   │   │   └── usecase/
│   │       │   │   ├── ui/
│   │       │   │   │   ├── screens/
│   │       │   │   │   ├── components/
│   │       │   │   │   ├── theme/
│   │       │   │   │   ├── navigation/
│   │       │   │   │   └── viewmodel/
│   │       │   │   ├── util/
│   │       │   │   └── di/
│   │       │   └── res/
│   │       └── test/
│   │
│   └── docs/                           # Android-specific docs
│       └── (linked to main docs/)
│
└── archive/                            # 📦 Legacy Code (Old Implementation)
    ├── README.md                       # Explains this is archived
    ├── src/                            # Old src/ from root
    ├── scripts/                        # Old scripts/ from root
    └── tests/                          # Old tests/ from root
```

## File Locations Reference

### Documentation Files

| File | Current Location | Correct Location |
|------|------------------|------------------|
| INTEGRATION_OVERVIEW.md | `Athernex/` | `docs/integration/` |
| INTEGRATION_STATUS.md | `Athernex/` | `docs/integration/` |
| COMPLETE_INTEGRATION_GUIDE.md | `Athernex/` | `docs/integration/` |
| FINAL_STATUS.md | `voice-order-system/` | `docs/backend/` |
| QUICK_REFERENCE.md | `voice-order-system/` | `docs/backend/` |
| LANGUAGE_DETECTION_TEST_RESULTS.md | `voice-order-system/` | `docs/backend/features/` |
| FASTTEXT_INTEGRATION.md | `voice-order-system/` | `docs/backend/features/` |
| TELEPHONY_INTEGRATION_GUIDE.md | `voice-order-system/` | `docs/backend/features/` |
| TASK1_FASTTEXT_COMPLETE.md | `voice-order-system/` | `docs/backend/features/` |
| TASK5_LANGUAGE_TRAINING_COMPLETE.md | `voice-order-system/` | `docs/backend/features/` |
| INSTALLATION_GUIDE.md | `voice-order-system/` | `docs/backend/` |
| WINDOWS_SETUP_GUIDE.md | `voice-order-system/` | `docs/backend/` |
| START_HERE.md | `voice-order-system/` | `docs/backend/` |
| README.md (Android) | `VyapaarSetuAITester/` | Keep + link to `docs/android/` |
| QUICK_START.md (Android) | `VyapaarSetuAITester/` | `docs/android/` |
| IMPLEMENTATION_GUIDE.md | `VyapaarSetuAITester/` | `docs/android/` |
| PROJECT_STRUCTURE.md | `VyapaarSetuAITester/` | `docs/android/` |

### Code Files

| File | Current Location | Status |
|------|------------------|--------|
| `src/api/main.py` | `voice-order-system/src/api/` | ✅ Correct |
| `src/api/android_routes.py` | `voice-order-system/src/api/` | ✅ Correct |
| `src/language/trained_detector.py` | `voice-order-system/src/language/` | ✅ Correct |
| `src/language/hybrid_detector.py` | `voice-order-system/src/language/` | ✅ Correct |
| `test_android_integration.py` | `voice-order-system/` | ✅ Correct (root of backend) |
| `test_quick.py` | `voice-order-system/` | ✅ Correct (root of backend) |
| `ApiService.kt` | `VyapaarSetuAITester/app/src/main/java/.../data/remote/` | ✅ Correct |
| `LanguageResult.kt` | `VyapaarSetuAITester/app/src/main/java/.../data/model/` | ✅ Correct |
| `IntentResult.kt` | `VyapaarSetuAITester/app/src/main/java/.../data/model/` | ✅ Correct |

### Duplicate/Legacy Files

| File/Folder | Location | Action |
|-------------|----------|--------|
| `Athernex/src/` | Root | ❌ Move to `archive/` |
| `Athernex/scripts/` | Root | ❌ Move to `archive/` |
| `Athernex/tests/` | Root | ❌ Move to `archive/` |
| `voice-order-system/Athernex/` | Nested | ❌ Delete (duplicate) |
| Old README files | Various | ❌ Consolidate |

## Quick Navigation

### For Backend Development
```bash
cd Athernex/voice-order-system
# All backend code in src/
# Tests in tests/
# Scripts in scripts/
# Docs in ../docs/backend/
```

### For Android Development
```bash
cd Athernex/VyapaarSetuAITester
# All Android code in app/src/
# Docs in ../docs/android/
```

### For Documentation
```bash
cd Athernex/docs
# Integration guides in integration/
# Backend docs in backend/
# Android docs in android/
```

## Implementation Status

### ✅ Correct Locations
- Backend source code: `voice-order-system/src/`
- Backend tests: `voice-order-system/tests/`
- Backend scripts: `voice-order-system/scripts/`
- Android source: `VyapaarSetuAITester/app/src/`
- Android models: `VyapaarSetuAITester/app/src/main/java/.../data/model/`

### ⚠️ Needs Reorganization
- Documentation scattered across multiple locations
- Legacy code in root directory
- Nested duplicate `voice-order-system/Athernex/`

### ❌ To Be Removed
- `Athernex/voice-order-system/Athernex/` (nested duplicate)
- Redundant documentation files

## Next Steps

1. **Create docs/ directory structure**
2. **Move documentation files to correct locations**
3. **Archive legacy code**
4. **Remove nested duplicates**
5. **Update all internal links**
6. **Create master README with navigation**

## File Count Summary

### Backend (voice-order-system)
- Source files: ~50 Python files
- Test files: 5 test suites
- Scripts: 17 utility scripts
- Documentation: 15+ markdown files
- Configuration: 2 config files

### Android (VyapaarSetuAITester)
- Source files: ~30 Kotlin files (to be created)
- Models: 3 data model files (created)
- Documentation: 4 markdown files
- Configuration: 2 gradle files

### Documentation (to be organized)
- Integration guides: 3 files
- Backend guides: 12 files
- Android guides: 4 files
- Total: 19 documentation files

## Maintenance

This structure should be maintained as follows:

1. **All documentation** → `docs/` directory
2. **Backend code** → `voice-order-system/src/`
3. **Android code** → `VyapaarSetuAITester/app/src/`
4. **Tests** → Respective `tests/` directories
5. **Scripts** → Respective `scripts/` directories
6. **Legacy code** → `archive/` (read-only)

## Version Control

- Main branch: Clean, organized structure
- All commits: Reference this structure
- Pull requests: Must maintain organization
- Documentation: Keep in sync with code

---

**Last Updated**: 2026-04-24
**Status**: Structure defined, reorganization pending
**Next**: Execute reorganization plan
