# Implementation Plan: Multilingual Voice Order System

## Overview

This implementation plan converts the feature design into actionable coding tasks for building a self-hosted multilingual voice order system. The system uses free/open-source components: Whisper (STT), Ollama + LLaMA 3.1 (LLM), and Piper TTS (TTS). All implementations will use Python with GPU acceleration where applicable.

**Key Implementation Priorities:**
- Self-hosted infrastructure with GPU optimization
- Streaming audio pipeline for low latency
- Confidence-based clarification logic
- Fallback mechanisms for resilience
- Property-based testing for correctness validation

## Tasks

- [x] 1. Project setup and infrastructure configuration
  - Create Python project structure with virtual environment
  - Set up dependencies: faster-whisper, ollama-python, piper-tts, edge-tts, fastapi, websockets
  - Create configuration management system for service endpoints and thresholds
  - Set up logging infrastructure with structured logging (JSON format)
  - Create Docker Compose configuration for local service orchestration
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x]* 1.1 Validate hardware requirements and GPU availability
  - Write script to check NVIDIA GPU availability and CUDA version
  - Validate RTX 4060 8GB VRAM (or equivalent) is available
  - Check available disk space for model storage (~10GB)
  - Log hardware configuration and recommend optimizations
  - Warn if VRAM < 8GB (will need CPU fallback or smaller models)
  - _Requirements: 8.1_

- [x] 2. Deploy and configure self-hosted STT services
  - [x] 2.1 Set up faster-whisper-server for Whisper Medium
    - Install faster-whisper-server with CUDA 12.1+ support
    - Download and configure Whisper Medium model (optimized for 8GB VRAM)
    - Start faster-whisper-server on port 8000 with GPU acceleration
    - Configure streaming mode and word-level timestamps
    - Verify VRAM usage stays under 2GB during inference
    - _Requirements: 1.1, 1.4, 1.7, 8.2_
  
  - [x] 2.2 Set up Vosk as fallback STT service
    - Install Vosk with Indian language models (Hindi, Kannada, Marathi, English)
    - Create REST API wrapper for Vosk on port 8001
    - Configure streaming recognition with confidence scores
    - _Requirements: 1.1, 19.1, 8.2_
  
  - [x] 2.3 Implement STT engine interface and client
    - Create STTEngine abstract base class with interface methods
    - Implement WhisperSTTEngine client for faster-whisper-server API
    - Implement VoskSTTEngine client for Vosk API
    - Add streaming session management and audio chunk processing
    - Implement word-level confidence extraction from API responses
    - _Requirements: 1.1, 1.4, 1.5, 1.7_

- [x] 3. Deploy and configure self-hosted LLM services
  - [x] 3.1 Set up Ollama with LLaMA 3.1 8B (4-bit quantized)
    - Install Ollama and pull llama3.1:8b-instruct-q4_K_M model (4-bit quantized)
    - Configure Ollama server on port 11434
    - Test JSON mode output and verify GPU utilization
    - Verify VRAM usage stays under 5GB during inference
    - Confirm total VRAM (Whisper + LLaMA) stays under 7GB
    - _Requirements: 2.1, 2.8, 8.3_
  
  - [x] 3.2 Configure Hugging Face Inference API as fallback
    - Set up Hugging Face API client with authentication
    - Configure meta-llama/Llama-3.1-8B-Instruct endpoint
    - Implement rate limiting for free tier (30 requests/hour)
    - _Requirements: 2.1, 19.2, 18.1, 18.2_
  
  - [x] 3.3 Implement LLM processor interface and client
    - Create LLMProcessor abstract base class with interface methods
    - Implement OllamaLLMProcessor client for Ollama API
    - Implement HuggingFaceLLMProcessor client for HF Inference API
    - Design prompt templates for intent detection and data extraction
    - Implement JSON schema validation for structured output
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7_

