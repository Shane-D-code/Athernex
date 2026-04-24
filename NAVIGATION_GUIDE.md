# Athernex - Quick Navigation Guide

**Use this guide to quickly find what you need in the reorganized project.**

---

## 🚀 I Want To...

### Get Started
- **Install the system** → [docs/backend/INSTALLATION_GUIDE.md](docs/backend/INSTALLATION_GUIDE.md)
- **Quick start** → [docs/backend/START_HERE.md](docs/backend/START_HERE.md)
- **Windows setup** → [docs/backend/WINDOWS_SETUP_GUIDE.md](docs/backend/WINDOWS_SETUP_GUIDE.md)
- **See project status** → [PROJECT_STATUS.md](PROJECT_STATUS.md)

### Understand the System
- **Project overview** → [README.md](README.md)
- **Project structure** → [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md)
- **Integration architecture** → [docs/integration/INTEGRATION_OVERVIEW.md](docs/integration/INTEGRATION_OVERVIEW.md)
- **System status** → [docs/backend/FINAL_STATUS.md](docs/backend/FINAL_STATUS.md)

### Work on Backend
- **Backend code** → `voice-order-system/src/`
- **Backend tests** → `voice-order-system/tests/`
- **Backend scripts** → `voice-order-system/scripts/`
- **Backend docs** → `docs/backend/`
- **Quick reference** → [docs/backend/QUICK_REFERENCE.md](docs/backend/QUICK_REFERENCE.md)

### Work on Android
- **Android code** → `VyapaarSetuAITester/app/src/`
- **Android docs** → `docs/android/`
- **Quick start** → [docs/android/QUICK_START.md](docs/android/QUICK_START.md)
- **Implementation guide** → [docs/android/IMPLEMENTATION_GUIDE.md](docs/android/IMPLEMENTATION_GUIDE.md)

### Learn About Features
- **Language detection** → [docs/backend/features/LANGUAGE_DETECTION_TEST_RESULTS.md](docs/backend/features/LANGUAGE_DETECTION_TEST_RESULTS.md)
- **fastText integration** → [docs/backend/features/FASTTEXT_INTEGRATION.md](docs/backend/features/FASTTEXT_INTEGRATION.md)
- **Telephony (phone calls)** → [docs/backend/features/TELEPHONY_INTEGRATION_GUIDE.md](docs/backend/features/TELEPHONY_INTEGRATION_GUIDE.md)
- **Telephony quick start** → [docs/backend/features/TELEPHONY_QUICK_START.md](docs/backend/features/TELEPHONY_QUICK_START.md)

### Test the System
- **Run all tests** → `cd voice-order-system && pytest tests/ -v`
- **Quick test** → `cd voice-order-system && python test_quick.py`
- **Android API test** → `cd voice-order-system && python test_android_integration.py`
- **Language tests** → `cd voice-order-system && pytest tests/test_brutal_language_detection.py -v`

### Understand Integration
- **Integration overview** → [docs/integration/INTEGRATION_OVERVIEW.md](docs/integration/INTEGRATION_OVERVIEW.md)
- **Integration status** → [docs/integration/INTEGRATION_STATUS.md](docs/integration/INTEGRATION_STATUS.md)
- **Complete guide** → [docs/integration/COMPLETE_INTEGRATION_GUIDE.md](docs/integration/COMPLETE_INTEGRATION_GUIDE.md)

### Find Documentation
- **All documentation** → `docs/`
- **Documentation index** → [docs/README.md](docs/README.md)
- **Integration docs** → `docs/integration/`
- **Backend docs** → `docs/backend/`
- **Feature docs** → `docs/backend/features/`
- **Android docs** → `docs/android/`

---

## 📁 Directory Quick Reference

```
Athernex/
├── docs/                          # 📚 ALL DOCUMENTATION HERE
│   ├── integration/              # Backend-Android integration
│   ├── backend/                  # Backend documentation
│   │   └── features/             # Feature-specific guides
│   └── android/                  # Android documentation
│
├── voice-order-system/           # 🐍 BACKEND CODE HERE
│   ├── src/                      # Backend source code
│   ├── tests/                    # Backend tests
│   ├── scripts/                  # Utility scripts
│   └── config/                   # Configuration
│
├── VyapaarSetuAITester/          # 📱 ANDROID CODE HERE
│   └── app/src/                  # Android source code
│
└── archive/                      # 📦 OLD CODE (reference only)
```

