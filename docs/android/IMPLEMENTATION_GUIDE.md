# VyapaarSetu AI Tester - Implementation Guide

## Quick Start

This guide will help you build the Android app step-by-step to work with your existing Python voice-order-system backend.

## Prerequisites

✅ Python backend running (voice-order-system)
✅ Android Studio Hedgehog or later
✅ JDK 17
✅ Android SDK 34
✅ Device/Emulator with API 26+

## Step 1: Project Setup

### 1.1 Create local.properties

```properties
# In project root: VyapaarSetuAITester/local.properties

# Point to your Python backend
# Use 10.0.2.2 for Android emulator to access localhost
api.base.url=http://10.0.2.2:8000

# Claude API key for intent classification
claude.api.key=your-claude-api-key-here

# WebSocket URL for real-time updates
ws.url=ws://10.0.2.2:8000/ws/dashboard
```

### 1.2 Verify Backend is Running

```bash
# In voice-order-system directory
cd Athernex/voice-order-system

# Start the API server
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test endpoint
curl http://localhost:8000/api/health
```

### 1.3 Sync Gradle

Open Android Studio → File → Sync Project with Gradle Files

## Step 2: Core Files to Create

### 2.1 MainActivity.kt

```kotlin
package com.vyapaarsetu.aitester

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.vyapaarsetu.aitester.ui.navigation.NavGraph
import com.vyapaarsetu.aitester.ui.navigation.Screen
import com.vyapaarsetu.aitester.ui.theme.VyapaarSetuAITesterTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            VyapaarSetuAITesterTheme {
                MainScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen() {
    val navController = rememberNavController()
    var selectedScreen by remember { mutableStateOf(Screen.Home) }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    icon = { Text("🏠") },
                    label = { Text("Home") },
                    selected = selectedScreen == Screen.Home,
                    onClick = {
                        selectedScreen = Screen.Home
                        navController.navigate(Screen.Home.route)
                    }
                )
                NavigationBarItem(
                    icon = { Text("🎤") },
                    label = { Text("Voice Test") },
                    selected = selectedScreen == Screen.VoiceTest,
                    onClick = {
                        selectedScreen = Screen.VoiceTest
                        navController.navigate(Screen.VoiceTest.route)
                    }
                )
                NavigationBarItem(
                    icon = { Text("▶") },
                    label = { Text("Simulator") },
                    selected = selectedScreen == Screen.Simulator,
                    onClick = {
                        selectedScreen = Screen.Simulator
                        navController.navigate(Screen.Simulator.route)
                    }
                )
                NavigationBarItem(
                    icon = { Text("📊") },
                    label = { Text("Dashboard") },
                    selected = selectedScreen == Screen.Dashboard,
                    onClick = {
                        selectedScreen = Screen.Dashboard
                        navController.navigate(Screen.Dashboard.route)
                    }
                )
                NavigationBarItem(
                    icon = { Text("📋") },
                    label = { Text("Audit") },
                    selected = selectedScreen == Screen.AuditLog,
                    onClick = {
                        selectedScreen = Screen.AuditLog
                        navController.navigate(Screen.AuditLog.route)
                    }
                )
            }
        }
    ) { paddingValues ->
        NavGraph(
            navController = navController,
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        )
    }
}
```

### 2.2 Navigation Setup

Create `ui/navigation/NavGraph.kt`:

```kotlin
package com.vyapaarsetu.aitester.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.vyapaarsetu.aitester.ui.screens.*

sealed class Screen(val route: String) {
    object Home : Screen("home")
    object VoiceTest : Screen("voice_test")
    object Simulator : Screen("simulator")
    object Dashboard : Screen("dashboard")
    object AuditLog : Screen("audit_log")
    object LanguageStressTest : Screen("stress_test")
}

@Composable
fun NavGraph(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route,
        modifier = modifier
    ) {
        composable(Screen.Home.route) {
            HomeScreen(navController)
        }
        composable(Screen.VoiceTest.route) {
            VoiceTestScreen()
        }
        composable(Screen.Simulator.route) {
            SimulatorScreen()
        }
        composable(Screen.Dashboard.route) {
            DashboardScreen()
        }
        composable(Screen.AuditLog.route) {
            AuditLogScreen()
        }
        composable(Screen.LanguageStressTest.route) {
            LanguageStressTestScreen()
        }
    }
}
```

### 2.3 Theme Setup

Create `ui/theme/Color.kt`:

