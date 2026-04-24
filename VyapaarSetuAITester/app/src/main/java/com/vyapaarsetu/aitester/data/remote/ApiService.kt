package com.vyapaarsetu.aitester.data.remote

import com.vyapaarsetu.aitester.data.model.IntentResult
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/**
 * API service for communicating with Python backend.
 * Base URL configured in BuildConfig.API_BASE_URL
 */
interface ApiService {
    
    /**
     * Detect language of input text.
     * Endpoint: POST /api/detect-language
     */
    @POST("detect-language")
    suspend fun detectLanguage(
        @Body request: LanguageDetectionRequest
    ): LanguageDetectionResponse
    
    /**
     * Classify intent of user speech.
     * Endpoint: POST /api/classify-intent
     */
    @POST("classify-intent")
    suspend fun classifyIntent(
        @Body request: IntentClassificationRequest
    ): IntentClassificationResponse
    
    /**
     * Process speech end-to-end.
     * Endpoint: POST /api/process-speech
     */
    @POST("process-speech")
    suspend fun processSpeech(
        @Body request: SpeechProcessingRequest
    ): SpeechProcessingResponse
    
    /**
     * Test a phrase for accuracy.
     * Endpoint: POST /api/test-phrase
     */
    @POST("test-phrase")
    suspend fun testPhrase(
        @Body request: TestPhraseRequest
    ): TestPhraseResponse
    
    /**
     * Health check.
     * Endpoint: GET /health
     */
    @GET("health")
    suspend fun healthCheck(): HealthResponse
}

// ============================================================================
// Request Models
// ============================================================================

data class LanguageDetectionRequest(
    val text: String
)

data class IntentClassificationRequest(
    val text: String,
    val language: String
)

data class SpeechProcessingRequest(
    val text: String,
    val language: String = "auto",
    val session_id: String? = null
)

data class TestPhraseRequest(
    val text: String,
    val expected_language: String,
    val expected_intent: String? = null
)

// ============================================================================
// Response Models
// ============================================================================

data class LanguageDetectionResponse(
    val language: String,
    val confidence: Float,
    val is_code_mixed: Boolean,
    val method: String,
    val script: String,
    val display_name: String
)

data class IntentClassificationResponse(
    val primary_intent: String,
    val payment_intent: String,
    val modification_type: String?,
    val sentiment: String,
    val confidence: Float,
    val ambiguity_flag: Boolean,
    val clarification_needed: String?,
    val extracted_entities: Map<String, String>,
    val bot_response_suggestion: String
)

data class SpeechProcessingResponse(
    val transcript: String,
    val language: LanguageDetectionResponse,
    val intent: IntentClassificationResponse,
    val bot_response: String,
    val session_id: String,
    val processing_time_ms: Float
)

data class TestPhraseResponse(
    val text: String,
    val expected_language: String,
    val detected_language: String,
    val language_match: Boolean,
    val language_confidence: Float,
    val intent: String?,
    val intent_confidence: Float?,
    val processing_time_ms: Float
)

data class HealthResponse(
    val status: String,
    val version: String,
    val services: Map<String, Any>,
    val system_stats: Map<String, Any>
)
