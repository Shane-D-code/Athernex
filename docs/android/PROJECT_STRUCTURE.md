# VyapaarSetu AI Tester - Complete Project Structure

## Overview

This document provides the complete file structure and implementation guide for the Android app. The app is designed to work seamlessly with the existing Python voice-order-system backend.

## Complete File Tree

```
VyapaarSetuAITester/
├── app/
│   ├── build.gradle.kts                    ✅ Created
│   ├── proguard-rules.pro
│   └── src/
│       ├── main/
│       │   ├── AndroidManifest.xml         ✅ Created
│       │   ├── java/com/vyapaarsetu/aitester/
│       │   │   ├── VyapaarSetuApp.kt       ✅ Created
│       │   │   ├── MainActivity.kt
│       │   │   │
│       │   │   ├── data/
│       │   │   │   ├── model/
│       │   │   │   │   ├── LanguageResult.kt       ✅ Created
│       │   │   │   │   ├── IntentResult.kt         ✅ Created
│       │   │   │   │   ├── VoiceSession.kt         ✅ Created
│       │   │   │   │   ├── Order.kt
│       │   │   │   │   └── PaymentState.kt
│       │   │   │   │
│       │   │   │   ├── repository/
│       │   │   │   │   ├── VoiceRepository.kt
│       │   │   │   │   ├── OrderRepository.kt
│       │   │   │   │   └── PaymentRepository.kt
│       │   │   │   │
│       │   │   │   ├── local/
│       │   │   │   │   ├── AppDatabase.kt
│       │   │   │   │   ├── VoiceSessionDao.kt
│       │   │   │   │   ├── OrderDao.kt
│       │   │   │   │   └── Converters.kt
│       │   │   │   │
│       │   │   │   └── remote/
│       │   │   │       ├── ApiService.kt
│       │   │   │       ├── ClaudeApiService.kt
│       │   │   │       ├── WebSocketManager.kt
│       │   │   │       └── dto/
│       │   │   │           ├── LanguageDetectionRequest.kt
│       │   │   │           ├── IntentClassificationRequest.kt
│       │   │   │           └── SpeechProcessingRequest.kt
│       │   │   │
│       │   │   ├── domain/
│       │   │   │   └── usecase/
│       │   │   │       ├── ProcessSpeechUseCase.kt
│       │   │   │       ├── DetectLanguageUseCase.kt
│       │   │   │       ├── ClassifyIntentUseCase.kt
│       │   │   │       └── HandlePaymentUseCase.kt
│       │   │   │
│       │   │   ├── ui/
│       │   │   │   ├── theme/
│       │   │   │   │   ├── Color.kt
│       │   │   │   │   ├── Theme.kt
│       │   │   │   │   └── Type.kt
│       │   │   │   │
│       │   │   │   ├── navigation/
│       │   │   │   │   └── NavGraph.kt
│       │   │   │   │
│       │   │   │   ├── screens/
│       │   │   │   │   ├── HomeScreen.kt
│       │   │   │   │   ├── VoiceTestScreen.kt
│       │   │   │   │   ├── SimulatorScreen.kt
│       │   │   │   │   ├── DashboardScreen.kt
│       │   │   │   │   ├── AuditLogScreen.kt
│       │   │   │   │   └── LanguageStressTestScreen.kt
│       │   │   │   │
│       │   │   │   ├── components/
│       │   │   │   │   ├── VoiceWaveform.kt
│       │   │   │   │   ├── ConfidenceMeter.kt
│       │   │   │   │   ├── LanguageBadge.kt
│       │   │   │   │   ├── IntentCard.kt
│       │   │   │   │   ├── SoundboxAlert.kt
│       │   │   │   │   ├── StatCard.kt
│       │   │   │   │   ├── OrderCard.kt
│       │   │   │   │   └── TimelineStage.kt
│       │   │   │   │
│       │   │   │   └── viewmodel/
│       │   │   │       ├── VoiceViewModel.kt
│       │   │   │       ├── SimulatorViewModel.kt
│       │   │   │       ├── DashboardViewModel.kt
│       │   │   │       └── AuditLogViewModel.kt
│       │   │   │
│       │   │   ├── util/
│       │   │   │   ├── LanguageDetector.kt
│       │   │   │   ├── SpeechProcessor.kt
│       │   │   │   ├── TTSManager.kt
│       │   │   │   ├── ConfidenceGateEngine.kt
│       │   │   │   ├── PermissionHandler.kt
│       │   │   │   └── Extensions.kt
│       │   │   │
│       │   │   └── di/
│       │   │       ├── AppModule.kt
│       │   │       ├── NetworkModule.kt
│       │   │       ├── DatabaseModule.kt
│       │   │       └── UtilModule.kt
│       │   │
│       │   └── res/
│       │       ├── values/
│       │       │   ├── strings.xml
│       │       │   ├── colors.xml
│       │       │   └── themes.xml
│       │       ├── xml/
│       │       │   ├── backup_rules.xml
│       │       │   └── data_extraction_rules.xml
│       │       ├── mipmap-*/
│       │       │   └── ic_launcher.png
│       │       └── raw/
│       │           └── lottie_mic_animation.json
│       │
│       └── test/
│           └── java/com/vyapaarsetu/aitester/
│               ├── LanguageDetectorTest.kt
│               ├── IntentClassifierTest.kt
│               └── ConfidenceGateTest.kt
│
├── build.gradle.kts                        ✅ Created
├── settings.gradle.kts
├── gradle.properties
├── local.properties                        (Create this)
├── README.md                               ✅ Created
└── PROJECT_STRUCTURE.md                    ✅ This file
```

