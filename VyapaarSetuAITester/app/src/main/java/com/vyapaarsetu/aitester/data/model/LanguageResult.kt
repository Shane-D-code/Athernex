package com.vyapaarsetu.aitester.data.model

/**
 * Result of language detection.
 * Maps to the Python backend's language detection output.
 */
data class LanguageResult(
    val primaryLanguage: String,        // "hi", "en", "kn", "mr", "hinglish"
    val displayName: String,            // "Hindi", "English", "Hinglish", etc.
    val confidence: Float,              // 0.0 - 1.0
    val isCodeMixed: Boolean,           // true for Hinglish, Kanglish
    val script: Script,                 // DEVANAGARI, LATIN, MIXED, KANNADA
    val allCandidates: List<LanguageCandidate> = emptyList()
)

data class LanguageCandidate(
    val languageCode: String,
    val confidence: Float
)

enum class Script {
    DEVANAGARI,     // Hindi, Marathi
    LATIN,          // English
    MIXED,          // Hinglish, Kanglish
    KANNADA,        // Kannada
    TELUGU,         // Telugu
    TAMIL,          // Tamil
    UNKNOWN
}

/**
 * Extension functions for display
 */
fun LanguageResult.getConfidenceColor(): androidx.compose.ui.graphics.Color {
    return when {
        confidence >= 0.80f -> androidx.compose.ui.graphics.Color(0xFF2E7D32) // Green
        confidence >= 0.60f -> androidx.compose.ui.graphics.Color(0xFFF57C00) // Orange
        else -> androidx.compose.ui.graphics.Color(0xFFC62828) // Red
    }
}

fun LanguageResult.getConfidenceLabel(): String {
    return when {
        confidence >= 0.80f -> "High"
        confidence >= 0.60f -> "Medium"
        else -> "Low"
    }
}

fun String.toDisplayLanguage(): String = when (this) {
    "hi" -> "Hindi"
    "en" -> "English"
    "kn" -> "Kannada"
    "mr" -> "Marathi"
    "te" -> "Telugu"
    "ta" -> "Tamil"
    "hinglish" -> "Hinglish 🇮🇳"
    "kanglish" -> "Kanglish"
    else -> this.uppercase()
}

fun String.toLanguageEmoji(): String = when (this) {
    "hi" -> "🇮🇳"
    "en" -> "🇬🇧"
    "kn" -> "🇮🇳"
    "mr" -> "🇮🇳"
    "te" -> "🇮🇳"
    "ta" -> "🇮🇳"
    "hinglish" -> "🇮🇳🇬🇧"
    "kanglish" -> "🇮🇳🇬🇧"
    else -> "🌐"
}
