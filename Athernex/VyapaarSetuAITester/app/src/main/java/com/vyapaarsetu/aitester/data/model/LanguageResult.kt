package com.vyapaarsetu.aitester.data.model

data class LanguageResult(
    val language: String,
    val confidence: Float,
    val isCodeMixed: Boolean,
    val method: String,
    val script: String,
    val displayName: String
)

enum class SupportedLanguage(val code: String, val displayName: String, val emoji: String) {
    HINDI("hi", "Hindi", "🇮🇳"),
    ENGLISH("en", "English", "🇬🇧"),
    KANNADA("kn", "Kannada", "🇮🇳"),
    MARATHI("mr", "Marathi", "🇮🇳"),
    HINGLISH("hinglish", "Hinglish", "🇮🇳🇬🇧");
    
    companion object {
        fun fromCode(code: String): SupportedLanguage? {
            return values().find { it.code == code }
        }
    }
}