- [x] 4. Deploy and configure self-hosted TTS services
  - [x] 4.1 Set up Piper TTS with Indian language models
    - Install piper-tts and download hi-IN and en-IN voice models
    - Create REST API wrapper for Piper on port 8002
    - Configure streaming audio output (22kHz, PCM_16)
    - _Requirements: 5.1, 5.3, 5.7, 8.4_
  
  - [x] 4.2 Configure Edge TTS as fallback
    - Install edge-tts npm package and create Python wrapper
    - Configure Indian language voices (hi-IN-SwaraNeural, en-IN-NeerjaNeural)
    - Implement streaming synthesis with async/await
    - _Requirements: 5.1, 5.3, 19.3, 8.4_
  
  - [x] 4.3 Implement TTS engine interface and client
    - Create TTSEngine abstract base class with interface methods
    - Implement PiperTTSEngine client for Piper API
    - Implement EdgeTTSEngine client for Edge TTS
    - Add audio format conversion and streaming support
    - _Requirements: 5.1, 5.2, 5.3, 5.7, 5.8_

- [x] 5. Implement audio processing pipeline components
  - [x] 5.1 Implement Voice Activity Detection (VAD)
    - Integrate WebRTC VAD with aggressiveness level 2
    - Implement speech onset detection (<50ms target)
    - Implement speech offset detection (<300ms target)
    - Add audio buffering for pre-roll capture
    - _Requirements: 14.4, 14.5, 14.6, 14.7_
  
  - [x] 5.2 Implement echo cancellation and noise suppression
    - Integrate acoustic echo cancellation library (e.g., speexdsp)
    - Implement noise suppression with 15dB reduction target
    - Maintain signal-to-noise ratio above 20dB
    - Process within 20ms latency budget
    - _Requirements: 16.1, 16.2, 16.3, 16.4_
  
  - [x] 5.3 Implement audio buffer manager
    - Create AudioBufferManager class for streaming audio chunks
    - Support 16kHz sample rate, PCM_16 encoding, mono channel
    - Implement chunk size management (20-100ms)
    - Add buffer overflow protection and memory management
    - _Requirements: 14.1, 14.6, 14.7_

- [x] 6. Implement confidence scoring and analysis
  - [x] 6.1 Implement Confidence Estimation Module (CEM)
    - Extract word-level confidence scores from STT output
    - Calculate utterance-level confidence by aggregating word scores
    - Implement minimum word confidence detection (<0.4 threshold)
    - Generate confidence metadata for downstream components
    - _Requirements: 1.4, 1.5, 3.3, 12.8_
  
  - [x] 6.2 Implement confidence analyzer
    - Create ConfidenceAnalyzer class with combined scoring algorithm
    - Implement weighted combination: 0.4 * STT + 0.6 * LLM
    - Apply word-level penalty for low-confidence words (<0.4)
    - Apply missing fields penalty (0.15 per missing field)
    - Implement intent-specific threshold checking
    - Generate clarification recommendations with reasons
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 6.3 Write property test for confidence score bounds
    - **Property 1: Confidence score bounds**
    - **Validates: Requirements 1.5, 2.7, 3.5**
    - Test that all confidence scores are in range [0.0, 1.0]
    - Test that combined scores never exceed bounds after penalties
  
  - [ ]* 6.4 Write property test for clarification threshold consistency
    - **Property 2: Clarification threshold consistency**
    - **Validates: Requirements 3.1, 3.2, 3.7**
    - Test that scores below threshold always trigger clarification
    - Test that scores above threshold never trigger clarification