## Backend Integration

### Python Backend Endpoints

The app connects to your existing `voice-order-system` backend:

```
Base URL: http://localhost:8000 (or your server)

Endpoints:
- POST /api/detect-language
  Request: { "text": "मुझे pizza चाहिए" }
  Response: { "language": "hinglish", "confidence": 0.87, "is_code_mixed": true }

- POST /api/classify-intent
  Request: { "text": "...", "language": "hi" }
  Response: { "primary_intent": "confirm_order", "confidence": 0.92, ... }

- POST /api/process-speech
  Request: { "audio": "base64...", "language": "auto" }
  Response: { "transcript": "...", "language": "...", "intent": "..." }

- WS /ws/dashboard
  WebSocket for real-time updates
```

### Configuration

Create `local.properties` in project root:

```properties
# Backend API
api.base.url=http://10.0.2.2:8000

# Claude API (for intent classification)
claude.api.key=your-claude-api-key-here

# Optional: WebSocket URL
ws.url=ws://10.0.2.2:8000/ws/dashboard
```

Note: `10.0.2.2` is the Android emulator's way to access `localhost` on your development machine.

## Implementation Priority

### Phase 1: Core Foundation (Essential)
1. ✅ Project setup (build.gradle, manifest)
2. ✅ Data models (LanguageResult, IntentResult, VoiceSession)
3. ✅ Application class
4. MainActivity with navigation
5. Theme and colors
6. Network module (Retrofit)
7. Database module (Room)

### Phase 2: Language Detection (Critical)
1. LanguageDetector utility (ML Kit)
2. DetectLanguageUseCase
3. VoiceRepository
4. API service integration

### Phase 3: Voice Test Screen (Core Feature)
1. VoiceTestScreen UI
2. VoiceViewModel
3. SpeechProcessor (Android SpeechRecognizer)
4. TTSManager
5. Voice components (waveform, confidence meter)

### Phase 4: Intent Classification
1. ClaudeApiService
2. ClassifyIntentUseCase
3. ConfidenceGateEngine
4. Intent components (IntentCard)

### Phase 5: Call Simulator
1. SimulatorScreen UI
2. SimulatorViewModel
3. Timeline components
4. Payment flow simulation

### Phase 6: Dashboard & Analytics
1. DashboardScreen
2. DashboardViewModel
3. WebSocket integration
4. Charts (Koalaplot)
5. Real-time updates

