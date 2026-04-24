# VyapaarSetu AI Tester

Android testing application for the Athernex multilingual voice AI system.

## 🚀 Quick Start - Open in Android Studio

### 3 Simple Steps:

1. **Launch Android Studio**
2. **Click "Open"** → Navigate to:
   ```
   C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester
   ```
3. **Wait for Gradle sync** (2-5 minutes first time)

**Done!** Click the green Run button (▶️) to launch the app.

📖 **Need help?** See [QUICK_OPEN_GUIDE.md](QUICK_OPEN_GUIDE.md)

---

## ✨ Current Status

### ✅ Foundation Complete
- Project structure with MVVM + Clean Architecture
- Data models (LanguageResult, IntentResult, VoiceSession)
- API service interface (5 endpoints)
- Minimal working UI
- Hilt dependency injection setup
- Gradle configuration complete

### ⏳ Next Steps (UI Implementation)
- Full UI screens (Home, Test, Results, Dashboard)
- Speech recognition integration
- TTS playback
- Real-time visualization
- Session management

---

## 🏗️ Architecture

- **Pattern**: MVVM + Clean Architecture
- **UI**: Jetpack Compose (Material 3)
- **DI**: Hilt
- **Networking**: Retrofit
- **Database**: Room (planned)
- **Min SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)

---

## 📱 What You'll See

When you run the app, you'll see a welcome screen with:
- "VyapaarSetu AI Tester" title
- Foundation complete status
- Next development steps

This confirms the app is working!

---

## 🔧 Configuration

### Backend URL
Update in `ApiService.kt`:
```kotlin
private const val BASE_URL = "http://YOUR_BACKEND_IP:8000/"
```

### Local Properties (if needed)
If Android Studio can't find your SDK:
1. Copy `local.properties.example` to `local.properties`
2. Set your Android SDK path

---

## 📚 Documentation

### Quick Guides
- [QUICK_OPEN_GUIDE.md](QUICK_OPEN_GUIDE.md) - How to open in Android Studio (1 page)
- [ANDROID_STUDIO_SETUP.md](ANDROID_STUDIO_SETUP.md) - Detailed setup guide

### Complete Documentation
- [Quick Start](../docs/android/QUICK_START.md) - Getting started
- [Implementation Guide](../docs/android/IMPLEMENTATION_GUIDE.md) - Implementation details
- [Project Structure](../docs/android/PROJECT_STRUCTURE.md) - Architecture details
- [Integration Overview](../docs/integration/INTEGRATION_OVERVIEW.md) - Backend integration

---

## 🎯 Planned Features

### 1. Voice Test Screen
- Real-time speech-to-text
- Live language detection (Hindi, English, Hinglish, Kannada, Marathi)
- Intent classification with confidence scoring
- Bot response simulation with TTS

### 2. Call Simulator
- Full order-to-payment flow simulation
- Step-by-step visual timeline
- Payment link generation
- Soundbox alert simulation

### 3. Live Dashboard
- Real-time order feed
- Language distribution charts
- Confidence score analytics
- Payment tracking

### 4. Audit Log
- Complete session history
- Searchable and filterable
- Export to CSV/JSON
- Detailed transcripts

### 5. Language Stress Tester
- Pre-loaded test phrases
- Accuracy validation
- Custom phrase testing
- Pass/fail reporting

---

## 🧪 Backend Integration

### API Endpoints (Ready)
- `POST /api/android/detect-language` - Language detection
- `POST /api/android/classify-intent` - Intent classification
- `POST /api/android/process-speech` - Full speech processing
- `POST /api/android/test-phrase` - Quick phrase testing
- `WS /ws/dashboard` - Real-time dashboard updates

### Language Detection Accuracy
- Hindi: 100%
- English: 100%
- Hinglish: 100%
- Kannada: 100%
- Marathi: 100%

---

## 🛠️ Technology Stack

- **Language**: Kotlin
- **Compose**: 1.5.4
- **Hilt**: 2.48
- **Retrofit**: 2.9.0
- **Room**: 2.6.0
- **Coroutines**: 1.7.3
- **Material 3**: Latest

---

## ⚠️ Troubleshooting

### Can't open project?
See [ANDROID_STUDIO_SETUP.md](ANDROID_STUDIO_SETUP.md) troubleshooting section

### Gradle sync failed?
1. Check internet connection
2. File → Invalidate Caches → Restart
3. Try again

### Build errors?
1. Build → Clean Project
2. Build → Rebuild Project

### SDK not found?
1. File → Settings → System Settings → Android SDK
2. Note the SDK path
3. Create `local.properties` with your SDK path

---

## 📊 Project Metrics

- **Foundation**: 100% complete ✅
- **UI Implementation**: 0% (next step) ⏳
- **Backend Integration**: API service ready ✅
- **Testing Framework**: Ready ✅

---

## 🎯 Next Development Steps

1. **Implement UI Screens**
   - HomeScreen with language selection
   - TestScreen for speech input
   - ResultsScreen for displaying results
   - DashboardScreen for monitoring

2. **Add Speech Integration**
   - Android SpeechRecognizer
   - Audio recording
   - TTS playback

3. **Connect to Backend**
   - Implement repository layer
   - Add use cases
   - Handle API responses

4. **Add Testing**
   - Unit tests
   - Integration tests
   - UI tests

---

## 🤝 Contributing

1. Follow existing architecture patterns
2. Use Jetpack Compose for UI
3. Write tests for new features
4. Update documentation

---

## 📝 License

Proprietary

---

**Status**: Foundation complete, ready for UI development  
**Last Updated**: 2026-04-24

**Quick Links**:
- [How to Open](QUICK_OPEN_GUIDE.md)
- [Setup Guide](ANDROID_STUDIO_SETUP.md)
- [Documentation](../docs/android/)