- [x] 7. Implement language detection and dominant language selection
  - [x] 7.1 Implement language detection from STT output
    - Extract language labels from word-level STT metadata
    - Identify unique languages in code-mixed speech
    - Calculate language statistics (word count, duration, percentage)
    - _Requirements: 1.2, 1.3, 13.1, 13.4_
  
  - [x] 7.2 Implement dominant language selection algorithm
    - Sort languages by word count and duration
    - Handle ambiguous cases (within 10% difference) using first-word language
    - Set is_code_mixed flag when multiple languages detected
    - _Requirements: 5.2, 13.2, 13.3, 13.5_
  
  - [ ]* 7.3 Write property test for language invariance
    - **Property 3: Language invariance**
    - **Validates: Requirements 12.4, 10.3**
    - Test that same intent is extracted regardless of language used
    - Test with Hindi, Kannada, Marathi, English variations

- [x] 8. Implement structured data extraction and validation
  - [x] 8.1 Define JSON schema for structured order data
    - Create Pydantic models for StructuredOrderData
    - Define schema for intent, items, quantities, delivery_time, special_instructions
    - Add validation rules for required fields and data types
    - _Requirements: 2.3, 2.4, 2.5, 4.1, 4.2_
  
  - [x] 8.2 Implement LLM prompt engineering for data extraction
    - Design system prompt for order understanding and extraction
    - Create few-shot examples for each intent type
    - Implement JSON mode output formatting
    - Add instructions for missing field identification
    - _Requirements: 2.1, 2.2, 2.3, 2.6_
  
  - [x] 8.3 Implement relative time conversion
    - Parse relative time expressions ("in 30 minutes", "tomorrow", "at 5pm")
    - Convert to absolute ISO 8601 timestamps
    - Handle timezone considerations
    - _Requirements: 4.4_
  
  - [ ]* 8.4 Write property test for round-trip consistency
    - **Property 4: Round-trip consistency**
    - **Validates: Requirements 12.1, 4.1**
    - Test that serializing then deserializing StructuredOrderData produces equivalent data
    - Test with various order configurations
  
  - [ ]* 8.5 Write property test for semantic equivalence
    - **Property 5: Semantic equivalence**
    - **Validates: Requirements 12.5, 2.3**
    - Test that different phrasings of same order produce equivalent StructuredOrderData
    - Test with paraphrased utterances

- [x] 9. Checkpoint 1 - Ensure core components are functional
  - Verify all service deployments are working (Whisper, Ollama, Piper)
  - Verify STT, LLM, and TTS clients can communicate with services
  - Run basic smoke tests for each component
  - Check VRAM usage is within limits (<7GB total)
  - Ensure all tests pass, ask the user if questions arise before proceeding

- [ ] 10. Implement dialogue state tracking and context management
  - [ ] 10.1 Create dialogue state data model
    - Define DialogueState Pydantic model with session_id, turn_count, slots
    - Implement slot-value pairs with confidence and last_updated_turn
    - Add conversation_history array with turn tracking
    - Create anaphora_context for entity references
    - _Requirements: 11.3, 11.8_
  
  - [ ] 10.2 Implement DialogueStateTracker class
    - Implement session creation and retrieval methods
    - Implement updateSession for adding new conversation turns
    - Implement mergeSlots for combining new data with existing slots
    - Add session expiration logic (10 turns or 5 minutes)
    - Implement context summarization when exceeding 8000 tokens
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6, 11.7_
  
  - [ ] 10.3 Implement anaphora resolution
    - Define anaphora patterns for order, item, and time references
    - Implement pattern matching in user utterances
    - Resolve references using anaphora_context from dialogue state
    - Update anaphora_context with newly mentioned entities
    - _Requirements: 11.4_
  
  - [ ]* 10.4 Write property test for context preservation
    - **Property 6: Context preservation**
    - **Validates: Requirements 11.1, 11.2**
    - Test that information from earlier turns is preserved in dialogue state
    - Test that slot updates don't lose unrelated information

- [ ] 11. Implement order processing and execution
  - [ ] 11.1 Create Order Manager component
    - Implement OrderManager class for validated order processing
    - Implement place_order handler to create new order records
    - Implement modify_order handler to update existing orders
    - Implement cancel_order handler to mark orders as cancelled
    - Generate confirmation messages for each action
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 11.2 Write unit tests for order manager
    - Test order creation with valid structured data
    - Test order modification with partial updates
    - Test order cancellation flow
    - Test error handling for invalid order IDs