### Phase 7: Audit & Testing
1. AuditLogScreen
2. LanguageStressTestScreen
3. Export functionality
4. Test phrases database

## Key Implementation Notes

### 1. Language Detection

Uses Google ML Kit for on-device detection, then validates with backend:

```kotlin
// Local detection (fast, offline)
val mlKitResult = languageIdentifier.identifyLanguage(text)

// Backend validation (accurate, uses trained detector)
val backendResult = apiService.detectLanguage(text)

// Combine results
val finalResult = if (backendResult.confidence > mlKitResult.confidence) {
    backendResult
} else {
    mlKitResult
}
```

### 2. Speech Recognition

Uses Android's built-in SpeechRecognizer:

```kotlin
val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, 
        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
    putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN") // or "en-IN", "kn-IN"
    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
}
recognizer.startListening(intent)
```

### 3. Text-to-Speech

Uses Android TTS with Indian language support:

```kotlin
val tts = TextToSpeech(context) { status ->
    if (status == TextToSpeech.SUCCESS) {
        tts.language = Locale("hi", "IN")
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
    }
}
```

### 4. Confidence Gating

Implements the same logic as Python backend:

```kotlin
fun evaluateConfidence(intent: IntentResult): ConfidenceGate {
    return when {
        intent.confidence >= 0.80f && !intent.ambiguityFlag -> 
            ConfidenceGate.PROCEED
        intent.confidence >= 0.60f -> 
            ConfidenceGate.ASK_CLARIFICATION
        intent.sentiment == Sentiment.ANGRY -> 
            ConfidenceGate.ESCALATE_TO_HUMAN
        else -> 
            ConfidenceGate.ASK_CLARIFICATION
    }
}
```

### 5. Real-time Updates

Uses OkHttp WebSocket for dashboard updates:

```kotlin
val webSocket = client.newWebSocket(request, object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        val update = gson.fromJson(text, DashboardUpdate::class.java)
        _dashboardState.update { it.copy(orders = update.orders) }
    }
})
```

## Testing Strategy

### Unit Tests
- LanguageDetector logic
- Intent classification parsing
- Confidence gate decisions
- Data model conversions

### Integration Tests
- API service calls
- Database operations
- WebSocket connections

### UI Tests
- Voice recording flow
- Navigation between screens
- Dashboard updates

## Performance Considerations

1. **Offline-first**: ML Kit language detection works offline
2. **Caching**: Room database caches all sessions
3. **Lazy loading**: Dashboard loads data incrementally
4. **Coroutines**: All network/DB operations on background threads
5. **Compose**: Efficient recomposition with remember/derivedStateOf

## Accessibility

1. **TalkBack support**: All UI elements have contentDescription
2. **Large text**: Supports system font scaling
3. **Color contrast**: Meets WCAG AA standards
4. **Haptic feedback**: Vibration for key actions

## Localization

Supports UI in:
- English (default)
- Hindi (हिंदी)
- Kannada (ಕನ್ನಡ)

Uses Noto Sans fonts for proper script rendering.

## Next Steps

1. **Complete MainActivity**: Set up navigation and bottom bar
2. **Implement VoiceTestScreen**: Core feature for testing
3. **Connect to backend**: Test API integration
4. **Add sample data**: Pre-populate for demo
5. **Polish UI**: Animations and transitions

## Resources

- [Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [ML Kit Language ID](https://developers.google.com/ml-kit/language/identification)
- [Android Speech Recognition](https://developer.android.com/reference/android/speech/SpeechRecognizer)
- [Hilt Dependency Injection](https://developer.android.com/training/dependency-injection/hilt-android)
- [Room Database](https://developer.android.com/training/data-storage/room)

## Support

For questions or issues:
1. Check the Python backend is running
2. Verify API endpoints in local.properties
3. Check Android logs for errors
4. Test with sample phrases from LanguageStressTest

---

**Status**: Foundation created, ready for implementation
**Next**: Implement MainActivity and navigation