---

## 🔍 Common Tasks

### Run Backend Server
```bash
cd voice-order-system
python src/api/main.py
```

### Run Tests
```bash
cd voice-order-system
pytest tests/ -v                    # All tests
python test_quick.py                # Quick test
python test_android_integration.py  # Android API test
```

### Check System Status
```bash
cd voice-order-system
python test_quick.py
# Should show: 5/5 tests passed
```

### View Documentation
```bash
# Open in browser or editor
docs/README.md                      # Documentation index
docs/backend/START_HERE.md          # Getting started
docs/integration/INTEGRATION_OVERVIEW.md  # Integration guide
```

### Work on Backend Code
```bash
cd voice-order-system/src
# Edit files in:
# - api/          (API endpoints)
# - language/     (Language detection)
# - stt/          (Speech-to-text)
# - tts/          (Text-to-speech)
# - llm/          (LLM processing)
# - telephony/    (Phone integration)
```

### Work on Android Code
```bash
cd VyapaarSetuAITester/app/src/main/java/com/vyapaarsetu/aitester
# Edit files in:
# - data/model/   (Data models)
# - data/remote/  (API service)
# - ui/           (UI screens - to be created)
```

---

## 📖 Documentation by Topic

### Setup & Installation
- [Installation Guide](docs/backend/INSTALLATION_GUIDE.md)
- [Windows Setup](docs/backend/WINDOWS_SETUP_GUIDE.md)
- [Start Here](docs/backend/START_HERE.md)

### System Overview
- [README](README.md)
- [Project Status](PROJECT_STATUS.md)
- [Project Structure](PROJECT_STRUCTURE_MASTER.md)
- [System Status](docs/backend/FINAL_STATUS.md)

### Integration
- [Integration Overview](docs/integration/INTEGRATION_OVERVIEW.md)
- [Integration Status](docs/integration/INTEGRATION_STATUS.md)
- [Complete Integration Guide](docs/integration/COMPLETE_INTEGRATION_GUIDE.md)

### Features
- [Language Detection](docs/backend/features/LANGUAGE_DETECTION_TEST_RESULTS.md)
- [fastText Integration](docs/backend/features/FASTTEXT_INTEGRATION.md)
- [Telephony Integration](docs/backend/features/TELEPHONY_INTEGRATION_GUIDE.md)
- [Telephony Quick Start](docs/backend/features/TELEPHONY_QUICK_START.md)
- [Task 1 Complete](docs/backend/features/TASK1_FASTTEXT_COMPLETE.md)
- [Task 5 Complete](docs/backend/features/TASK5_LANGUAGE_TRAINING_COMPLETE.md)

### Android
- [Android Quick Start](docs/android/QUICK_START.md)
- [Implementation Guide](docs/android/IMPLEMENTATION_GUIDE.md)
- [Project Structure](docs/android/PROJECT_STRUCTURE.md)

### Backend Reference
- [Quick Reference](docs/backend/QUICK_REFERENCE.md)
- [System Status Report](docs/backend/SYSTEM_STATUS_REPORT.md)
- [Fixes Applied](docs/backend/FIXES_APPLIED_SUMMARY.md)
- [Hardware Validation](docs/backend/HARDWARE_VALIDATION_REPORT.md)
- [Status](docs/backend/STATUS.md)
- [TODO](docs/backend/TODO.md)

### Project Organization
- [Reorganization Plan](REORGANIZATION_PLAN.md)
- [Reorganization Complete](REORGANIZATION_COMPLETE.md)
- [File Verification](FILE_VERIFICATION_REPORT.md)
- [Organization Summary](ORGANIZATION_SUMMARY.md)
- [Master Index](MASTER_INDEX.md)

---

## 🎯 By Role

### I'm a Backend Developer
1. Read: [docs/backend/START_HERE.md](docs/backend/START_HERE.md)
2. Code: `voice-order-system/src/`
3. Test: `voice-order-system/tests/`
4. Docs: `docs/backend/`
5. Reference: [docs/backend/QUICK_REFERENCE.md](docs/backend/QUICK_REFERENCE.md)