- [ ] 12. Implement API integration and service orchestration
  - [ ] 12.1 Implement rate limiter
    - Create RateLimiter class with per-service request tracking
    - Implement sliding window rate limiting algorithm
    - Configure limits: Whisper (10/min), Ollama (5/min), Piper (50/min)
    - Add waitForSlot method with exponential backoff
    - Implement usage percentage monitoring (warn at 80%)
    - _Requirements: 18.1, 18.2, 18.4_
  
  - [ ] 12.2 Implement quota manager for resource limits
    - Create QuotaManager class tracking GPU memory, CPU, RAM, concurrent requests
    - Implement resource quota checking before accepting requests
    - Add system metrics monitoring and logging
    - Implement request start/end tracking for concurrency limits
    - _Requirements: 18.1, 18.3, 18.5_
  
  - [ ] 12.3 Implement service orchestrator with fallback logic
    - Create ServiceOrchestrator class managing primary/fallback providers
    - Implement executeWithFallback for automatic service switching
    - Add error counting and threshold-based fallback triggers
    - Implement automatic primary service restoration after 5 minutes
    - Add health check methods for each service
    - _Requirements: 19.1, 19.2, 19.3, 19.5, 19.6_
  
  - [ ] 12.4 Implement retry strategy with exponential backoff
    - Create RetryStrategy class with configurable retry options
    - Implement exponential backoff with jitter (prevent thundering herd)
    - Add retryable error detection (5xx, 429, network errors)
    - Configure max retries (3) and max delay (10s)
    - _Requirements: 9.1, 9.3, 19.6_

- [ ] 13. Implement caching for performance optimization
  - [ ] 13.1 Implement LLM response cache
    - Create LLMCache class with SHA-256 key generation
    - Implement LRU eviction policy (max 1000 entries)
    - Add TTL-based expiration (1 hour)
    - Track cache hit counts for analytics
    - _Requirements: 20.1, 20.3, 20.5_
  
  - [ ] 13.2 Implement TTS audio cache
    - Create TTSCache class with language:voice:text keys
    - Implement FIFO eviction policy (max 500 entries)
    - Add TTL-based expiration (1 hour)
    - Store audio as compressed buffers
    - _Requirements: 20.2, 20.4, 20.5_
  
  - [ ] 13.3 Integrate caching into service clients
    - Add cache lookup before LLM API calls
    - Add cache lookup before TTS API calls
    - Implement cache invalidation on configuration changes
    - _Requirements: 20.1, 20.2, 20.6_
  
  - [ ]* 13.4 Write property test for cache consistency
    - **Property 7: Cache consistency**
    - **Validates: Requirements 20.1, 20.2**
    - Test that cached results match fresh API results
    - Test that cache invalidation works correctly

- [ ] 14. Implement barge-in detection logic
  - [ ] 14.1 Implement barge-in detection using VAD
    - Monitor for speech input during TTS playback using VAD component
    - Detect barge-in within 200ms of speech onset
    - Expose stop signal for TTS output when barge-in detected
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [ ] 14.2 Implement conversation context preservation for barge-in
    - Save interrupted conversation state in DialogueStateTracker
    - Restart pipeline processing with new input
    - Handle barge-in during order confirmation specially
    - _Requirements: 15.4, 15.5_