```kotlin
package com.vyapaarsetu.aitester.ui.theme

import androidx.compose.ui.graphics.Color

// VyapaarSetu Brand Colors
val VyapaarPrimary = Color(0xFF1A237E)      // Deep indigo (trust)
val VyapaarSecondary = Color(0xFFFF6F00)    // Paytm orange (commerce)
val VyapaarTertiary = Color(0xFF2E7D32)     // Green (success)
val VyapaarError = Color(0xFFC62828)        // Red (error)

// Confidence Colors
val ConfidenceHigh = Color(0xFF2E7D32)      // Green >80%
val ConfidenceMedium = Color(0xFFF57C00)    // Orange 60-80%
val ConfidenceLow = Color(0xFFC62828)       // Red <60%

// Language Colors
val HindiColor = Color(0xFFFF9933)          // Saffron
val EnglishColor = Color(0xFF1976D2)        // Blue
val KannadaColor = Color(0xFFFFC107)        // Yellow
val MarathiColor = Color(0xFF9C27B0)        // Purple
val HinglishColor = Color(0xFFFF6F00)       // Orange

// Background
val BackgroundLight = Color(0xFFFAFAFA)
val SurfaceLight = Color(0xFFFFFFFF)
```

Create `ui/theme/Theme.kt`:

```kotlin
package com.vyapaarsetu.aitester.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = VyapaarPrimary,
    secondary = VyapaarSecondary,
    tertiary = VyapaarTertiary,
    error = VyapaarError,
    background = BackgroundLight,
    surface = SurfaceLight
)

@Composable
fun VyapaarSetuAITesterTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}
```

## Step 3: Backend Integration

### 3.1 API Service

Create `data/remote/ApiService.kt`:

```kotlin
package com.vyapaarsetu.aitester.data.remote

import com.vyapaarsetu.aitester.data.model.IntentResult
import com.vyapaarsetu.aitester.data.model.LanguageResult
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    
    @POST("/api/detect-language")
    suspend fun detectLanguage(
        @Body request: LanguageDetectionRequest
    ): LanguageDetectionResponse
    
    @POST("/api/classify-intent")
    suspend fun classifyIntent(
        @Body request: IntentClassificationRequest
    ): IntentResult
    
    @POST("/api/process-speech")
    suspend fun processSpeech(
        @Body request: SpeechProcessingRequest
    ): SpeechProcessingResponse
}

data class LanguageDetectionRequest(
    val text: String
)

data class LanguageDetectionResponse(
    val language: String,
    val confidence: Float,
    val is_code_mixed: Boolean,
    val method: String
)

data class IntentClassificationRequest(
    val text: String,
    val language: String
)

data class SpeechProcessingRequest(
    val text: String,
    val language: String = "auto"
)

data class SpeechProcessingResponse(
    val transcript: String,
    val language: LanguageResult,
    val intent: IntentResult,
    val bot_response: String
)
```

### 3.2 Network Module

Create `di/NetworkModule.kt`:

```kotlin
package com.vyapaarsetu.aitester.di

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.vyapaarsetu.aitester.BuildConfig
import com.vyapaarsetu.aitester.data.remote.ApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideGson(): Gson = GsonBuilder()
        .setLenient()
        .create()
    
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        gson: Gson
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()
    
    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService =
        retrofit.create(ApiService::class.java)
}
```

## Step 4: Database Setup

### 4.1 Room Database

Create `data/local/AppDatabase.kt`:

```kotlin
package com.vyapaarsetu.aitester.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.vyapaarsetu.aitester.data.model.Order
import com.vyapaarsetu.aitester.data.model.VoiceSession

@Database(
    entities = [VoiceSession::class, Order::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun voiceSessionDao(): VoiceSessionDao
    abstract fun orderDao(): OrderDao
}
```

Create `data/local/Converters.kt`:

```kotlin
package com.vyapaarsetu.aitester.data.local

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class Converters {
    private val gson = Gson()
    
    @TypeConverter
    fun fromStringMap(value: Map<String, String>): String {
        return gson.toJson(value)
    }
    
    @TypeConverter
    fun toStringMap(value: String): Map<String, String> {
        val type = object : TypeToken<Map<String, String>>() {}.type
        return gson.fromJson(value, type)
    }
}
```

### 4.2 Database Module

Create `di/DatabaseModule.kt`:

```kotlin
package com.vyapaarsetu.aitester.di

import android.content.Context
import androidx.room.Room
import com.vyapaarsetu.aitester.data.local.AppDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideAppDatabase(
        @ApplicationContext context: Context
    ): AppDatabase = Room.databaseBuilder(
        context,
        AppDatabase::class.java,
        "vyapaarsetu_db"
    ).build()
    
    @Provides
    fun provideVoiceSessionDao(database: AppDatabase) =
        database.voiceSessionDao()
    
    @Provides
    fun provideOrderDao(database: AppDatabase) =
        database.orderDao()
}
```

## Step 5: Testing the Setup

### 5.1 Create a Simple Home Screen

Create `ui/screens/HomeScreen.kt`:

```kotlin
package com.vyapaarsetu.aitester.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.vyapaarsetu.aitester.ui.navigation.Screen

@Composable
fun HomeScreen(navController: NavController) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically)
    ) {
        Text(
            text = "🎤 VyapaarSetu AI Tester",
            style = MaterialTheme.typography.headlineLarge
        )
        
        Text(
            text = "Multilingual Voice Commerce Testing Harness",
            style = MaterialTheme.typography.bodyLarge
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        ModuleCard(
            icon = "🎤",
            title = "Voice Test",
            description = "Test speech recognition, language detection & intent classification",
            onClick = { navController.navigate(Screen.VoiceTest.route) }
        )
        
        ModuleCard(
            icon = "▶",
            title = "Call Simulator",
            description = "Simulate full order → call → payment → soundbox flow",
            onClick = { navController.navigate(Screen.Simulator.route) }
        )
        
        ModuleCard(
            icon = "📊",
            title = "Dashboard",
            description = "Real-time analytics and order tracking",
            onClick = { navController.navigate(Screen.Dashboard.route) }
        )
        
        ModuleCard(
            icon = "🌐",
            title = "Language Stress Test",
            description = "Validate Hinglish, Kanglish detection accuracy",
            onClick = { navController.navigate(Screen.LanguageStressTest.route) }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModuleCard(
    icon: String,
    title: String,
    description: String,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = icon,
                style = MaterialTheme.typography.displaySmall,
                modifier = Modifier.padding(end = 16.dp)
            )
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleLarge
                )
                Text(
                    text = description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
```

### 5.2 Create Placeholder Screens

For now, create simple placeholder screens for other routes:

```kotlin
// ui/screens/VoiceTestScreen.kt
@Composable
fun VoiceTestScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("Voice Test Screen - Coming Soon")
    }
}

// ui/screens/SimulatorScreen.kt
@Composable
fun SimulatorScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("Simulator Screen - Coming Soon")
    }
}

// ui/screens/DashboardScreen.kt
@Composable
fun DashboardScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("Dashboard Screen - Coming Soon")
    }
}

// ui/screens/AuditLogScreen.kt
@Composable
fun AuditLogScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("Audit Log Screen - Coming Soon")
    }
}

// ui/screens/LanguageStressTestScreen.kt
@Composable
fun LanguageStressTestScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("Language Stress Test - Coming Soon")
    }
}
```

## Step 6: Run the App

1. **Start Python Backend**:
   ```bash
   cd Athernex/voice-order-system/src/api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Run Android App**:
   - Open project in Android Studio
   - Select device/emulator
   - Click Run ▶️

3. **Verify**:
   - App launches with Home screen
   - Bottom navigation works
   - Can navigate between screens

## Next Steps

Now that the foundation is set up, you can implement:

1. **Voice Test Screen** - Core feature with speech recognition
2. **Language Detection** - ML Kit + Backend integration
3. **Intent Classification** - Claude API integration
4. **Call Simulator** - Full flow demonstration
5. **Dashboard** - Real-time analytics

See `PROJECT_STRUCTURE.md` for detailed file structure and `README.md` for feature descriptions.

## Troubleshooting

### Backend Connection Issues

```kotlin
// Test backend connectivity
curl http://10.0.2.2:8000/api/health

// Check Android logs
adb logcat | grep "VyapaarSetu"
```

### Build Errors

```bash
# Clean and rebuild
./gradlew clean
./gradlew build

# Sync Gradle
File → Sync Project with Gradle Files
```

### Permission Issues

Make sure AndroidManifest.xml has:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

And request at runtime using Accompanist Permissions.

---

**Status**: Foundation complete, ready for feature implementation
**Next**: Implement VoiceTestScreen with speech recognition
