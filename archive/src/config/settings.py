"""
Central configuration for the Multilingual Voice Order System.
All thresholds, model paths, and service endpoints are managed here.
Runtime-modifiable without code changes (via env vars or .env file).
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class STTSettings(BaseSettings):
    """Speech-to-Text configuration."""
    provider: str = Field(default="whisper", description="Primary STT provider: whisper | vosk")
    whisper_model: str = Field(default="medium", description="Whisper model size: tiny|base|small|medium|large-v3")
    whisper_device: str = Field(default="cuda", description="Device for Whisper inference: cuda | cpu")
    whisper_compute_type: str = Field(default="float16", description="Compute type: float16 | int8 | int8_float16")
    whisper_beam_size: int = Field(default=5, description="Beam size for decoding")
    whisper_language: Optional[str] = Field(default=None, description="Force language (None for auto-detect)")
    vosk_model_path: str = Field(default="models/vosk-model-hi", description="Path to Vosk model directory")

    model_config = {"env_prefix": "STT_"}


class LLMSettings(BaseSettings):
    """LLM Processor configuration."""
    provider: str = Field(default="ollama", description="Primary LLM provider: ollama | huggingface")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama3.1:8b-instruct-q4_K_M", description="Ollama model name")
    ollama_temperature: float = Field(default=0.0, description="Temperature for deterministic output")
    ollama_num_ctx: int = Field(default=4096, description="Context window size")
    hf_model_id: str = Field(default="meta-llama/Llama-3.1-8B-Instruct", description="HuggingFace model ID")
    hf_api_key: Optional[str] = Field(default=None, description="HuggingFace API key (free tier)")

    model_config = {"env_prefix": "LLM_"}


class TTSSettings(BaseSettings):
    """Text-to-Speech configuration."""
    provider: str = Field(default="edge", description="Primary TTS provider: piper | edge")
    piper_model_path: str = Field(default="models/piper", description="Path to Piper TTS models")
    edge_voice_hi: str = Field(default="hi-IN-SwaraNeural", description="Edge TTS Hindi voice")
    edge_voice_en: str = Field(default="en-IN-NeerjaNeural", description="Edge TTS English voice")
    edge_voice_kn: str = Field(default="kn-IN-GaganNeural", description="Edge TTS Kannada voice")
    edge_voice_mr: str = Field(default="mr-IN-AarohiNeural", description="Edge TTS Marathi voice")

    model_config = {"env_prefix": "TTS_"}


class ConfidenceSettings(BaseSettings):
    """Confidence thresholds for clarification decisions."""
    place_order: float = Field(default=0.85, description="Threshold for place_order intent")
    modify_order: float = Field(default=0.80, description="Threshold for modify_order intent")
    cancel_order: float = Field(default=0.90, description="Threshold for cancel_order intent")
    confirm_order: float = Field(default=0.80, description="Threshold for confirm_order intent")
    check_status: float = Field(default=0.75, description="Threshold for check_status intent")
    request_information: float = Field(default=0.70, description="Threshold for request_information intent")
    oos_intent: float = Field(default=0.50, description="Threshold for out-of-scope intent")
    word_level_threshold: float = Field(default=0.4, description="Min word-level confidence before flagging")
    stt_weight: float = Field(default=0.4, description="Weight for STT score in combined confidence")
    llm_weight: float = Field(default=0.6, description="Weight for LLM score in combined confidence")
    missing_field_penalty: float = Field(default=0.15, description="Penalty per missing required field")

    model_config = {"env_prefix": "CONFIDENCE_"}

    def get_threshold(self, intent: str) -> float:
        """Get the confidence threshold for a given intent."""
        thresholds = {
            "place_order": self.place_order,
            "modify_order": self.modify_order,
            "cancel_order": self.cancel_order,
            "confirm_order": self.confirm_order,
            "check_status": self.check_status,
            "request_information": self.request_information,
            "oos_intent": self.oos_intent,
        }
        return thresholds.get(intent, 0.80)


class ContextSettings(BaseSettings):
    """Dialogue context management configuration."""
    max_turns: int = Field(default=10, description="Maximum conversation turns before expiry")
    max_duration_seconds: int = Field(default=300, description="Maximum session duration (5 min)")
    max_tokens: int = Field(default=8000, description="Max context tokens before summarization")

    model_config = {"env_prefix": "CONTEXT_"}


class CacheSettings(BaseSettings):
    """Caching configuration."""
    llm_max_entries: int = Field(default=1000, description="Max LLM cache entries")
    tts_max_entries: int = Field(default=500, description="Max TTS audio cache entries")
    ttl_seconds: int = Field(default=3600, description="Cache TTL (1 hour)")

    model_config = {"env_prefix": "CACHE_"}


class Settings(BaseSettings):
    """Root settings aggregating all component configs."""
    app_name: str = "Athernex Voice Pipeline"
    debug: bool = Field(default=False, description="Enable debug logging")
    log_level: str = Field(default="INFO", description="Log level: DEBUG|INFO|WARNING|ERROR")

    stt: STTSettings = STTSettings()
    llm: LLMSettings = LLMSettings()
    tts: TTSSettings = TTSSettings()
    confidence: ConfidenceSettings = ConfidenceSettings()
    context: ContextSettings = ContextSettings()
    cache: CacheSettings = CacheSettings()

    model_config = {"env_prefix": "APP_", "env_file": ".env", "env_nested_delimiter": "__"}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings (singleton)."""
    return Settings()
