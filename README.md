# Athernex - Multilingual Voice AI System

A production-ready multilingual voice-based order processing system with support for Hindi, English, Kannada, Marathi, and Hinglish (code-mixed Hindi-English).

## 🚀 Quick Start

### Backend
```bash
cd voice-order-system
pip install -r requirements.txt
python src/api/main.py
```

### Android App
```bash
cd VyapaarSetuAITester
# Open in Android Studio
```

## 📚 Documentation

All documentation is organized in the `docs/` directory:

- **[Integration Guides](docs/integration/)** - Backend-Android integration
- **[Backend Documentation](docs/backend/)** - Backend setup and features
- **[Android Documentation](docs/android/)** - Android app development

### Quick Links
- [Installation Guide](docs/backend/INSTALLATION_GUIDE.md)
- [Windows Setup](docs/backend/WINDOWS_SETUP_GUIDE.md)
- [Integration Overview](docs/integration/INTEGRATION_OVERVIEW.md)
- [Android Quick Start](docs/android/QUICK_START.md)

## 🏗️ Project Structure

```
Athernex/
├── docs/                      # 📚 All documentation
│   ├── integration/          # Backend-Android integration
│   ├── backend/              # Backend documentation
│   │   └── features/         # Feature-specific guides
│   └── android/              # Android documentation
│
├── voice-order-system/       # 🐍 Python Backend
│   ├── src/                  # Source code
│   │   ├── api/             # FastAPI endpoints
│   │   ├── language/        # Language detection
│   │   ├── stt/             # Speech-to-text
│   │   ├── tts/             # Text-to-speech
│   │   ├── llm/             # LLM processing
│   │   └── telephony/       # Twilio integration
│   ├── tests/               # Test suite (96 tests, 100% passing)
│   ├── scripts/             # Utility scripts
│   └── config/              # Configuration
│
├── VyapaarSetuAITester/     # 📱 Android Testing App
│   └── app/src/             # Android source code
│
└── archive/                 # 📦 Legacy code (reference only)
```

## ✨ Features

### Language Support
- ✅ Hindi (100% accuracy)
- ✅ English (100% accuracy)
- ✅ Kannada (100% accuracy)
- ✅ Marathi (100% accuracy)
- ✅ Hinglish - Code-mixed Hindi-English (100% accuracy)

### Core Capabilities
- **Speech-to-Text**: Vosk and Whisper engines
- **Text-to-Speech**: Edge-TTS and Piper engines
- **Language Detection**: Hybrid detection (fastText + trained models)
- **LLM Processing**: Ollama and HuggingFace support
- **Telephony**: Twilio integration for phone calls
- **Android Integration**: REST API with 5 endpoints

### System Status
- 🟢 Backend: Production-ready (96/96 tests passing)
- 🟢 Language Detection: 100% accuracy (75/75 tests)
- 🟢 Integration: All 5 API endpoints functional
- 🟡 Android: Foundation complete, UI pending

## 🧪 Testing

```bash
# Backend tests
cd voice-order-system
pytest tests/ -v                    # Run all tests
python test_android_integration.py  # Test Android API
python test_quick.py                # Quick smoke test

# Language detection tests
pytest tests/test_brutal_language_detection.py -v
```

### Web-Based Testing
Open `voice-order-system/proxy.html` in your browser to test:
- 🎙️ Voice recognition (speak in any language)
- 📝 Text-based language detection
- 🧪 Quick test phrases (all 5 languages)
- 🔌 API endpoint testing
- 📊 Real-time results visualization

**Quick Start**:
1. Start backend: `python src/api/main.py`
2. Open `proxy.html` in browser
3. Click "Check Backend Health"
4. Test with voice or text!

See [PROXY_GUIDE.md](voice-order-system/PROXY_GUIDE.md) for details.

## 🔧 Development

### Backend Development
```bash
cd voice-order-system
# All backend code in src/
# Tests in tests/
# Scripts in scripts/
```

### Android Development
```bash
cd VyapaarSetuAITester
# All Android code in app/src/
# Open in Android Studio
```

## 📖 Key Documentation

| Document | Description |
|----------|-------------|
| [START_HERE](docs/backend/START_HERE.md) | Getting started guide |
| [INSTALLATION_GUIDE](docs/backend/INSTALLATION_GUIDE.md) | Complete setup instructions |
| [INTEGRATION_OVERVIEW](docs/integration/INTEGRATION_OVERVIEW.md) | Backend-Android integration |
| [QUICK_REFERENCE](docs/backend/QUICK_REFERENCE.md) | Command reference |
| [PROJECT_STRUCTURE_MASTER](PROJECT_STRUCTURE_MASTER.md) | Detailed structure guide |

## 🛠️ Technology Stack

### Backend
- Python 3.8+
- FastAPI
- Vosk / Whisper (STT)
- Edge-TTS / Piper (TTS)
- Ollama / HuggingFace (LLM)
- fastText (Language Detection)
- Twilio (Telephony)

### Android
- Kotlin
- Jetpack Compose
- Hilt (Dependency Injection)
- Retrofit (Networking)
- Room (Database)

## 📊 System Metrics

- **Test Coverage**: 96/96 tests passing (100%)
- **Language Accuracy**: 75/75 tests passing (100%)
- **API Endpoints**: 5 endpoints (all functional)
- **Supported Languages**: 5 languages
- **Code Files**: 50+ Python files, 5+ Kotlin files

## 🤝 Contributing

1. Check documentation in `docs/` directory
2. Follow existing code structure
3. Run tests before committing
4. Update documentation as needed

## 📝 License

Proprietary

---

**Last Updated**: 2026-04-24
**Status**: Production-ready backend, Android foundation complete