- [ ] 16. Implement end-to-end voice processing pipeline
  - [ ] 16.1 Create main pipeline orchestrator
    - Implement VoicePipeline class coordinating all components
    - Wire together: Audio Input → VAD → Echo Cancel → STT → LLM → Confidence → Order Manager → TTS → Audio Output
    - Add error handling and logging at each stage
    - Implement latency tracking for each component
    - _Requirements: 7.1, 7.5, 7.6, 7.7_
  
  - [ ] 16.2 Implement streaming audio processing
    - Process audio in real-time chunks (20-100ms)
    - Begin STT transcription before complete utterance
    - Stream TTS output as it's generated
    - _Requirements: 1.7, 7.8_
  
  - [ ] 16.3 Implement clarification dialogue flow
    - Detect when clarification is needed from confidence analyzer
    - Generate clarification questions based on clarification_reason
    - Wait for customer response and resume processing
    - Merge clarification response with original order data
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.7_
  
  - [ ]* 16.4 Write property test for idempotence
    - **Property 8: Idempotence**
    - **Validates: Requirements 12.9**
    - Test that processing same utterance multiple times produces identical StructuredOrderData
    - Test with various utterances and intents
  
  - [ ]* 16.5 Write integration tests for end-to-end pipeline
    - Test complete flow from audio input to audio output
    - Test clarification dialogue flow
    - Test fallback service switching
    - Test error handling and recovery

- [ ] 17. Checkpoint 2 - Ensure pipeline integration is working
  - Verify end-to-end pipeline processes audio correctly
  - Test clarification dialogue flow with sample utterances
  - Verify fallback mechanisms switch correctly on errors
  - Check latency is within acceptable range (p95 < 3s)
  - Ensure all integration tests pass, ask the user if questions arise before proceeding

- [ ] 18. Implement monitoring and observability
  - [ ] 18.1 Set up structured logging
    - Configure JSON logging with timestamp, level, component, message
    - Log component latencies for each request
    - Log confidence scores, intent classifications, clarification triggers
    - Log language detection results and dominant language
    - Log error stack traces with context
    - _Requirements: 21.1, 21.2, 21.5, 21.6_
  
  - [ ] 18.2 Implement metrics collection
    - Create MetricsCollector class for latency percentiles (p50, p95, p99)
    - Track error rates per component
    - Track cache hit rates
    - Track API usage counts
    - _Requirements: 21.3, 21.4, 18.4_
  
  - [ ] 18.3 Create monitoring endpoint
    - Implement /metrics endpoint exposing Prometheus-compatible metrics
    - Implement /health endpoint for service health checks
    - Add real-time metrics dashboard (optional)
    - _Requirements: 21.7_

- [ ] 19. Implement error handling and graceful degradation
  - [ ] 19.1 Implement error response generation
    - Create error message templates for each failure type
    - Generate voice responses for errors using TTS
    - Implement retry prompts for STT failures
    - Implement human support escalation for repeated failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 19.2 Implement graceful degradation patterns
    - Implement text-only mode when TTS unavailable
    - Implement rule-based intent detection when LLM unavailable
    - Implement quality reduction for TTS (high → medium → low)
    - _Requirements: 19.4_
  
  - [ ]* 19.3 Write unit tests for error handling
    - Test STT failure recovery
    - Test LLM failure recovery
    - Test TTS failure recovery
    - Test network error handling

- [ ] 20. Implement few-shot learning for new intents
  - [ ] 20.1 Create intent management interface
    - Implement addIntent method in LLMProcessor
    - Store few-shot examples in configuration
    - Update prompt templates dynamically with new examples
    - _Requirements: 17.1, 17.2, 17.5_
  
  - [ ] 20.2 Implement intent classification with new intents
    - Extend prompt to include both original and new intents
    - Validate accuracy on original intents after adding new ones
    - _Requirements: 17.3, 17.4_
  
  - [ ]* 20.3 Write unit tests for few-shot learning
    - Test adding new intents with 3-5 examples
    - Test classification accuracy on original intents (>90%)
    - Test classification of new intent examples