### I'm an Android Developer
1. Read: [docs/android/QUICK_START.md](docs/android/QUICK_START.md)
2. Code: `VyapaarSetuAITester/app/src/`
3. API: [docs/integration/INTEGRATION_OVERVIEW.md](docs/integration/INTEGRATION_OVERVIEW.md)
4. Docs: `docs/android/`

### I'm a Project Manager
1. Status: [PROJECT_STATUS.md](PROJECT_STATUS.md)
2. Overview: [README.md](README.md)
3. Structure: [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md)
4. Integration: [docs/integration/INTEGRATION_STATUS.md](docs/integration/INTEGRATION_STATUS.md)

### I'm New to the Project
1. Start: [README.md](README.md)
2. Install: [docs/backend/INSTALLATION_GUIDE.md](docs/backend/INSTALLATION_GUIDE.md)
3. Quick Start: [docs/backend/START_HERE.md](docs/backend/START_HERE.md)
4. Test: `cd voice-order-system && python test_quick.py`
5. Explore: [docs/README.md](docs/README.md)

---

## 🔧 Troubleshooting

### Can't Find a File?
- Check [FILE_VERIFICATION_REPORT.md](FILE_VERIFICATION_REPORT.md)
- Check [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md)
- All docs are in `docs/` directory
- All backend code is in `voice-order-system/src/`
- All Android code is in `VyapaarSetuAITester/app/src/`

### Tests Failing?
- Run: `cd voice-order-system && python test_quick.py`
- Check: [docs/backend/SYSTEM_STATUS_REPORT.md](docs/backend/SYSTEM_STATUS_REPORT.md)
- Read: [docs/backend/FIXES_APPLIED_SUMMARY.md](docs/backend/FIXES_APPLIED_SUMMARY.md)

### Setup Issues?
- Windows: [docs/backend/WINDOWS_SETUP_GUIDE.md](docs/backend/WINDOWS_SETUP_GUIDE.md)
- General: [docs/backend/INSTALLATION_GUIDE.md](docs/backend/INSTALLATION_GUIDE.md)
- Quick: [docs/backend/START_HERE.md](docs/backend/START_HERE.md)

### Integration Issues?
- Overview: [docs/integration/INTEGRATION_OVERVIEW.md](docs/integration/INTEGRATION_OVERVIEW.md)
- Status: [docs/integration/INTEGRATION_STATUS.md](docs/integration/INTEGRATION_STATUS.md)
- Guide: [docs/integration/COMPLETE_INTEGRATION_GUIDE.md](docs/integration/COMPLETE_INTEGRATION_GUIDE.md)

---

## 📊 Quick Stats

- **Total Documentation**: 23 files
- **Backend Code Files**: 50+ Python files
- **Android Code Files**: 5 Kotlin files (foundation)
- **Test Files**: 5 test suites (176 tests)
- **Test Pass Rate**: 100%
- **Language Accuracy**: 100%
- **Supported Languages**: 5 (Hindi, English, Kannada, Marathi, Hinglish)

---

## 🎉 Quick Wins

### Test the System (30 seconds)
```bash
cd voice-order-system
python test_quick.py
# Should see: ✅ All tests passed!
```

### View Project Status (2 minutes)
```bash
# Open in editor:
PROJECT_STATUS.md
```

### Understand Integration (5 minutes)
```bash
# Open in editor:
docs/integration/INTEGRATION_OVERVIEW.md
```

### Start Development (10 minutes)
```bash
# Backend:
cd voice-order-system
# Read: docs/backend/START_HERE.md
# Edit: src/

# Android:
cd VyapaarSetuAITester
# Read: docs/android/QUICK_START.md
# Edit: app/src/
```

---

**Remember**: 
- All documentation is in `docs/`
- All backend code is in `voice-order-system/src/`
- All Android code is in `VyapaarSetuAITester/app/src/`
- Legacy code is in `archive/` (reference only)

**Need help?** Check [docs/README.md](docs/README.md) for complete documentation index.

---

*Last Updated: 2026-04-24*