- [ ] 21. Implement optional emotion detection (if time permits)
  - [ ] 21.1 Implement acoustic emotion detection
    - Extract acoustic features: pitch, energy, speaking rate, MFCCs
    - Implement rule-based emotion classification (neutral, happy, frustrated, angry, confused)
    - Calculate emotion confidence scores
    - Complete processing within 100ms
    - _Requirements: 22.1, 22.2, 22.3_
  
  - [ ] 21.2 Implement emotion-aware response generation
    - Adjust TTS prosody based on detected emotion
    - Implement empathetic tone for frustration/anger
    - Implement enthusiastic tone for happiness
    - Escalate to human support when frustration/anger detected with confidence >0.7
    - _Requirements: 22.4, 22.5, 23.1, 23.2, 23.3, 23.4_
  
  - [ ]* 21.3 Write unit tests for emotion detection
    - Test emotion classification accuracy (>85%)
    - Test latency (<100ms)
    - Test escalation triggers

- [ ] 22. Package ML pipeline and create API layer
  - [ ] 22.1 Create VoicePipelineSDK Python package
    - Expose VoicePipeline class with process_audio(audio_bytes) → OrderResult
    - Expose individual components: transcribe(), detect_intent(), synthesize()
    - Add typed dataclasses for all inputs/outputs (Pydantic models)
    - Provide clear __init__.py exports for teammates to import
    - _Requirements: 7.1_
  
  - [ ] 22.2 Implement FastAPI REST API endpoints
    - Create POST /api/v1/transcribe endpoint for audio transcription
    - Create POST /api/v1/process endpoint for complete pipeline processing
    - Create POST /api/v1/synthesize endpoint for text-to-speech
    - Create GET /api/v1/config endpoint for runtime configuration
    - Add request validation, error handling, and CORS middleware
    - _Requirements: 7.1, 8.5_
  
  - [ ] 22.3 Implement WebSocket endpoint for streaming
    - Create /ws/voice endpoint for bidirectional audio streaming
    - Implement session management for WebSocket connections
    - Handle connection lifecycle (connect, disconnect, error, reconnect)
    - _Requirements: 14.2, 14.3_
  
  - [ ] 22.4 Add API documentation
    - Generate OpenAPI/Swagger documentation automatically
    - Document request/response schemas with examples
    - Provide usage examples for REST and WebSocket endpoints
    - Document configuration options and environment variables

- [ ] 23. Model setup and ML documentation
  - [ ] 23.1 Create automated model download script
    - Script to download Whisper Medium, LLaMA 3.1 8B Q4, Piper TTS models
    - Verify GPU availability and CUDA version
    - Validate VRAM fits Whisper Medium (~2GB) + LLaMA Q4 (~5GB)
    - Print hardware summary and recommended config
  
  - [ ] 23.2 Create ML setup documentation
    - Document hardware requirements (RTX 4060 8GB VRAM, i7-14700HX, 16GB RAM)
    - Document model optimization for 8GB VRAM (Whisper Medium + LLaMA Q4)
    - Document CUDA 12.1+ and cuDNN 8.9+ setup for RTX 4060
    - Add troubleshooting guide (OOM errors, CUDA errors, VRAM monitoring)
  
  - [ ] 23.3 Create performance optimization guide
    - Document GPU optimization tips (faster-whisper CTranslate2, Ollama GPU layers)
    - Document model quantization options (Q4_K_M vs Q5_K_M tradeoffs)
    - Document caching strategies for LLM and TTS responses
    - Document latency benchmarks on RTX 4060 + i7-14700HX

- [ ] 24. Checkpoint 3 - Complete system validation and deployment readiness
  - Run full end-to-end system tests with real audio samples
  - Verify end-to-end latency meets targets (p95 < 3150ms)
  - Verify all fallback mechanisms work correctly under load
  - Verify monitoring and logging are operational
  - Test with code-mixed speech (Hindi-English, Kannada-English)
  - Verify VRAM usage remains stable under continuous operation
  - Ensure all tests pass, ask the user if deployment is ready

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- All implementations use Python with GPU acceleration where applicable
- Self-hosted infrastructure prioritized to minimize API costs
- Fallback mechanisms ensure resilience and graceful degradation
